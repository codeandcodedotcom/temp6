import json, os, threading
from typing import Any, Dict, List
from operator import itemgetter
from app.config import Config

KPI_FILE_PATH = getattr(Config, "KPI_FILE_PATH")

_lock = threading.Lock()
_cache: Dict[str, Any] = {"mtime": None, "data": None}


def _load_file() -> Dict[str, Any]:
    if not os.path.exists(KPI_FILE_PATH):
        return {}
    with open(KPI_FILE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _get_data() -> Dict[str, Any]:
    with _lock:
        try:
            mtime = os.path.getmtime(KPI_FILE_PATH)
        except OSError:
            mtime = None
        if _cache["data"] is None or _cache["mtime"] != mtime:
            _cache["data"] = _load_file()
            _cache["mtime"] = mtime
        return _cache["data"] or {}


def get_department_charters() -> List[Dict]:
    data = _get_data()
    return [dict(d) for d in data.get("department_charters", [])]


def total_charters() -> int:
    return sum(int(d.get("charterCount", 0)) for d in get_department_charters())


def avg_charters_per_department() -> float:
    """Return total/average charters from KPI data."""
    arr = get_department_charters()
    return (total_charters() / len(arr)) if arr else 0.0


def top_departments(limit: int = 3) -> List[Dict]:
    arr = get_department_charters()
    sorted_list = sorted(arr, key=itemgetter("charterCount"), reverse=True)
    return [dict(i) for i in sorted_list[: max(1, int(limit))]]


def get_returning_users(days: int = 15) -> List[Dict]:
    """
    Return the last `days` items from `returning_users` in file.
    Assumes entries are in chronological order oldest->newest.
    """
    data = _get_data()
    arr = data.get("returning_users", [])
    if not arr:
        return []
    try:
        days = int(days)
    except Exception:
        days = 15
    return [dict(i) for i in arr[-days:]]


def get_user_activity(limit: int = 10) -> List[Dict]:
    """Return most recent user activity events, up to `limit` entries."""
    data = _get_data()
    arr = data.get("user_activity", [])
    try:
        limit = int(limit)
    except Exception:
        limit = 10
    return [dict(i) for i in arr[: max(0, limit) ]]
