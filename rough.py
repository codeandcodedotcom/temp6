from collections import defaultdict
from datetime import datetime  # already imported at top, just for context
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.project import Project
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _fy_quarter(dt: datetime) -> str:
    """
    Map a datetime to a financial-year quarter.
    Financial year starts in April:
      Q1: Apr–Jun
      Q2: Jul–Sep
      Q3: Oct–Dec
      Q4: Jan–Mar
    """
    m = dt.month
    if 4 <= m <= 6:
        return "Q1"
    elif 7 <= m <= 9:
        return "Q2"
    elif 10 <= m <= 12:
        return "Q3"
    else:
        return "Q4"


async def get_returning_users(session: AsyncSession) -> List[Dict[str, Any]]:
    """
    KPI: Returning vs New users (per financial-year quarter).

    Rules (per quarter):
    - If a user creates exactly 1 charter in that quarter => "new_user"
    - If a user creates more than 1 charter in that quarter => "returning_user"

    One project == one charter (uses the `projects` table).
    """

    # 1) Pull all project creations with a valid user & created_at
    stmt = select(Project.user_id, Project.created_at).where(
        Project.user_id.isnot(None),
        Project.created_at.isnot(None),
    )

    result = await session.execute(stmt)
    rows = result.all()

    if not rows:
        # Return zeroes for all quarters so the chart still renders
        return [
            {"Quarter": q, "new_user": 0, "returning_user": 0}
            for q in ("Q1", "Q2", "Q3", "Q4")
        ]

    # 2) Count number of projects per (user, quarter)
    counts: Dict[tuple[Any, str], int] = defaultdict(int)

    for user_id, created_at in rows:
        # created_at can be aware or naive; we only care about month
        q = _fy_quarter(created_at)
        counts[(user_id, q)] += 1

    # 3) For each quarter, track which users are "new" vs "returning"
    quarter_stats: Dict[str, Dict[str, set]] = {
        "Q1": {"new_user": set(), "returning_user": set()},
        "Q2": {"new_user": set(), "returning_user": set()},
        "Q3": {"new_user": set(), "returning_user": set()},
        "Q4": {"new_user": set(), "returning_user": set()},
    }

    for (user_id, q), n_projects in counts.items():
        if n_projects == 1:
            quarter_stats[q]["new_user"].add(user_id)
        elif n_projects > 1:
            quarter_stats[q]["returning_user"].add(user_id)

    # 4) Convert to the JSON structure expected by the frontend
    data: List[Dict[str, Any]] = [
        {
            "Quarter": q,
            "new_user": len(quarter_stats[q]["new_user"]),
            "returning_user": len(quarter_stats[q]["returning_user"]),
        }
        for q in ("Q1", "Q2", "Q3", "Q4")
    ]

    logger.info("Computed returning vs new users KPI: %s", data)
    return data



-----

@router.get("/kpi/returning-users", response_model=List[ReturningUserEntry])
async def returning_users(
    session: AsyncSession = Depends(get_db_session),
) -> List[ReturningUserEntry]:
    try:
        data = await kpi_service.get_returning_users(session)
        return data
    except Exception:
        logger.exception("Failed to fetch new vs returning users data.")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch new vs returning users data.",
    )

