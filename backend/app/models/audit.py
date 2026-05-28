import uuid
from sqlalchemy import Column, String, Integer, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.session import Base


class AuditLog(Base):
    """Immutable record of every system action for compliance and debugging."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    action_metadata = Column(JSONB, nullable=True)  # renamed from 'metadata'
    created_at = Column(DateTime, server_default=func.now())


class RecruiterFeedback(Base):
    """Structured feedback from recruiters to fine‑tune future rankings."""
    __tablename__ = "recruiter_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ranking_job_id = Column(UUID(as_uuid=True), ForeignKey("ranking_jobs.id"), index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"))
    rating = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())