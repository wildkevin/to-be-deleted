from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models.user import User


async def get_current_user(
    x_ccm_user: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not x_ccm_user:
        raise HTTPException(status_code=401, detail="X-CCM-User header required")
    result = await db.execute(select(User).where(User.username == x_ccm_user))
    user = result.scalar_one_or_none()
    if not user:
        # Spec: unknown users must 401 (no auto-create).
        raise HTTPException(status_code=401, detail="Unknown user")
    return user


async def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
