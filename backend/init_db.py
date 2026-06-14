import asyncio
from app.db.session import engine, Base
from app.models.user import User
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.ranking import RankingJob
from app.models.feedback import RecruiterFeedback
from app.models.audit import AuditLog

async def init_db():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(init_db())
