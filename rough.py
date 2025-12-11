# app/services/update_charter_service.py
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pydantic_models import ProjectCharter
from app.utils.json_sanitizer import _sanitize_for_db
from app.utils.logger import get_logger

# ORM models (match the names in your screenshots)
from app.schemas.charter import Charter as DBCharter
from app.schemas.charter_section import CharterSection as DBCharterSection
from app.schemas.charter_version import CharterVersion as DBCharterVersion

logger = get_logger(__name__)


async def update_charter(
    session: AsyncSession,
    charter: ProjectCharter,
    user_id: UUID,
    *,
    charter_section_updated: Optional[str] = None,
    current_pdf: Optional[str] = None,
) -> Tuple[DBCharter, Optional[DBCharterSection], DBCharterVersion]:
    """
    Update charters table (charter_json + last_modified_* + current_pdf),
    update a single charter_sections row (section_json + updated_*) if requested,
    and insert a new charter_versions snapshot row.
    """
    now = datetime.utcnow()

    # get flat payload and sanitized json for DB
    charter_payload = charter.model_dump() if hasattr(charter, "model_dump") else charter.dict()
    charter_json = _sanitize_for_db(charter_payload)

    # charter_id must be present
    charter_id = getattr(charter, "charter_id", None) or charter_payload.get("charter_id")
    if charter_id is None:
        raise ValueError("charter.charter_id is required to update a charter")

    # fetch existing charter row
    res = await session.execute(select(DBCharter).where(DBCharter.charter_id == charter_id))
    db_charter = res.scalars().one_or_none()
    if db_charter is None:
        raise ValueError(f"Charter with id {charter_id} not found")

    # update charter master row
    db_charter.charter_json = charter_json
    db_charter.last_modified_by = user_id
    db_charter.last_modified_at = now
    if current_pdf is not None:
        db_charter.current_pdf = current_pdf

    session.add(db_charter)

    # optional: update single section
    updated_section_row: Optional[DBCharterSection] = None
    if charter_section_updated:
        # try to find section payload in incoming flat payload
        section_payload = None
        if isinstance(charter_payload, dict):
            section_payload = charter_payload.get(charter_section_updated)
        if section_payload is None:
            section_payload = {}
        section_json = _sanitize_for_db(section_payload)

        # try to fetch existing section row
        q = select(DBCharterSection).where(
            DBCharterSection.charter_id == charter_id,
            DBCharterSection.section_name == charter_section_updated,
        )
        sec_res = await session.execute(q)
        existing_section = sec_res.scalars().one_or_none()

        if existing_section:
            existing_section.section_json = section_json
            existing_section.updated_by = user_id
            existing_section.updated_at = now
            session.add(existing_section)
            updated_section_row = existing_section
        else:
            # insert new section row (handle race using flush + IntegrityError)
            new_section = DBCharterSection(
                charter_id=charter_id,
                section_name=charter_section_updated,
                section_json=section_json,
                updated_by=user_id,
                updated_at=now,
            )
            session.add(new_section)
            try:
                await session.flush()
                updated_section_row = new_section
                logger.info("Created missing charter_section %s for charter %s", charter_section_updated, charter_id)
            except IntegrityError:
                # another process inserted the same row concurrently -> rollback and re-fetch
                await session.rollback()
                sec_res = await session.execute(q)
                existing_section = sec_res.scalars().one_or_none()
                if existing_section is None:
                    # if still missing, re-raise
                    raise
                existing_section.section_json = section_json
                existing_section.updated_by = user_id
                existing_section.updated_at = now
                session.add(existing_section)
                await session.flush()
                updated_section_row = existing_section

    # insert new charter_version snapshot
    version_row = DBCharterVersion(
        charter_id=charter_id,
        version_by=user_id,
        version_at=now,
        charter_json=charter_json,
    )
    session.add(version_row)

    # final persist: commit so changes are durable
    await session.commit()

    logger.info("Updated charter %s (modified_by=%s). Inserted new version.", charter_id, user_id)

    return db_charter, updated_section_row, version_row


-------

# app/api/update_charter.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session_new import get_db_session
from app.services.update_charter_service import update_charter
from app.models.pydantic_models import ProjectCharter
from app.utils.logger import get_logger

router = APIRouter(tags=["charter"])
logger = get_logger(__name__)


# ---------- Request Model ----------
class UpdateCharterRequest(BaseModel):
    # Flat payload containing the whole charter fields
    user_id: UUID
    charter_section_updated: Optional[str] = None
    current_pdf: Optional[str] = None

    # Everything else should be accepted as part of the flat payload
    # so allow arbitrary extra fields
    class Config:
        extra = "allow"


# ---------- Response Model ----------
class UpdateCharterResponse(BaseModel):
    charter_id: UUID
    section_updated: Optional[str] = None
    version_id: Optional[int] = None
    message: str


# ---------- Endpoint ----------
@router.put("/charter/{charter_id}/update", response_model=UpdateCharterResponse)
async def update_charter_endpoint(
    charter_id: UUID,
    payload: UpdateCharterRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update charter, charter section (optional), and insert a new version snapshot.
    """
    try:
        # Build ProjectCharter pydantic model from flat payload
        # Include charter_id because service expects it inside the model
        flat_payload = payload.dict()
        flat_payload["charter_id"] = charter_id

        charter_model = ProjectCharter(**flat_payload)

        db_charter, updated_section, version_row = await update_charter(
            session=session,
            charter=charter_model,
            user_id=payload.user_id,
            charter_section_updated=payload.charter_section_updated,
            current_pdf=payload.current_pdf,
        )

        return UpdateCharterResponse(
            charter_id=db_charter.charter_id,
            section_updated=payload.charter_section_updated,
            version_id=version_row.version_id,
            message="Charter updated successfully",
        )

    except Exception as e:
        logger.error(f"Update charter failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
