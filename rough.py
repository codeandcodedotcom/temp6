# src/app/api/update_charter.py
from typing import Any, Dict, Optional
from uuid import UUID
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session_new import get_db_session
from app.models.pydantic_models import ProjectCharter
from app.services.update_charter_service import update_charter as update_charter_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["charter"])


class UpdateCharterResponseDict(Dict[str, Any]):
    """
    Response will be a small dict; kept dynamic so we don't have to duplicate Pydantic models here.
    Keys:
      - charter_id: str
      - section_updated: Optional[str]
      - version_id: Optional[str]
      - message: str
    """


@router.put("/charter/{charter_id}/update", response_model=UpdateCharterResponseDict)
async def update_charter_endpoint(
    charter_id: UUID = Path(..., description="Charter ID to update (UUID)"),
    payload: Dict[str, Any] = Body(..., description="Flat charter payload (same shape frontend sends)"),
    session: AsyncSession = Depends(get_db_session),
) -> UpdateCharterResponseDict:
    """
    Update a charter:
      - Accepts a flat JSON (charter fields + extras)
      - Required extra: `user_id` (UUID)
      - Optional extras: `charter_section_updated` (str), `current_pdf` (str)
    The remainder of the body is validated against the ProjectCharter Pydantic model.
    """

    # ------------- Extract extras from flat payload -------------
    user_id_raw = payload.pop("user_id", None)
    if not user_id_raw:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{"loc": ["body", "user_id"], "msg": "Field required", "type": "missing"}],
        )

    try:
        user_id = UUID(str(user_id_raw))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{"loc": ["body", "user_id"], "msg": "Invalid UUID", "type": "value_error.uuid"}],
        )

    charter_section_updated: Optional[str] = payload.pop("charter_section_updated", None)
    current_pdf: Optional[str] = payload.pop("current_pdf", None)

    # ------------- Validate remaining payload as ProjectCharter (flat payload) -------------
    # The payload now contains the fields that make up the charter object (flat).
    try:
        charter_obj = ProjectCharter.parse_obj(payload)
    except Exception as exc:
        # Pydantic error -> convert to 422 with details so frontend sees validation issues
        logger.exception("ProjectCharter validation failed for update payload")
        # If pydantic raises ValidationError, it has .errors(); but keep generic fallback:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=getattr(exc, "errors", str(exc)),
        )

    # Ensure the incoming charter_id (path) matches the charter object if it has one
    # ProjectCharter likely has a charter_id field. If present, ensure it matches path param.
    try:
        incoming_charter_id = getattr(charter_obj, "charter_id", None)
        if incoming_charter_id and str(incoming_charter_id) != str(charter_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{
                    "loc": ["path", "charter_id"],
                    "msg": "Path charter_id does not match payload charter_id",
                    "type": "value_error"
                }]
            )
    except Exception:
        # If attribute access behaves oddly, ignore and proceed — primary key is path param.
        pass

    # ------------- Call service -------------
    try:
        db_charter, updated_section_row, version_row = await update_charter_service(
            session=session,
            charter=charter_obj,
            user_id=user_id,
            charter_section_updated=charter_section_updated,
            current_pdf=current_pdf,
        )
    except HTTPException:
        # propagate explicit service HTTPExceptions
        raise
    except Exception as exc:
        logger.exception("Unhandled exception in update_charter_service")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update charter due to server error",
        ) from exc

    # ------------- Build response -------------
    # charter_id: prefer db_charter.charter_id
    try:
        resp_charter_id = str(getattr(db_charter, "charter_id"))
    except Exception:
        resp_charter_id = str(charter_id)

    # section_updated: prefer explicit param or updated_section_row.section_name if available
    section_updated = charter_section_updated
    if not section_updated and updated_section_row is not None:
        section_updated = getattr(updated_section_row, "section_name", None)

    # version_id: if version_row exists and has version_id attribute
    version_id = None
    if version_row is not None:
        version_id = getattr(version_row, "version_id", None)
        if version_id is not None:
            version_id = str(version_id)

    response: UpdateCharterResponseDict = {
        "charter_id": resp_charter_id,
        "section_updated": section_updated,
        "version_id": version_id,
        "message": "Charter updated successfully",
    }

    return response
