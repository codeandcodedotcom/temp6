# app/services/user_login_service.py
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4, UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import UserLogin  # your existing SQLAlchemy model
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def close_open_sessions_for_user(
    session: AsyncSession,
    user_id: UUID,
    logout_time: Optional[datetime] = None,
) -> int:
    """
    Set logout_time on any sessions for this user that are still open.

    Returns number of sessions updated.
    """
    if logout_time is None:
        logout_time = datetime.utcnow()

    stmt = select(UserLogin).where(
        UserLogin.user_id == user_id,
        UserLogin.logout_time.is_(None),
    )

    result = await session.execute(stmt)
    open_sessions = result.scalars().all()

    for s in open_sessions:
        s.logout_time = logout_time

    count = len(open_sessions)
    if count:
        logger.info("Closed %d open login session(s) for user %s", count, user_id)

    return count


async def record_login_for_user(
    session: AsyncSession,
    user_id: UUID,
    ip_address: Optional[str] = None,
    login_time: Optional[datetime] = None,
) -> UserLogin:
    """
    Record a new login:

    - Close any previous open sessions for this user.
    - Insert a new user_login row with login_time and ip_address.
    """
    if login_time is None:
        login_time = datetime.utcnow()

    # 1) Close old open sessions
    await close_open_sessions_for_user(session, user_id, logout_time=login_time)

    # 2) Create new login row
    login = UserLogin(
        session_id=uuid4(),
        user_id=user_id,
        login_time=login_time,
        logout_time=None,
        ip_address=ip_address,
    )

    session.add(login)

    logger.info(
        "Recorded new login for user %s from IP %s at %s",
        user_id,
        ip_address,
        login_time.isoformat(timespec="seconds"),
    )

    # No commit here – caller will commit
    return login



------



@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    try:
        async with session.begin():
            # 1) Upsert user in `users` table
            user = await create_or_update_user(session, payload)

            # 2) Record login in `user_login` table
            #    If your UserCreate has ip_address, it will be used; otherwise None.
            await record_login_for_user(
                session=session,
                user_id=user.user_id,
                ip_address=getattr(payload, "ip_address", None),
            )

            # 3) Return user response (transaction is committed by session.begin)
            return user

    except Exception as e:
        logger.exception("Failed to create/update user: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to create or update user",
)
