# app/services/project_service.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project          # adjust import if your models module is different
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_project_record(
    session: AsyncSession,
    *,
    project_id: UUID,
    user_id: UUID,
    charter_data: Mapping[str, Any],
    total_score: int,
    created_at: datetime,
    department: Optional[str] = None,
) -> Project:
    """
    Create one row in `projects` table based on the generated charter JSON.

    Parameters
    ----------
    session:
        Active AsyncSession inside a transaction (async with session.begin()).
    project_id:
        UUID for this project (already generated in generation.ask).
    user_id:
        UUID of the user who owns the project (from AskRequest / frontend).
    charter_data:
        Dict coming from the LLM/ProjectCharter JSON (same keys as response).
    total_score:
        Computed complexity score (int).
    created_at:
        When this project/charter was created (datetime).
    department:
        Optional department; can come from request payload or user record.

    Returns
    -------
    Project ORM instance (already added & flushed).
    """

    logger.info(
        "Creating project %s for user %s with total_score=%s",
        project_id,
        user_id,
        total_score,
    )

    # Fallback helpers so we don't explode on missing keys
    title = (
        charter_data.get("project_name")
        or charter_data.get("project_title")
        or ""
    )
    budget = charter_data.get("budget") or ""
    sponsor = (
        charter_data.get("project_sponsor")
        or charter_data.get("sponsor")
        or ""
    )
    description = (
        charter_data.get("description")
        or charter_data.get("project_description")
        or ""
    )

    # “managed_by” – who should manage this project.
    # Try LLM JSON first, then scoring-based recommendation if you’ve put it there.
    managed_by = (
        charter_data.get("recommendation")
        or charter_data.get("complexity")
        or ""
    )

    project = Project(
        project_id=project_id,
        user_id=user_id,
        project_title=title,
        department=department or "",
        budget=budget,
        sponsor=sponsor,
        description=description,
        complexity_score=int(total_score),
        managed_by=managed_by,
        created_at=created_at,
    )

    session.add(project)
    await session.flush()  # get DB-side defaults if any

    logger.info("Project %s created for user %s", project_id, user_id)
    return project


# Optional convenience helpers – you can keep or delete as you like.

from sqlalchemy import select


async def get_project_by_id(
    session: AsyncSession,
    project_id: UUID,
) -> Optional[Project]:
    """Fetch a single project by its ID."""
    stmt = select(Project).where(Project.project_id == project_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def list_projects_for_user(
    session: AsyncSession,
    user_id: UUID,
    limit: int = 50,
) -> list[Project]:
    """Return recent projects for a given user."""
    stmt = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars())
