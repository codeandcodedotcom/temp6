# app/services/charter_section_service.py

from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.logger import get_logger
from app.models.pydantic_models import ProjectCharter
from app.db.models import CharterSection  # adjust import path to your SQLAlchemy models

logger = get_logger(__name__)


def _build_sections_from_charter(charter: ProjectCharter) -> Dict[str, Any]:
    """
    Build a mapping of section_name -> JSON-serialisable content
    from the full ProjectCharter object.

    This is what will be stored in the `charter_sections.section_json` column.
    """

    # You can tweak these groupings later to match exactly how
    # the frontend wants to display sections.
    return {
        # Overview / header section
        "project_overview": {
            "project_name": charter.project_name,
            "description": charter.description,
            "industry": charter.industry,
            "duration": charter.duration,
            "budget": charter.budget,
            "project_sponsor": charter.project_sponsor,
            "complexity_score": charter.complexity_score,
            "managed_by": charter.managed_by,
            "date": charter.date,
        },

        # Core narrative sections
        "current_state": charter.current_state,
        "objectives": charter.objectives,
        "future_state": charter.future_state,
        "high_level_requirement": charter.high_level_requirement,
        "business_benefit": charter.business_benefit,

        # Structured sections
        "project_scope": charter.project_scope,
        "budget_breakdown": charter.budget_breakdown,
        "timeline": charter.timeline,
        "dependencies": charter.dependencies,
        "risks_and_mitigation": charter.risks_and_mitigation,

        # Lessons / recommendations
        "pm_resource_recommendation": charter.pm_resource_recommendation,
        "lesson_learnt": charter.lesson_learnt,
        "success_criteria": charter.success_criteria,
        "assumptions": charter.assumptions,
    }


async def create_charter_sections(
    session: AsyncSession,
    *,
    charter: ProjectCharter,
    user_id: UUID,
) -> List[CharterSection]:
    """
    Create one row per section in the `charter_sections` table
    for the given charter.

    - Uses `charter.charter_id` as FK.
    - Uses `user_id` as `updated_by`.
    """

    if not charter.charter_id:
        # Defensive check – charter_id should have been set in generation.py
        raise ValueError("charter.charter_id is required to create charter sections")

    charter_id = charter.charter_id
    now = datetime.now(timezone.utc)

    sections = _build_sections_from_charter(charter)

    created: List[CharterSection] = []

    for section_name, section_payload in sections.items():
        section_row = CharterSection(
            charter_id=charter_id,
            section_name=section_name,
            section_json=section_payload,
            updated_by=user_id,
            updated_at=now,
        )
        session.add(section_row)
        created.append(section_row)

    if created:
        await session.flush()

    logger.info(
        "Created %s charter_sections rows for charter %s",
        len(created),
        charter_id,
    )

    return created



-----------


