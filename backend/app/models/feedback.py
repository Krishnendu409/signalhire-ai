import uuid
from sqlalchemy import Column, String, Integer, DateTime, func, ForeignKey
from sqlalchemy.types import Uuid as UUID, JSON as JSONB
from app.db.session import Base

class RecruiterFeedback(Base):
    __tablename__ = "recruiter_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    ranking_id = Column(UUID(as_uuid=True), ForeignKey("ranking_jobs.id"), index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), index=True)
    original_rank = Column(Integer)
    new_rank = Column(Integer)
    reason = Column(String)
    created_at = Column(DateTime, server_default=func.now())
