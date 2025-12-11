from typing import Any
from pydantic import ValidationError

@router.put("/charter/{charter_id}/update", response_model=UpdateCharterResponse)
async def update_charter_endpoint(
    charter_id: UUID,
    payload: dict,  # accept raw dict
    session: AsyncSession = Depends(get_db_session),
):
    # payload now is the raw flat object you were sending.
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    # build the ProjectCharter model from payload (flattened)
    try:
        # if payload already contains nested charter, prefer that
        charter_data = payload.get("charter", payload)
        # ensure charter_id in body matches path (optional)
        charter_data["charter_id"] = charter_data.get("charter_id", str(charter_id))
        charter_obj = ProjectCharter.model_validate(charter_data)
    except ValidationError as ve:
        # return the validation error to the client
        raise HTTPException(status_code=422, detail=ve.errors())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # now call your service with charter_obj, user_id, ...
