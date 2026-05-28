from fastapi import Depends, HTTPException, Header
from sqlalchemy import select
from app.db.session import async_session
from app.models.user import User
import uuid

async def get_current_user(authorization: str = Header(default="")):
    """Always returns a demo user. No auth required."""
    async with async_session() as session:
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email="demo@signalhire.ai",
                full_name="Demo Recruiter",
                role="recruiter"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user