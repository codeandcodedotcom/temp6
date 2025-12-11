from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.utils.logger import get_logger
from app.db.session_new import get_db_session
from app.services.update_charter_service import update_charter
from app.api.update_charter import UpdateCharterRequest, UpdateCharterResponse  # adjust import path if needed

logger = get_logger(__name__)
router = APIRouter(tags=["charter"])


@router.put("/charter/{charter_id}/update", response_model=UpdateCharterResponse)
async def update_charter_endpoint(
    charter_id: UUID,
    payload: UpdateCharterRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update a charter (charter_json + last_modified columns), update a single
    charter_section identified by `payload.charter_section_updated` and insert
    a new charter_versions snapshot row.

    Request body must include user_id and the full/flat charter JSON (as we agreed).
    """

    # call service
    try:
        result = await update_charter(
            session=session,
            charter=payload.charter,           # if your payload is flat option B, adjust accordingly
            user_id=payload.user_id,
            charter_section_updated=payload.charter_section_updated,
            current_pdf=payload.current_pdf,
        )
    except HTTPException:
        # let service raise HTTPException for known cases
        raise
    except Exception as e:
        logger.exception("update_charter service failed")
        raise HTTPException(status_code=500, detail="Failed to update charter") from e

    # ---- handle tuple result ----
    if not isinstance(result, tuple):
        # defensive: if service changes, return clear error
        raise HTTPException(
            status_code=500,
            detail="update_charter service returned unexpected type (expected tuple)."
        )

    try:
        db_charter, updated_section_row, version_row = result
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="update_charter service returned tuple with unexpected length."
        )

    # Extract values defensively (use getattr so missing attributes don't crash)
    charter_id_val = getattr(db_charter, "charter_id", None) or charter_id
    # section name — your CharterSection model likely has section_name or section_id
    section_updated_val = (
        getattr(updated_section_row, "section_name", None)
        or getattr(updated_section_row, "section_id", None)
        or None
    )
    # version id — your CharterVersion likely exposes 'version_id' (or id)
    version_id_val = getattr(version_row, "version_id", None) or getattr(version_row, "id", None)

    response_body = {
        "charter_id": str(charter_id_val),
        "section_updated": section_updated_val,
        "version_id": str(version_id_val) if version_id_val is not None else None,
        "message": "Charter updated successfully",
    }

    return response_body
