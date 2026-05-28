from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.ranking import RankingJob
from app.tasks.manager import task_queue
from app.tasks.functions import process_ranking
import uuid

router = APIRouter()


@router.post("/{job_id}")
async def create_ranking(
    job_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Trigger ranking for a job. Enqueues async task that:
    1. Retrieves all parsed candidates.
    2. Runs dense retrieval + cross-encoder reranking + AI scoring.
    3. Generates explanations for top 5.
    4. Stores the complete ranked list.
    """
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.recruiter_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.parsed_requirements:
        raise HTTPException(status_code=400, detail="Job has not been parsed yet")

    candidate_result = await db.execute(
        select(Candidate).where(
            Candidate.recruiter_id == user.id,
            Candidate.parsed_data.isnot(None),
        )
    )
    candidates = candidate_result.scalars().all()
    if not candidates:
        raise HTTPException(status_code=400, detail="No parsed candidates found. Upload and wait for parsing to complete.")

    ranking = RankingJob(
        id=uuid.uuid4(),
        job_id=job.id,
        version=1,
        status="pending",
        total_candidates=len(candidates),
    )
    db.add(ranking)
    await db.commit()

    await task_queue.add_task("process_ranking", process_ranking, str(ranking.id))

    return {
        "ranking_id": str(ranking.id),
        "status": "pending",
        "message": f"Ranking started for {len(candidates)} candidates.",
    }


@router.get("/{job_id}/latest")
async def get_latest_ranking(
    job_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get the latest completed ranking for a job."""
    job_result = await db.execute(
        select(Job).where(Job.id == job_id, Job.recruiter_id == user.id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    ranking_result = await db.execute(
        select(RankingJob)
        .where(RankingJob.job_id == job.id)
        .order_by(RankingJob.created_at.desc())
        .limit(1)
    )
    ranking = ranking_result.scalar_one_or_none()

    if not ranking:
        return {"status": "not_started", "message": "No ranking has been run for this job yet."}

    if ranking.status in ("pending", "processing"):
        return {
            "ranking_id": str(ranking.id),
            "status": ranking.status,
            "message": "Ranking is still in progress. Poll again in a few seconds.",
        }

    if ranking.status == "failed":
        return {
            "ranking_id": str(ranking.id),
            "status": "failed",
            "error": ranking.results.get("error", "Unknown error"),
        }

    return {
        "ranking_id": str(ranking.id),
        "job_id": str(ranking.job_id),
        "status": ranking.status,
        "total_candidates": ranking.total_candidates,
        "results": ranking.results.get("results", []),
        "created_at": ranking.created_at.isoformat(),
    }


@router.get("/{job_id}/export")
async def export_ranking_csv(
    job_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Export the latest ranking as CSV for spreadsheet integration."""
    import csv
    import io
    from fastapi.responses import StreamingResponse

    ranking_result = await db.execute(
        select(RankingJob)
        .where(RankingJob.job_id == job_id)
        .order_by(RankingJob.created_at.desc())
        .limit(1)
    )
    ranking = ranking_result.scalar_one_or_none()

    if not ranking or ranking.status != "completed":
        raise HTTPException(status_code=404, detail="No completed ranking found")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank", "Candidate Name", "Current Title", "Final Score",
        "Semantic Relevance", "Experience Depth", "Career Trajectory",
        "Project Relevance", "Behavioral", "Domain Alignment", "Adaptability",
        "Top Strengths", "Missing Skills", "Adjacent Skills", "Risk Factors",
    ])

    for i, res in enumerate(ranking.results.get("results", [])):
        parsed = res.get("parsed_data", {})
        dims = res.get("dimension_scores", {})
        expl = res.get("explanation", {})

        writer.writerow([
            i + 1,
            parsed.get("full_name", "Unknown"),
            parsed.get("current_title", ""),
            res.get("final_score", 0),
            dims.get("semantic_relevance", {}).get("score", ""),
            dims.get("experience_depth", {}).get("score", ""),
            dims.get("career_trajectory", {}).get("score", ""),
            dims.get("project_relevance", {}).get("score", ""),
            dims.get("behavioral_indicators", {}).get("score", ""),
            dims.get("domain_alignment", {}).get("score", ""),
            dims.get("adaptability", {}).get("score", ""),
            "; ".join(expl.get("top_strengths", [])),
            "; ".join(expl.get("missing_skills", [])),
            "; ".join(expl.get("adjacent_skills", [])),
            "; ".join(expl.get("risk_factors", [])),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ranking_{job_id}.csv"},
    )