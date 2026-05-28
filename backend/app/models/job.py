import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.session import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    title = Column(String, nullable=False)
    raw_text = Column(String, nullable=False)
    parsed_requirements = Column(JSONB, nullable=True)   # structured output from JD Understanding Engine
    embedding_id = Column(String, nullable=True)         # Qdrant point ID for JD embedding
    status = Column(String, default="active")            # active, archived
    created_at = Column(DateTime, server_default=func.now())