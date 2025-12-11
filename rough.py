from datetime import datetime
from typing import Optional, Tuple

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.logger import get_logger
from app.utils.json_sanitizer import _sanitize_for_db
from app.services.charter_section_service import _build_sections_from_charter
from app.models import Charter, CharterSection, CharterVersion  # adjust import path if needed
from app.models.pydantic_models import ProjectCharter  # adjust path to your pydantic model if different

logger = get_logger(__name__)


async def update_charter(
    session: AsyncSession,
    charter: ProjectCharter,
    user_id: UUID,
    *,
    charter_section_updated: Optional[str] = None,
    current_pdf: Optional[str] = None,
) -> Tuple[Charter, Optional[CharterSection], CharterVersion]:
    """
    Update an existing charter and related tables:
      - Update `charters` row: charter_json, last_modified_by, last_modified_at, current_pdf (if provided)
      - Update only the single charter section named `charter_section_updated`:
          update section_json, updated_by, updated_at (create row if it does not exist)
      - Insert a new charter_versions row (snapshot) with full charter_json

    Returns tuple: (updated_charter_row, updated_or_created_section_row_or_None, created_version_row)

    Notes:
    - Assumes `charter.charter_id` is present and matches the DB row key.
    - Uses _build_sections_from_charter() to extract section payloads.
    - Uses _sanitize_for_db() to prepare JSON for DB storage.
    """
    if not charter.charter_id:
        raise ValueError("charter.charter_id is required for update")

    now = datetime.utcnow()
    charter_id = charter.charter_id

    # ---------- Prepare sanitized JSON payload ----------
    charter_payload = charter.model_dump()  # pydantic BaseModel -> dict
    charter_json = _sanitize_for_db(charter_payload)

    # ---------- Find existing charter row ----------
    db_charter = await session.get(Charter, charter_id)
    if db_charter is None:
        raise ValueError(f"Charter with id {charter_id} not found")

    # ---------- Update charters table columns ----------
    db_charter.charter_json = charter_json
    # use the same column names as your model: last_modified_by / last_modified_at
    db_charter.last_modified_by = user_id
    db_charter.last_modified_at = now
    if current_pdf is not None:
        db_charter.current_pdf = current_pdf

    # persist change (flush later together with other ops)
    session.add(db_charter)

    # ---------- Update single charter_section (if requested) ----------
    updated_section_row: Optional[CharterSection] = None
    if charter_section_updated:
        # Build the mapping of sections -> payloads (reuse service helper)
        sections_map = _build_sections_from_charter(charter)  # expects dict[str, Any]
        if charter_section_updated not in sections_map:
            # frontend asked to update a section we don't have in the rendered charter
            raise ValueError(f"Section '{charter_section_updated}' not present in charter payload")

        new_section_payload = sections_map[charter_section_updated]
        sanitized_section_json = _sanitize_for_db(new_section_payload)

        # Try to fetch existing section row
        q = await session.execute(
            select(CharterSection).where(
                CharterSection.charter_id == charter_id,
                CharterSection.section_name == charter_section_updated,
            )
        )
        existing_section = q.scalars().one_or_none()

        if existing_section:
            # Update in-place
            existing_section.section_json = sanitized_section_json
            existing_section.updated_by = user_id
            existing_section.updated_at = now
            session.add(existing_section)
            updated_section_row = existing_section
            logger.info("Updated charter_section '%s' for charter %s", charter_section_updated, charter_id)
        else:
            # Create new row for that section
            new_row = CharterSection(
                charter_id=charter_id,
                section_name=charter_section_updated,
                section_json=sanitized_section_json,
                updated_by=user_id,
                updated_at=now,
            )
            session.add(new_row)
            # flush to get any DB defaults if caller expects ORM object filled
            await session.flush()
            updated_section_row = new_row
            logger.info("Created missing charter_section '%s' for charter %s", charter_section_updated, charter_id)

    # ---------- Insert new charter_versions row (snapshot) ----------
    version_row = CharterVersion(
        charter_id=charter_id,
        version_by=user_id,
        version_at=now,
        charter_json=charter_json,
    )
    session.add(version_row)

    # ---------- Final flush and return ----------
    await session.flush()

    logger.info("Updated charter %s (modified_by=%s). Inserted new version.", charter_id, user_id)

    return db_charter, updated_section_row, version_row



______

# src/app/api/update_charter.py
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

# adjust imports if your project layout differs
from app.models.pydantic_models import ProjectCharter
from app.services.update_charter_service import update_charter as svc_update_charter
from app.db.session_new import get_db_session  # per your screenshots
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["charter"])

class UpdateCharterRequest(BaseModel):
    charter: ProjectCharter
    user_id: UUID
    charter_section_updated: Optional[str] = None
    current_pdf: Optional[str] = None

class UpdateCharterResponse(BaseModel):
    charter_id: UUID
    section_updated: Optional[str] = None
    version_id: Optional[UUID] = None
    message: str

@router.put("/charter/{charter_id}/update", response_model=UpdateCharterResponse)
async def update_charter_endpoint(
    charter_id: UUID,
    payload: UpdateCharterRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update a charter (charter_json + last_modified columns + current_pdf),
    update a single charter_section identified by `charter_section_updated` (if provided),
    and insert a new charter_versions snapshot row.

    The request body must include `user_id` (UUID) and `charter` object (ProjectCharter).
    """
    # basic sanity: ensure path charter_id matches body.charter.charter_id if body contains one
    if payload.charter.charter_id and payload.charter.charter_id != charter_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path charter_id does not match charter.charter_id in request body.",
        )

    # Ensure pydantic model has the charter_id set if it was missing
    if not payload.charter.charter_id:
        # populate model with the path id (so service gets charter_id present)
        # ProjectCharter is a pydantic model; rebuild with charter_id set
        try:
            charter_dict = payload.charter.model_dump()
            charter_dict["charter_id"] = charter_id
            charter_obj = ProjectCharter.model_validate(charter_dict)
        except Exception as e:
            logger.exception("Failed to set charter_id on ProjectCharter: %s", e)
            raise HTTPException(status_code=400, detail="Invalid charter payload")
    else:
        charter_obj = payload.charter

    try:
        # Use a transaction boundary at the caller (session should be bound as in other endpoints).
        # If you usually use `async with session.begin():` in your stack, wrap caller there.
        db_charter, section_row, version_row = await svc_update_charter(
            session=session,
            charter=charter_obj,
            user_id=payload.user_id,
            charter_section_updated=payload.charter_section_updated,
            current_pdf=payload.current_pdf,
        )
    except ValueError as ve:
        # validation / not-found style errors from service
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        logger.exception("Error updating charter %s: %s", charter_id, exc)
        raise HTTPException(status_code=500, detail="Failed to update charter")

    # Try to extract version id if ORM populated it (may be None until committed depending on ORM)
    version_id = getattr(version_row, "version_id", None)

    return UpdateCharterResponse(
        charter_id=charter_id,
        section_updated=payload.charter_section_updated,
        version_id=version_id,
        message="Charter updated and version snapshot created",
)
