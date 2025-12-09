# app/services/kpi_service.py

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract

from app.db.models.projects import Project
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ------------------------------
# HELPER: Map month → quarter
# ------------------------------
def _get_quarter(month: int) -> str:
    if month in (1, 2, 3):
        return "Quarter 1"
    if month in (4, 5, 6):
        return "Quarter 2"
    if month in (7, 8, 9):
        return "Quarter 3"
    return "Quarter 4"


# ---------------------------------------
# MAIN KPI SERVICE
# ---------------------------------------
async def get_department_charters(session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Returns KPI:
    Charter counts per department per quarter, broken down by PM band.
    Shape must match DepartmentCharter Pydantic model.
    """

    stmt = select(
        Project.department,
        Project.managed_by,
        extract("month", Project.created_at).label("month")
    ).where(Project.department.isnot(None))

    result = await session.execute(stmt)
    rows = result.all()

    data: Dict[str, Dict[str, Dict[str, int]]] = {}

    # Initialize structure while looping rows
    for dept, managed_by, month in rows:
        if dept not in data:
            data[dept] = {
                "Quarter 1": {"self_managed": 0, "team_lead": 0, "project_manager": 0, "team_of_PM_professionals": 0},
                "Quarter 2": {"self_managed": 0, "team_lead": 0, "project_manager": 0, "team_of_PM_professionals": 0},
                "Quarter 3": {"self_managed": 0, "team_lead": 0, "project_manager": 0, "team_of_PM_professionals": 0},
                "Quarter 4": {"self_managed": 0, "team_lead": 0, "project_manager": 0, "team_of_PM_professionals": 0},
            }

        quarter = _get_quarter(int(month))

        # Map managed_by to correct field
        if managed_by == "Self managed":
            data[dept][quarter]["self_managed"] += 1
        elif managed_by == "Project Lead":
            data[dept][quarter]["team_lead"] += 1
        elif managed_by == "Project Manager":
            data[dept][quarter]["project_manager"] += 1
        elif managed_by == "Team of PM professionals":
            data[dept][quarter]["team_of_PM_professionals"] += 1

    # Convert into list for API output
    final_output = [
        {
            "department": dept,
            "quarters": quarters
        }
        for dept, quarters in data.items()
    ]

    logger.info("KPI: generated department charter summary (%d departments)", len(final_output))

    return final_output

------

@router.get("/kpi/department-charters", response_model=List[DepartmentCharter])
async def department_charters(session: AsyncSession = Depends(get_db_session)) -> List[DepartmentCharter]:
    try:
        raw = await kpi_service.get_department_charters(session)
        return raw
    except Exception:
        logger.exception("Failed to fetch department charters")
        raise HTTPException(status_code=500, detail="Failed to fetch department charters")
