# app/services/charter_service.py

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Charter  # your SQLAlchemy model for "charters"
from app.models.pydantic_models import ProjectCharter
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_charter(
    session: AsyncSession,
    charter: ProjectCharter,
    user_id: UUID,
    project_id: Optional[UUID] = None,
) -> Charter:
    """
    Persist a charter row linked to a project.

    - charter: validated ProjectCharter pydantic model
    - user_id: user who triggered generation (created_by / last_modified_by)
    - project_id: FK to projects table (defaults to charter.project_id)
    """
    now = datetime.now(timezone.utc)

    effective_project_id = project_id or charter.project_id

    # Full JSON for storage in jsonb
    charter_json: Dict[str, Any] = charter.model_dump(mode="python")

    db_charter = Charter(
        charter_id=charter.charter_id,
        project_id=effective_project_id,
        charter_json=charter_json,
        created_by=user_id,
        created_at=now,
        last_modified_by=user_id,
        last_modified_at=now,
        # placeholder until PDF generation is wired
        current_pdf="PENDING_PDF",
    )

    session.add(db_charter)
    await session.flush()  # so IDs are available if needed

    logger.info(
        "Charter %s created for project %s by user %s",
        db_charter.charter_id,
        effective_project_id,
        user_id,
    )

    return db_charter


-----
from app.services.charter_service import create_charter

-----
charter = ProjectCharter(**response)

try:
    async with session.begin():
        project = await create_project(
            session=session,
            charter=charter,
            user_id=payload.user_id,
        )

        # NEW: store charter JSON
        await create_charter(
            session=session,
            charter=charter,
            user_id=payload.user_id,
            project_id=project.project_id,
        )

        await create_answers(
            session=session,
            project_id=project.project_id,
            user_id=payload.user_id,
            raw_questions=questions,
        )

