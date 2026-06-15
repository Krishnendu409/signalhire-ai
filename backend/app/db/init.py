import logging
from sqlalchemy import inspect, text
from app.db.session import engine, Base

logger = logging.getLogger("signalhire.db")


def _import_models():
    from app.models.user import User  # noqa: F401
    from app.models.job import Job  # noqa: F401
    from app.models.candidate import Candidate  # noqa: F401
    from app.models.ranking import RankingJob  # noqa: F401
    from app.models.feedback import RecruiterFeedback  # noqa: F401


async def ensure_schema():
    """Create tables and apply lightweight schema migrations."""
    _import_models()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        def _needs_job_id_column(sync_conn):
            inspector = inspect(sync_conn)
            if "candidates" not in inspector.get_table_names():
                return False
            return "job_id" not in {col["name"] for col in inspector.get_columns("candidates")}

        needs_job_id = await conn.run_sync(_needs_job_id_column)
        if needs_job_id:
            dialect = engine.dialect.name
            if dialect == "sqlite":
                await conn.execute(text("ALTER TABLE candidates ADD COLUMN job_id CHAR(32)"))
            else:
                await conn.execute(
                    text("ALTER TABLE candidates ADD COLUMN job_id UUID REFERENCES jobs(id)")
                )
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_candidates_job_id ON candidates (job_id)"))
            logger.info("Added job_id column to candidates table")
