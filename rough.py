# app/services/kpi_service.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.charter import Charter as DBCharter
from app.schemas.user import User as DBUser


async def get_total_charters(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(DBCharter)
    res = await session.execute(stmt)
    return int(res.scalar_one())


async def get_total_users(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(DBUser)
    res = await session.execute(stmt)
    return int(res.scalar_one())


# app/api/kpi.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session_new import get_db_session
from app.services.kpi_service import get_total_charters, get_total_users

router = APIRouter(prefix="/api/kpi", tags=["kpi"])


@router.get("/total-charters")
async def total_charters(session: AsyncSession = Depends(get_db_session)):
    total = await get_total_charters(session)
    return {"total_charters": total}


@router.get("/total-users")
async def total_users(session: AsyncSession = Depends(get_db_session)):
    total = await get_total_users(session)
    return {"total_users": total}
