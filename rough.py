# app/services/user_login_service.py

from uuid import uuid4
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserLogin  # <-- your SQLAlchemy model for user_login
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def record_login_for_user(
    session: AsyncSession,
    user_id,
    ip_address: Optional[str] = None,
) -> UserLogin:
    """
    Insert a row into user_login for this user.
    - session_id: new uuid
    - user_id: given
    - login_time: now (UTC)
    - logout_time: NULL
    - ip_address: from frontend (if provided)
    """
    now = datetime.utcnow()

    login = UserLogin(
        session_id=uuid4(),
        user_id=user_id,
        login_time=now,
        logout_time=None,
        ip_address=ip_address,
    )

    logger.info(
        "Recording login for user_id=%s at %s from ip=%s",
        user_id,
        now,
        ip_address,
    )

    session.add(login)
    # DO NOT commit here – commit is handled by the caller's transaction
    await session.flush()

    logger.info("Login row created with session_id=%s", login.session_id)

    return login



------



@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    try:
        async with session.begin():
            # 1) Upsert the user
            user = await create_or_update_user(session, payload)

            # 2) Record login (same DB transaction)
            await record_login_for_user(
                session=session,
                user_id=user.user_id,
                ip_address=getattr(payload, "ip_address", None),
            )

            # 3) Return user; transaction is committed when we exit session.begin()
            return user

    except Exception as e:
        logger.exception("Failed to create/update user: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to create or update user",
)
