# app/utils/json_sanitizer.py (or wherever you put it)
from datetime import datetime, date
from uuid import UUID
from typing import Any

try:
    # pydantic v2
    from pydantic import BaseModel
except ImportError:
    # pydantic v1 fallback
    from pydantic import BaseModel  # type: ignore


def _sanitize_for_db(value: Any) -> Any:
    """
    Recursively convert values so they can be stored in JSONB columns.

    - Pydantic models -> dict via .model_dump() / .dict()
    - UUID / datetime / date -> str (ISO)
    - dict / list -> walk recursively
    - everything else returned as-is
    """
    # 🔹 Handle Pydantic models (ProjectScope, BudgetBreakdown, Timeline, PMRoleProfile, etc.)
    if isinstance(value, BaseModel):
        try:
            value = value.model_dump()  # pydantic v2
        except AttributeError:
            value = value.dict()        # pydantic v1

    # 🔹 Dict: sanitize keys and values
    if isinstance(value, dict):
        return {str(k): _sanitize_for_db(v) for k, v in value.items()}

    # 🔹 List / tuple
    if isinstance(value, (list, tuple)):
        return [_sanitize_for_db(v) for v in value]

    # 🔹 UUID / datetime / date -> string
    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    # primitives are fine
    return value
