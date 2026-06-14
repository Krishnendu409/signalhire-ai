import uuid
from sqlalchemy import Column, String, Integer, DateTime, func, ForeignKey
from sqlalchemy.types import Uuid as UUID, JSON as JSONB
from app.db.session import Base

class RankingJob(Base):
    __tablename__ = "ranking_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), index=True)
    version = Column(Integer, default=1)                    # incremented on re-ranking
    status = Column(String, default="pending")              # pending, processing, completed, failed
    total_candidates = Column(Integer, default=0)
    results = Column(JSONB, nullable=True)                  # full ranked list with scores, dimensions, explanations
    created_at = Column(DateTime, server_default=func.now())