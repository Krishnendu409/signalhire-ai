from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from sqlalchemy import select
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.job import Job
from app.models.candidate import Candidate
from app.services.ai import AIPipeline
import uuid

router = APIRouter()


@router.get("/default")
async def get_default_investigation(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Return the seeded default showcase investigation (70%+ matches in shortlist)."""
    from app.services.default_investigation import (
        DEFAULT_INVESTIGATION_TITLE,
        ensure_default_investigation,
        get_default_investigation_job_id,
    )

    job_id = await get_default_investigation_job_id(db, user)
    if not job_id:
        job_id = await ensure_default_investigation()
    if not job_id:
        raise HTTPException(status_code=404, detail="Default investigation is not available")

    result = await db.execute(
        select(Job).where(Job.id == uuid.UUID(job_id), Job.recruiter_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Default investigation not found")

    return {
        "id": str(job.id),
        "title": job.title,
        "status": job.status,
        "is_default": True,
        "default_title": DEFAULT_INVESTIGATION_TITLE,
        "created_at": job.created_at.isoformat(),
    }


@router.post("/default-showcase")
async def create_default_showcase(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Manually recreate the default showcase investigation."""
    from app.services.default_investigation import (
        DEFAULT_INVESTIGATION_TITLE,
        create_default_investigation,
    )

    existing = await _find_default_job(db, user)
    if existing:
        existing.status = "archived"
    await db.commit()

    try:
        return await create_default_investigation(user, db)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/hackathon-demo")
async def create_hackathon_demo(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Bootstrap a demo investigation from bundled sample_resumes/ PDFs."""
    from app.services.demo import create_hackathon_demo as bootstrap_demo

    try:
        return await bootstrap_demo(user, db)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("")
async def create_job(
    title: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Upload a job description file (PDF/Text). The system will:
    1. Extract text using the parsing service.
    2. Parse it into structured requirements using AI.
    3. Store in DB and Qdrant.
    """
    try:
        from app.services.parsing import extract_text_from_pdf, extract_text_from_image
        
        file_bytes = await file.read()
        if file.filename.lower().endswith(".pdf"):
            raw_text, _ = await extract_text_from_pdf(file_bytes)
        elif file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
            raw_text, _ = await extract_text_from_image(file_bytes)
        else:
            raw_text = file_bytes.decode("utf-8", errors="ignore")

        if not raw_text:
            raise HTTPException(status_code=400, detail="Could not extract text from JD file")

        # 1. AI parsing
        parsed = await AIPipeline.parse_jd(raw_text)

        # 2. Create DB record
        job = Job(
            id=uuid.uuid4(),
            recruiter_id=user.id,
            title=title,
            raw_text=raw_text,
            parsed_requirements=parsed,
            status="active",
        )
        db.add(job)
        await db.commit()

        job.embedding_id = str(job.id)
        await db.commit()

        return {"id": str(job.id), "title": job.title, "status": job.status}
    except Exception as e:
        import traceback
        with open("error.log", "w") as f:
            traceback.print_exc(file=f)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_jobs(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """List all jobs for the current recruiter."""
    result = await db.execute(
        select(Job)
        .where(Job.recruiter_id == user.id)
        .order_by(Job.created_at.desc())
    )
    jobs = result.scalars().all()
    return [
        {
            "id": str(j.id),
            "title": j.title,
            "status": j.status,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ]


@router.get("/{job_id}/candidates-status")
async def get_job_candidates_status(
    job_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Return how many job-linked candidates are parsed and ready to rank."""
    job_result = await db.execute(
        select(Job).where(Job.id == uuid.UUID(job_id), Job.recruiter_id == user.id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidate_result = await db.execute(
        select(Candidate).where(
            Candidate.recruiter_id == user.id,
            Candidate.job_id == job.id,
        )
    )
    candidates = candidate_result.scalars().all()

    ready = []
    processing = []
    failed = []
    for candidate in candidates:
        parsed = candidate.parsed_data
        if not parsed:
            processing.append(str(candidate.id))
        elif "error" in parsed:
            failed.append({"candidate_id": str(candidate.id), "error": parsed["error"]})
        else:
            ready.append(str(candidate.id))

    return {
        "job_id": str(job.id),
        "total": len(candidates),
        "ready_count": len(ready),
        "processing_count": len(processing),
        "failed_count": len(failed),
        "ready": len(ready) > 0,
        "failures": failed,
    }


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get a single job with its parsed requirements."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job id")

    result = await db.execute(
        select(Job).where(Job.id == job_uuid, Job.recruiter_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": str(job.id),
        "title": job.title,
        "raw_text": job.raw_text,
        "parsed_requirements": job.parsed_requirements,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
    }


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Archive a job."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job id")

    result = await db.execute(
        select(Job).where(Job.id == job_uuid, Job.recruiter_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "archived"
    await db.commit()
    return {"status": "archived"}