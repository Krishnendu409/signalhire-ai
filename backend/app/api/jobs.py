from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from sqlalchemy import select
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.job import Job
from app.services.ai import AIPipeline
from app.services.embeddings import embed_document
from app.services.vector_store import index_job
import uuid

router = APIRouter()


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

    # 3. Generate embedding and store in Qdrant
    query_text = f"{parsed.get('title', '')}. {raw_text[:1000]}"
    embedding = await embed_document(query_text)
    await index_job(
        job_id=str(job.id),
        embedding=embedding,
        payload={
            "job_id": str(job.id),
            "title": job.title,
            "seniority": parsed.get("seniority", ""),
        },
    )
    job.embedding_id = str(job.id)
    await db.commit()

    return {"id": str(job.id), "title": job.title, "status": job.status}


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


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get a single job with its parsed requirements."""
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.recruiter_id == user.id)
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
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.recruiter_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "archived"
    await db.commit()
    return {"status": "archived"}