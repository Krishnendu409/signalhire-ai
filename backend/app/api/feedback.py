from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.ranking import RankingJob
from app.services.audit import AuditAgent
from sqlalchemy import select

router = APIRouter()

class FeedbackRequest(BaseModel):
    ranking_id: str
    candidate_id: str
    original_rank: int
    new_rank: int
    reason: str

@router.post("/")
async def submit_feedback(
    request: FeedbackRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Capture recruiter override/feedback.
    This logs the decision for audit and future fine-tuning.
    """
    # Log the override
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
    
    # In a full implementation, we would store this in a 'feedback' table
    # and use it for local regression training as mentioned in research.
    
    return {"status": "recorded", "message": "Feedback captured for model refinement."}