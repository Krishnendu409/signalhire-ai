import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.session import Base


class AuditLog(Base):
    """Immutable record of every system action for compliance and debugging."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    action_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now())