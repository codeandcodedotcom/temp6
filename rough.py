# app/services/kpi_view.py  (or similar)

from typing import List, Dict, Any
from datetime import datetime
import calendar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.db.models import Project  # adjust import path to your ORM model


async def get_charters_per_month(session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Return list of rows:
      {
        "month": "January",
        "self_managed": 15,
        "team_lead": 7,
        "project_manager": 5,
        "team_of_PM_professionals": 28,
      }
    computed from the projects table.
    """

    month_expr = func.date_trunc("month", Project.created_at).label("month")

    stmt = (
        select(
            month_expr,
            func.sum(
                case((Project.managed_by == "Self managed", 1), else_=0)
            ).label("self_managed"),
            func.sum(
                case((Project.managed_by == "Project Lead", 1), else_=0)
            ).label("team_lead"),
            func.sum(
                case((Project.managed_by == "Project Manager", 1), else_=0)
            ).label("project_manager"),
            func.sum(
                case((Project.managed_by == "Team of PM professionals", 1), else_=0)
            ).label("team_of_PM_professionals"),
        )
        .group_by(month_expr)
        .order_by(month_expr)
    )

    result = await session.execute(stmt)
    rows = result.all()

    data: List[Dict[str, Any]] = []
    for row in rows:
        month_dt: datetime = row.month
        month_name = calendar.month_name[month_dt.month]

        data.append(
            {
                "month": month_name,
                "self_managed": row.self_managed or 0,
                "team_lead": row.team_lead or 0,
                "project_manager": row.project_manager or 0,
                "team_of_PM_professionals": row.team_of_PM_professionals or 0,
            }
        )

    return data



--------



from typing import List
from fastapi import Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.logger import get_logger
from app.db.session import get_session  # whatever your dependency is
from app.services import kpi_view
from app.models.pydantic_models import MonthlyCharter

logger = get_logger(__name__)


@router.get("/kpi/charters-per-month", response_model=List[MonthlyCharter])
async def charters_per_month(
    session: AsyncSession = Depends(get_session),
) -> List[MonthlyCharter]:
    """
    Returns total charter counts per month, broken down by PM band.
    """
    try:
        data = await kpi_view.get_charters_per_month(session=session)
        return data
    except Exception:
        logger.exception("Failed to fetch charters per month")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch charters per month",
    )
