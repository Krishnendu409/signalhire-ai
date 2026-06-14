import uuid
from sqlalchemy import select
from app.db.session import async_session
from app.models.user import User

async def get_current_user():
    """Provides a permanent system user, completely removing authentication."""
    async with async_session() as session:
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=uuid.uuid4(), email="system@signalhire.ai", full_name="System Administrator")
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user