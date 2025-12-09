from collections import defaultdict
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.project import Project
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Re-use your existing _fy_quarter(dt) -> "Q1"/"Q2"/"Q3"/"Q4"
# If it's in the same file already, DON'T duplicate it.


def _quarter_label_from_fy(q: str) -> str:
    """
    Convert 'Q1'..'Q4' to the labels used in KPI JSON ('Quarter 1'..'Quarter 4').
    """
    mapping = {
        "Q1": "Quarter 1",
        "Q2": "Quarter 2",
        "Q3": "Quarter 3",
        "Q4": "Quarter 4",
    }
    return mapping.get(q, q)


def _empty_counts() -> Dict[str, int]:
    """
    Helper: empty bucket for one quarter.
    """
    return {
        "self_managed": 0,
        "team_lead": 0,
        "project_manager": 0,
        "team_of_PM_professionals": 0,
    }


async def get_user_activity(session: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """
    KPI: Top N users by total charters, with quarter-wise PM band breakdown.

    Returns data shaped like the existing dummy `user_activity` JSON:
    [
      {
        "user": "<user-id-or-email>",
        "quarters": {
          "Quarter 1": { "self_managed": ..., "team_lead": ..., ... },
          ...
        }
      },
      ...
    ]
    """

    # 1) Fetch all projects that have a user & created_at & managed_by
    stmt = select(
        Project.user_id,
        Project.managed_by,
        Project.created_at,
    ).where(
        Project.user_id.isnot(None),
        Project.created_at.isnot(None),
        Project.managed_by.isnot(None),
    )

    result = await session.execute(stmt)
    rows = result.all()

    if not rows:
        # No projects yet → return empty list
        logger.info("No projects found for user activity KPI.")
        return []

    # Map text in `managed_by` column → KPI band key
    band_map = {
        # Try to cover likely spellings
        "Self Managed": "self_managed",
        "Self managed": "self_managed",
        "self managed": "self_managed",

        "Project Lead": "team_lead",
        "Project lead": "team_lead",
        "Project Lead Managed": "team_lead",

        "Project Manager": "project_manager",
        "Project manager": "project_manager",
        "Project Manager Managed": "project_manager",

        "Team of PM Professionals": "team_of_PM_professionals",
        "Team of PM Profesionals": "team_of_PM_professionals",
        "Team of PM professionals": "team_of_PM_professionals",
    }

    # 2) Aggregate per (user, quarter_label)
    # user_buckets[user_id][quarter_label] = { band -> count }
    user_buckets: Dict[Any, Dict[str, Dict[str, int]]] = defaultdict(
        lambda: defaultdict(_empty_counts)
    )

    for user_id, managed_by, created_at in rows:
        band_key = band_map.get(str(managed_by).strip())
        if not band_key:
            # Unknown / unexpected managed_by label → skip this project
            continue

        q = _fy_quarter(created_at)               # "Q1".."Q4"
        quarter_label = _quarter_label_from_fy(q)  # "Quarter 1".."Quarter 4"

        user_buckets[user_id][quarter_label][band_key] += 1

    # 3) Compute total charters per user (across all quarters) → for ranking
    user_totals: Dict[Any, int] = {}
    for user_id, qdict in user_buckets.items():
        total = 0
        for counts in qdict.values():
            total += (
                counts["self_managed"]
                + counts["team_lead"]
                + counts["project_manager"]
                + counts["team_of_PM_professionals"]
            )
        user_totals[user_id] = total

    # 4) Pick top N users by total charters (descending)
    top_users = sorted(
        user_totals.items(),
        key=lambda kv: kv[1],
        reverse=True,
    )[: max(1, int(limit))]

    # 5) Build response payload
    all_quarter_labels = ["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"]
    payload: List[Dict[str, Any]] = []

    for user_id, _total in top_users:
        quarters_dict: Dict[str, Dict[str, int]] = {}

        # Ensure every quarter key exists (even if all zeros)
        for q_label in all_quarter_labels:
            counts = user_buckets[user_id].get(q_label, _empty_counts())
            # copy to avoid sharing same dict instance
            quarters_dict[q_label] = {
                "self_managed": counts["self_managed"],
                "team_lead": counts["team_lead"],
                "project_manager": counts["project_manager"],
                "team_of_PM_professionals": counts["team_of_PM_professionals"],
            }

        # For now, represent the user by UUID string;
        # later you can replace this with email or full_name via a join to users table.
        payload.append(
            {
                "user": str(user_id),
                "quarters": quarters_dict,
            }
        )

    logger.info("Computed user activity KPI for %d users", len(payload))
    return payload


-----


@router.get("/kpi/user-activity", response_model=List[UserActivityEntry])
async def user_activity(
    limit: int = Query(10, ge=1),
    session: AsyncSession = Depends(get_db_session),
) -> List[UserActivityEntry]:
    """
    Returns quarter counts of top N users per quarter.
    """
    try:
        data = await kpi_service.get_user_activity(session=session, limit=limit)
        return data
    except Exception:
        logger.exception("Failed to fetch users activity")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch users activity",
            )
