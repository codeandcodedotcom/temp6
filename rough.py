# src/app/api/update_charter.py
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session_new import get_db_session
from app.services.update_charter_service import update_charter
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["charter"])


@router.put("/api/charter/{charter_id}/update", status_code=status.HTTP_200_OK)
async def api_update_charter(
    charter_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Update a charter:
      - frontend sends full updated charter JSON in body
      - JSON must contain user_id
      - We update:
            * charters table (only timestamp + pdf if needed)
            * charter_sections table (replace one section)
            * charter_versions table (append full snapshot)
    """
    # Parse JSON body
    try:
        incoming_json = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(incoming_json, dict):
        raise HTTPException(status_code=400, detail="JSON must be an object")

    # Extract user_id → required
    user_id_raw = incoming_json.get("user_id")
    if not user_id_raw:
        raise HTTPException(status_code=400, detail="'user_id' is required in the request body")

    try:
        user_id = UUID(str(user_id_raw))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid 'user_id' format (must be UUID)")

    # Optional flag from frontend
    mark_pdf_pending = bool(incoming_json.get("mark_pdf_pending"))

    # Call the service
    try:
        result = await update_charter(
            session=db,
            charter_id=charter_id,
            incoming_json=incoming_json,
            user_id=user_id,
            mark_pdf_pending=mark_pdf_pending,
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to update charter %s", charter_id)
        raise HTTPException(status_code=500, detail="Failed to update charter")

    return {"ok": True, **result}
