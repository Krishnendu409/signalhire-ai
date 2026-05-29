import jwt
from fastapi import Depends, HTTPException, Header
from sqlalchemy import select
from app.db.session import async_session
from app.models.user import User
from app.core.config import settings
import uuid

async def get_current_user(authorization: str = Header(default="")):
    """Validates the JWT token or provides a demo user for development."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    # DEV BYPASS: Allow a placeholder token or a raw UUID for demo purposes
    token = authorization.split(" ")[1] if " " in authorization else authorization
    
    if token == "demo-token-placeholder":
        async with async_session() as session:
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            if not user:
                user = User(id=uuid.uuid4(), email="demo@signalhire.ai", full_name="Demo User")
                session.add(user)
                await session.commit()
                await session.refresh(user)
            return user

    try:
        payload = jwt.decode(token, settings.auth_secret, algorithms=["HS256"])
        user_id = payload.get("sub") or payload.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except (jwt.InvalidTokenError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid authorization token")