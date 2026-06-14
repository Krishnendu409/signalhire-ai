import asyncio
from app.db.session import engine, Base
from app.models import user, job, candidate, ranking, feedback

async def test():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database connection successful")
    except Exception as e:
        print(f"Database error: {e}")

asyncio.run(test())
