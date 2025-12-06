from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    user_name: constr(strip_whitespace=True, min_length=1)
    email: EmailStr
    department: Optional[str] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    user_id: UUID
    user_name: str
    email: EmailStr
    department: Optional[str]
    role: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


________


from uuid import uuid4
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User  # your SQLAlchemy model
from app.models.pydantic_models import UserCreate
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def get_user_by_email(
    session: AsyncSession, email: str
) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalars().first()


async def create_or_update_user(
    session: AsyncSession, payload: UserCreate
) -> User:
    """
    Simple upsert-by-email:
    - if user with this email exists -> update name/department/role
    - else -> create new user
    """
    existing = await get_user_by_email(session, payload.email)

    now = datetime.utcnow()

    if existing:
        logger.info("Updating existing user with email=%s", payload.email)
        existing.user_name = payload.user_name
        existing.department = payload.department
        existing.role = payload.role
        existing.updated_at = now
        await session.flush()
        return existing

    logger.info("Creating new user with email=%s", payload.email)

    user = User(
        user_id=uuid4(),
        user_name=payload.user_name,
        email=payload.email,
        department=payload.department,
        role=payload.role,
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    await session.flush()
    return user


-------


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session_new import get_db_session
from app.models.pydantic_models import UserCreate, UserResponse
from app.services.user_service import create_or_update_user, get_user_by_email
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    try:
        async with session.begin():
            user = await create_or_update_user(session, payload)
        return user
    except Exception as e:
        logger.exception("Failed to create/update user: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to create or update user",
        )


@router.get("/users/by-email/{email}", response_model=UserResponse)
async def get_user(
    email: str,
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    user = await get_user_by_email(session, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user



-------


from app.api import users

app.include_router(users.router, prefix="/api")
