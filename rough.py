# src/app/services/update_charter_service.py

from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Replace these paths with the exact imports in your repo if different
from app.models.pydantic_models import ProjectCharter
from app.utils.json_sanitizer import _sanitize_for_db
from app.utils.logger import get_logger

# ORM models used in create/update flows (these names used in your screenshots)
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
) -> Tuple[DBCharter, DBCharterSection, DBCharterVersion]:
    """
    Update the charter master row, update a single charter section (by name),
    and insert a new charter_versions snapshot.

    Parameters
    - session: AsyncSession (caller manages transaction scope)
    - charter: ProjectCharter (pydantic model with full/flat charter data)
    - user_id: UUID of the user making the update
    - charter_section_updated: Optional[str] name of the section that was changed (e.g. "assumptions")
    - current_pdf: Optional[str] new PDF URL (if frontend provided)

    Returns:
    - (db_charter, updated_section_row, version_row)
    """

    now = datetime.utcnow()

    # Sanitize and dump charter JSON for DB storage (consistent with create flows)
    charter_payload = charter.model_dump() if hasattr(charter, "model_dump") else charter.dict()
    charter_json = _sanitize_for_db(charter_payload)

    # --------------- Update charters table ----------------
    charter_id = getattr(charter, "charter_id", None)
    if charter_id is None:
        raise ValueError("charter.charter_id is required to update a charter")

    # Fetch existing charter row
    result = await session.execute(select(DBCharter).where(DBCharter.charter_id == charter_id))
    db_charter = result.scalars().one_or_none()

    if db_charter is None:
        # Business decision: create or raise? We choose to raise so we don't silently create
        # If you prefer to insert when missing, replace this with a creation block.
        raise ValueError(f"Charter with id {charter_id} not found")

    # Update fields on the ORM object
    db_charter.charter_json = charter_json
    db_charter.last_modified_by = user_id
    db_charter.last_modified_at = now
    if current_pdf is not None:
        db_charter.current_pdf = current_pdf

    # Add to session (probably already attached) to ensure it's persisted
    session.add(db_charter)

    # --------------- Update single charter_section (if provided) ---------------
    updated_section_row: Optional[DBCharterSection] = None
    if charter_section_updated:
        # Find the section value in the incoming pydantic payload
        # Your ProjectCharter -> sections mapping is built by _build_sections_from_charter
        # The frontend is sending a flat payload; we expect the field that represents that section
        # to be present in the payload. We'll construct the section JSON the same way create flow does:
        # -- build a mini mapping with only that section's content

        # safe lookup: patch from the raw payload
        section_payload = None
        if charter_payload and isinstance(charter_payload, dict):
            # For a "flat" payload, locate fields that correspond to the requested section.
            # We will attempt to build a minimal JSON object containing that section by reading
            # the attribute name matching the section key.
            #
            # Example: if charter_section_updated == "assumptions",
            # we expect charter_payload.get("assumptions")
            section_payload = charter_payload.get(charter_section_updated)

        # If the payload doesn't contain that section as a top-level key, create an empty object
        if section_payload is None:
            # Create an empty/placeholder section payload (so the DB section_json is valid JSON).
            section_payload = {}

        section_json = _sanitize_for_db(section_payload)

        # Try to fetch existing section row for (charter_id, section_name)
        q = select(DBCharterSection).where(
            DBCharterSection.charter_id == charter_id,
            DBCharterSection.section_name == charter_section_updated,
        )
        sec_res = await session.execute(q)
        existing_section = sec_res.scalars().one_or_none()

        if existing_section:
            # Update existing row
            existing_section.section_json = section_json
            existing_section.updated_by = user_id
            existing_section.updated_at = now
            session.add(existing_section)
            updated_section_row = existing_section
        else:
            # Insert new section row (handle race via IntegrityError fallback)
            new_section = DBCharterSection(
                charter_id=charter_id,
                section_name=charter_section_updated,
                section_json=section_json,
                updated_by=user_id,
                updated_at=now,
            )
            session.add(new_section)
            try:
                # Flush to persist (may raise IntegrityError if another process inserted same unique row)
                await session.flush()
                updated_section_row = new_section
                logger.info("Created missing charter_section '%s' for charter %s", charter_section_updated, charter_id)
            except IntegrityError:
                # Race happened: another transaction inserted the row; reload and update it
                await session.rollback()  # rollback this partial flush state
                # re-fetch and update
                sec_res = await session.execute(q)
                existing_section = sec_res.scalars().one_or_none()
                if existing_section is None:
                    # If still none, re-raise
                    raise
                existing_section.section_json = section_json
                existing_section.updated_by = user_id
                existing_section.updated_at = now
                session.add(existing_section)
                # flush again
                await session.flush()
                updated_section_row = existing_section

    # --------------- Insert a new charter_versions snapshot row ---------------
    version_row = DBCharterVersion(
        charter_id=charter_id,
        version_by=user_id,
        version_at=now,
        charter_json=charter_json,
    )
    session.add(version_row)

    # --------------- Finalize: flush so DB defaults/new PKs are populated ---------------
    await session.flush()

    logger.info("Updated charter %s (modified_by=%s). Inserted new version.", charter_id, user_id)

    # Return the ORM objects (still attached to session)
    # Note: updated_section_row may be None if charter_section_updated was not provided
    return db_charter, updated_section_row, version_row
