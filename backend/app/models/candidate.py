import uuid
from sqlalchemy import Column, String, DateTime, Float, func, ForeignKey
from sqlalchemy.types import Uuid as UUID, JSON as JSONB
from app.db.session import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    resume_file_key = Column(String, nullable=False)        # R2 object key
    parsed_data = Column(JSONB, nullable=True)              # structured resume from AI parser
    embedding_ids = Column(JSONB, nullable=True)            # list of Qdrant point IDs (chunks)
    layout_complexity = Column(Float, default=0.0)          # 0.0 = simple, 1.0 = highly complex layout
    extraction_confidence = Column(Float, default=1.0)      # 0.0-1.0 parser confidence score
    created_at = Column(DateTime, server_default=func.now())