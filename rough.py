# src/app/services/update_charter_service.py
from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.logger import get_logger
from app.utils.json_sanitizer import _sanitize_for_db
from app.models.pydantic_models import ProjectCharter
from app.schemas.charter import Charter            # ORM model (used in create_charter)
from app.schemas.charter_section import CharterSection  # ORM model for consistency (not directly created here)
from app.services.charter_section_service import create_charter_sections
from app.services.charter_version_service import create_charter_version

logger = get_logger(__name__)


async def update_charter(
    session: AsyncSession,
    charter_id: UUID,
    incoming_json: Dict[str, Any],
    user_id: UUID,
    *,
    mark_pdf_pending: bool = False,
) -> Dict[str, Any]:
    """
    Update an existing charter row plus its sections and append a new version.

    - `incoming_json` should contain the full charter JSON (frontend sends updated parent JSON).
    - Validates the payload using ProjectCharter pydantic model (structure must match).
    - Updates the `charters` row (charter_json, last_modified_by/at, current_pdf).
    - Rebuilds charter sections using create_charter_sections().
    - Appends a charter version using create_charter_version().

    Returns: dict with 'charter_id' and 'version_id' (if created).
    """

    # 1) validate payload with ProjectCharter
    try:
        validated = ProjectCharter(**incoming_json)
    except Exception as e:
        logger.exception("Incoming charter JSON failed validation")
        raise

    # ensure the validated model has the correct charter_id
    try:
        # if model doesn't include charter_id or is None, set it explicitly
        if getattr(validated, "charter_id", None) is None:
            validated.charter_id = charter_id
    except Exception:
        # ignore immutability if any; we will still use incoming_json values
        incoming_json["charter_id"] = str(charter_id)

    # 2) Begin a transaction and update DB objects
    version_row = None
    async with session.begin():
        # 2a) fetch the Charter DB row (raise if missing)
        q = select(Charter).where(Charter.charter_id == charter_id)
        result = await session.execute(q)
        db_charter = result.scalar_one_or_none()
        if db_charter is None:
            raise ValueError(f"Charter with id {charter_id} not found")

        now = datetime.now(timezone.utc)

        # 2b) prepare sanitized JSON for storage (reuse sanitizer used elsewhere)
        try:
            # prefer the pydantic model dump if available (pydantic v2 `model_dump`)
            try:
                charter_payload = validated.model_dump()
            except Exception:
                # fallback for pydantic v1 or if model_dump isn't present
                charter_payload = dict(validated)

            charter_json_for_db = _sanitize_for_db(charter_payload)
        except Exception:
            # fallback to storing incoming_json raw (not ideal, but safe)
            logger.exception("Sanitizer failed; falling back to raw incoming JSON")
            charter_json_for_db = incoming_json

        # 2c) update db_charter fields based on screenshot conventions
        # set the JSON snapshot
        setattr(db_charter, "charter_json", charter_json_for_db)

        # set last modified fields (field names taken from create_charter screenshots)
        setattr(db_charter, "last_modified_by", user_id)
        setattr(db_charter, "last_modified_at", now)

        # handle current_pdf logic: mark pending or accept provided URL (common screenshot names: current_pdf)
        if mark_pdf_pending:
            setattr(db_charter, "current_pdf", "PENDING_PDF")
        else:
            # look for likely field names in incoming JSON or pydantic model
            pdf_url = None
            for key in ("charter_pdf_url", "current_pdf", "pdf_url", "charter_pdf"):
                pdf_url = incoming_json.get(key) or getattr(validated, key, None) if pdf_url is None else pdf_url
            if pdf_url:
                setattr(db_charter, "current_pdf", pdf_url)

        # persist update
        session.add(db_charter)
        await session.flush()

        # 2d) rebuild charter sections using the existing service
        # According to your screenshots create_charter_sections(session, charter, user_id) exists
        try:
            await create_charter_sections(session=session, charter=validated, user_id=user_id)
        except Exception:
            logger.exception("Failed while creating charter sections")
            raise

        # 2e) append a charter version (snapshot) using existing service
        try:
            version_row = await create_charter_version(session=session, charter=validated, user_id=user_id)
        except Exception:
            logger.exception("Failed to create charter version")
            raise

        # 2f) optional: update a "latest_version_id" or similar field if your Charter model has it
        # (some create flow screenshots hinted at storing placeholders; this is safe to attempt)
        try:
            version_id = getattr(version_row, "version_id", None) or getattr(version_row, "id", None)
            if version_id is not None and hasattr(db_charter, "latest_version_id"):
                setattr(db_charter, "latest_version_id", version_id)
                session.add(db_charter)
                await session.flush()
        except Exception:
            # not critical; continue
            logger.debug("Could not write latest_version_id to Charter row (field may not exist)")

    # transaction committed here
    logger.info("Updated charter %s and created version %s", charter_id, getattr(version_row, "version_id", None))

    return {
        "charter_id": str(charter_id),
        "version_id": getattr(version_row, "version_id", None) or getattr(version_row, "id", None) or None,
    }
