import logging
from sqlalchemy import select
from app.db.session import async_session
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.ranking import RankingJob
from app.services.parsing import parse_resume_bytes
from app.services.storage import download_resume
from app.services.ranking import rank_candidates_for_job


logger = logging.getLogger("signalhire.tasks")

import uuid

async def process_resume(candidate_id: str):
    """Background task to parse a resume and index it."""
    async with async_session() as session:
        result = await session.execute(select(Candidate).where(Candidate.id == uuid.UUID(candidate_id)))
        candidate = result.scalar_one_or_none()
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found")
            return {"error": "Candidate not found"}
        
        try:
            file_bytes = await download_resume(candidate.resume_file_key)
            parsed = await parse_resume_bytes(file_bytes, candidate.resume_file_key)
            
            candidate.parsed_data = parsed
            candidate.layout_complexity = parsed.get("_meta", {}).get("layout_complexity", 0)
            candidate.extraction_confidence = parsed.get("_meta", {}).get("extraction_confidence", 0)
            

            await session.commit()
            logger.info(f"Successfully processed resume for candidate {candidate_id}")
            return {"candidate_id": candidate_id, "parsed": True}
        except Exception as e:
            logger.error(f"Error processing resume for candidate {candidate_id}: {str(e)}")
            candidate.parsed_data = {"error": str(e)}
            await session.commit()
            return {"candidate_id": candidate_id, "error": str(e)}

async def process_ranking(ranking_job_id: str):
    """Background task to run the full ranking pipeline."""
    async with async_session() as session:
        res = await session.execute(select(RankingJob).where(RankingJob.id == uuid.UUID(ranking_job_id)))
        ranking_job = res.scalar_one_or_none()
        if not ranking_job:
            return {"error": "Ranking job not found"}
        
        try:
            ranking_job.status = "processing"
            await session.commit()
            
            job_res = await session.execute(select(Job).where(Job.id == ranking_job.job_id))
            job = job_res.scalar_one_or_none()
            if not job:
                ranking_job.status = "failed"
                ranking_job.results = {"error": "Associated job not found"}
                await session.commit()
                return {"error": "Associated job not found"}

            cand_res = await session.execute(
                select(Candidate).where(
                    Candidate.recruiter_id == job.recruiter_id,
                    Candidate.parsed_data.isnot(None)
                )
            )
            candidates = cand_res.scalars().all()
            candidate_list = [
                {"id": str(c.id), "parsed_data": c.parsed_data}
                for c in candidates if c.parsed_data and "error" not in c.parsed_data
            ]
            
            results = await rank_candidates_for_job(
                job_id=str(job.id),
                job_requirements=job.parsed_requirements,
                candidates=candidate_list
            )
            
            ranking_job.results = results
            ranking_job.status = "completed"
            await session.commit()
            logger.info(f"Successfully completed ranking job {ranking_job_id}")
            return results
        except Exception as e:
            logger.error(f"Error in ranking job {ranking_job_id}: {str(e)}")
            ranking_job.status = "failed"
            ranking_job.results = {"error": str(e)}
            await session.commit()
            return {"error": str(e)}