from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.ranking import RankingJob
from app.models.job import Job
from app.services.audit import AuditAgent
from sqlalchemy import select

router = APIRouter()

class FeedbackRequest(BaseModel):
    ranking_id: str
    candidate_id: str
    original_rank: int
    new_rank: int
    reason: str

from app.models.feedback import RecruiterFeedback

@router.post("/")
async def submit_feedback(
    request: FeedbackRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Capture recruiter override/feedback.
    Saves to DB for future fine-tuning and logs to audit trail.
    """
    # Verify ranking belongs to a job owned by this recruiter
    rank_check = await db.execute(
        select(RankingJob)
        .join(Job, RankingJob.job_id == Job.id)
        .where(RankingJob.id == request.ranking_id, Job.recruiter_id == user.id)
    )
    if not rank_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Ranking not found or unauthorized")

    # 1. Log to audit trail
    await AuditAgent.log_decision(
        "RecruiterAgent",
        "manual_override",
        request.candidate_id,
        "N/A",
        {
            "ranking_id": request.ranking_id,
            "original_rank": request.original_rank,
            "new_rank": request.new_rank,
            "reason": request.reason
        },
        user_id=str(user.id)
    )
    
    # 2. Store in DB
    feedback = RecruiterFeedback(
        user_id=user.id,
        ranking_id=request.ranking_id,
        candidate_id=request.candidate_id,
        original_rank=request.original_rank,
        new_rank=request.new_rank,
        reason=request.reason
    )
    db.add(feedback)
    await db.commit()
    
    return {"status": "recorded", "message": "Feedback captured for model refinement."}