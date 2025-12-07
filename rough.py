# app/services/project_service.py

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project
from app.models.pydantic_models import ProjectCharter
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_project_record(
    session: AsyncSession,
    *,
    user_id: UUID,
    charter: ProjectCharter,
    department: Optional[str] = None,
) -> Project:
    """
    Create one row in `projects` table from a validated ProjectCharter.
    Assumes we're already inside `async with session.begin():`.
    """

    logger.info(
        "Creating project %s for user %s (score=%s)",
        charter.project_id,
        user_id,
        charter.complexity_score,
    )

    project = Project(
        project_id=charter.project_id,
        user_id=user_id,
        project_title=charter.project_name,
        department=department or "",
        budget=charter.budget,
        sponsor=charter.project_sponsor,
        description=charter.description,
        # Pydantic has already ensured types; cast in case your model keeps score as str
        complexity_score=int(charter.complexity_score),
        managed_by=charter.managed_by,     # we’ll add this in step 2
        created_at=charter.created_at,
    )

    session.add(project)
    await session.flush()

    logger.info("Project %s created for user %s", charter.project_id, user_id)
    return project
