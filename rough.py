# app/api/update_charter.py
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.db.session_new import get_db_session
from app.models.pydantic_models import ProjectCharter  # adjust import path if different
from app.services.update_charter_service import update_charter  # your service function
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["charter"])


class UpdateCharterResponseModel(Dict[str, Any]):
    """
    Minimal response structure returned to client.
    You can replace with a pydantic BaseModel if you prefer.
    Keys: charter_id (UUID), section_updated (Optional[str]), version_id (Optional[UUID]), message (str)
    """
    pass


@router.put(
    "/charter/{charter_id}/update",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
)
async def update_charter_endpoint(
    charter_id: UUID,
    payload: Dict[str, Any],  # accept raw flat payload from frontend
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update a charter: update charters JSON + last_modified columns, update a single charter_section
    (identified by 'charter_section_updated' in payload), and insert a new charter_version row.

    The frontend will send a FLAT payload (the same structure as the backend often returns).
    This endpoint supports two shapes:
      1) payload contains a top-level "charter" key: {"charter": {...}, "user_id": "...", ...}
      2) payload is flat: {"user_id": "...", "project_title": "...", "description": "...", ...}
    """
    # --- required top-level fields ---
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{"loc": ["body", "user_id"], "msg": "Field required", "type": "value_error.missing"}],
        )

    # optional helpers
    charter_section_updated: Optional[str] = payload.get("charter_section_updated")
    current_pdf: Optional[str] = payload.get("current_pdf")

    # Build the ProjectCharter model. Support both nested and flat payloads.
    # If payload has "charter" key, prefer that; otherwise use the whole payload as charter data.
    charter_raw = payload.get("charter", payload.copy())

    # Ensure the charter_id is consistent with URL path if not provided
    charter_raw.setdefault("charter_id", str(charter_id))

    # Validate and build ProjectCharter (pydantic v2 .model_validate used across your codebase)
    try:
        charter_obj = ProjectCharter.model_validate(charter_raw)
    except ValidationError as ve:
        # Return pydantic validation errors with 422
        logger.debug("ProjectCharter validation failed: %s", ve.errors())
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=ve.errors())
    except Exception as e:
        logger.exception("Unexpected error while validating charter payload")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Call service to perform updates. Keep service boundaries thin (you said update_charter_service handles everything).
    try:
        # service signature expected:
        # update_charter(session, charter: ProjectCharter, user_id: UUID|str,
        #                charter_section_updated: Optional[str] = None, current_pdf: Optional[str] = None)
        result = await update_charter(
            session=session,
            charter=charter_obj,
            user_id=UUID(str(user_id)),
            charter_section_updated=charter_section_updated,
            current_pdf=current_pdf,
        )
    except HTTPException:
        # let service raise HTTPException if appropriate (e.g. not found) - re-raise
        raise
    except Exception as e:
        logger.exception("Failed to update charter %s", charter_id)
        # don't leak internals
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update charter")

    # result expected to be something like {"charter_id": <UUID>, "section_updated": "assumptions", "version_id": <UUID>}
    response_body = {
        "charter_id": str(result.get("charter_id", charter_id)),
        "section_updated": result.get("section_updated"),
        "version_id": str(result.get("version_id")) if result.get("version_id") else None,
        "message": result.get("message", "Charter updated"),
    }

    return response_body
