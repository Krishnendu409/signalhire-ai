from app.services.comparison import ComparisonService
from pydantic import BaseModel
from typing import List, Optional
from fastapi import APIRouter, UploadFile, Depends, HTTPException, File, Form
from sqlalchemy import select
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.storage import upload_resume
from app.tasks.manager import task_queue
import uuid

router = APIRouter()


@router.post("/upload")
async def upload_candidate_resume(
    file: UploadFile = File(...),
    job_id: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Upload a resume PDF/image. The system will:
    1. Save the file.
    2. Create a candidate record.
    3. Enqueue async parsing + embedding via SAQ.
    """
    if not file.filename or not file.filename.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a PDF or image.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    job_uuid = None
    if job_id:
        job_result = await db.execute(
            select(Job).where(Job.id == uuid.UUID(job_id), Job.recruiter_id == user.id)
        )
        if not job_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Job not found")
        job_uuid = uuid.UUID(job_id)

    candidate = Candidate(
        id=uuid.uuid4(),
        recruiter_id=user.id,
        job_id=job_uuid,
        resume_file_key="",
    )
    db.add(candidate)
    await db.commit()

    file_key = await upload_resume(file_bytes, str(candidate.id), file.filename or "")
    candidate.resume_file_key = file_key
    await db.commit()

    # SAQ: only pass function name as string
    task_id = await task_queue.add_task("process_resume", candidate_id=str(candidate.id))

    return {
        "candidate_id": str(candidate.id),
        "task_id": task_id,
        "status": "processing",
        "message": "Resume uploaded and queued for parsing.",
    }


@router.get("/file/{candidate_id}")
async def get_candidate_file(
    candidate_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Serve the raw resume file for display or download."""
    from fastapi.responses import Response
    from app.services.storage import download_resume

    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.recruiter_id == uuid.UUID(str(user.id)))
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    file_bytes = await download_resume(candidate.resume_file_key)
    # Determine the media type
    media_type = "application/pdf" if candidate.resume_file_key.lower().endswith(".pdf") else "image/jpeg"
    
    return Response(content=file_bytes, media_type=media_type)


@router.get("/")
async def list_candidates(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """List all candidates for the current recruiter."""
    result = await db.execute(
        select(Candidate)
        .where(Candidate.recruiter_id == uuid.UUID(str(user.id)))
        .order_by(Candidate.created_at.desc())
    )
    candidates = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "name": c.parsed_data.get("full_name", "Processing...") if c.parsed_data else "Processing...",
            "current_title": c.parsed_data.get("current_title", "") if c.parsed_data else "",
            "status": "ready" if c.parsed_data and "error" not in c.parsed_data else "processing",
            "layout_complexity": c.layout_complexity,
            "extraction_confidence": c.extraction_confidence,
            "created_at": c.created_at.isoformat(),
        }
        for c in candidates
    ]


class CompareRequest(BaseModel):
    candidate_ids: List[str]

@router.post("/compare")
async def compare_candidates(
    req: CompareRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    result = await db.execute(
        select(Candidate).where(
            Candidate.id.in_([uuid.UUID(str(cid)) for cid in req.candidate_ids]),
            Candidate.recruiter_id == uuid.UUID(str(user.id))
        )
    )
    candidates = result.scalars().all()
    if not candidates:
        raise HTTPException(status_code=404, detail="Candidates not found")
        
    c_data = []
    for c in candidates:
        c_data.append({
            "id": str(c.id),
            "parsed_data": c.parsed_data
        })
        
    return ComparisonService.compare_candidates(c_data)

@router.get("/search")
async def search_candidates(
    q: Optional[str] = None,
    skills: Optional[str] = None,
    title: Optional[str] = None,
    experience_min: Optional[int] = None,
    experience_max: Optional[int] = None,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    result = await db.execute(
        select(Candidate).where(Candidate.recruiter_id == uuid.UUID(str(user.id)))
    )
    candidates = result.scalars().all()
    
    filtered = []
    for c in candidates:
        parsed = c.parsed_data or {}
        
        if title and title.lower() not in parsed.get("current_title", "").lower():
            continue
            
        yoe = parsed.get("total_years_of_experience", parsed.get("experience_years", 0))
        if experience_min is not None and yoe < experience_min:
            continue
        if experience_max is not None and yoe > experience_max:
            continue
            
        if skills:
            req_skills = [s.strip().lower() for s in skills.split(",")]
            cand_skills = [s.get("name", "").lower() for s in parsed.get("skills", []) if s.get("name")]
            if not all(any(rs in cs for cs in cand_skills) for rs in req_skills):
                continue
                
        if q:
            q_lower = q.lower()
            text_blob = str(parsed).lower()
            if q_lower not in text_blob:
                continue
                
        filtered.append({
            "id": str(c.id),
            "parsed_data": parsed
        })
        
    return filtered

@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get full candidate details including parsed resume data."""
    result = await db.execute(
        select(Candidate).where(
            Candidate.id == candidate_id,
            Candidate.recruiter_id == uuid.UUID(str(user.id)),
        )
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return {
        "id": str(candidate.id),
        "parsed_data": candidate.parsed_data,
        "layout_complexity": candidate.layout_complexity,
        "extraction_confidence": candidate.extraction_confidence,
        "created_at": candidate.created_at.isoformat(),
    }


@router.delete("/{candidate_id}")
async def delete_candidate(
    candidate_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete a candidate and their data."""
    result = await db.execute(
        select(Candidate).where(
            Candidate.id == candidate_id,
            Candidate.recruiter_id == uuid.UUID(str(user.id)),
        )
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    await db.delete(candidate)
    await db.commit()
    return {"status": "deleted"}

