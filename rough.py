from collections import defaultdict
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.project import Project
from app.schemas.users import User

logger = get_logger(__name__)


def _empty_counts() -> Dict[str, int]:
    return {
        "self_managed": 0,
        "project_lead": 0,
        "project_manager": 0,
        "team_of_PM_professionals": 0,
    }


async def get_user_activity(
    session: AsyncSession,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    KPI: Top N users by total charters, with quarter-wise PM band breakdown.
    """

    # --- Fetch all projects that have a user & created_at & managed_by ---

    stmt = (
        select(
            Project.user_id,
            User.email,
            Project.managed_by,
            Project.created_at,
        )
        .join(User, User.user_id == Project.user_id)
        .where(
            Project.user_id.isnot(None),
            Project.created_at.isnot(None),
            Project.managed_by.isnot(None),
        )
    )

    result = await session.execute(stmt)
    rows = result.all()

    if not rows:
        logger.info("No projects found for user activity KPI.")
        return []

    # --- Aggregate per (user_key, quarter_label) ---

    # user_key is **email string** (fallback to user_id string)
    # user_buckets[user_key][quarter_label] = { band -> count }
    user_buckets: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
        lambda: defaultdict(_empty_counts)
    )

    for user_id, email, managed_by, created_at in rows:
        # email is our primary identity in the KPI
        user_key = email or str(user_id)

        # Map text in managed_by column -> KPI band key
        raw = (managed_by or "").strip().lower()

        if raw.startswith("self"):
            band_key = "self_managed"
        elif raw.startswith("project lead"):
            band_key = "project_lead"
        elif raw.startswith("project manager"):
            band_key = "project_manager"
        elif raw.startswith("team of pm"):
            band_key = "team_of_PM_professionals"
        else:
            logger.warning("Unknown managed_by value for KPI: %r", managed_by)
            continue

        # Which FY quarter?
        q = _fy_quarter(created_at)              # "Q1"…"Q4"
        quarter_label = _quarter_label_from_fy(q)  # "Quarter 1"…"Quarter 4"

        user_buckets[user_key][quarter_label][band_key] += 1

    # --- Compute total charters per user (for ranking) ---

    user_totals: Dict[str, int] = {}

    for user_key, qdict in user_buckets.items():
        total = 0
        for counts in qdict.values():
            total += (
                counts["self_managed"]
                + counts["project_lead"]
                + counts["project_manager"]
                + counts["team_of_PM_professionals"]
            )
        user_totals[user_key] = total

    # Pick top N users by total charters (descending)
    top_users = sorted(
        user_totals.items(),
        key=lambda kv: kv[1],
        reverse=True,
    )[: max(1, int(limit))]

    # --- Build response payload ---

    all_quarter_labels = ["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"]
    payload: List[Dict[str, Any]] = []

    for user_key, _total in top_users:
        quarters_dict: Dict[str, Dict[str, int]] = {}

        # Ensure every quarter key exists (even if all zeros)
        for q_label in all_quarter_labels:
            counts = user_buckets[user_key].get(q_label, _empty_counts())
            # copy to avoid sharing same dict instance
            quarters_dict[q_label] = {
                "self_managed": counts["self_managed"],
                "project_lead": counts["project_lead"],
                "project_manager": counts["project_manager"],
                "team_of_PM_professionals": counts["team_of_PM_professionals"],
            }

        payload.append(
            {
                # This is the **email** (or user_id as string fallback)
                "user": user_key,
                "quarters": quarters_dict,
            }
        )

    logger.info("Computed user activity KPI for %d users", len(payload))
    return payload
