import json
import threading
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from app.config import Config
# from app.db import SessionLocal
# from app.models.error_log import ErrorLog
from app.utils.logger import get_logger

logger = get_logger(__name__)
_FALLBACK_FILE = Config.ERROR_LOG_FALLBACK_FILE
_USE_DB = Config.USE_DB_FOR_ERRORS


def _write_jsonl_line(path, obj) -> None:
    """Append one JSON object to path."""
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, default=str) + "\n")
    except Exception:
        try:
            logger.exception(f"ERROR: failed to write error log to file {path}")
            logger.info(json.dumps(obj, default=str))
        except Exception:
            pass


def _persist_to_db(payload) -> None:
    """
    Persist payload to DB if enabled; otherwise fallback to JSONL.
    """
    if not _USE_DB:
        _write_jsonl_line(_FALLBACK_FILE, payload)
        return

    try:
        # db = SessionLocal()
        # rec = ErrorLog(
        #     created_at=payload.get("created_at"),
        #     service=payload.get("service"),
        #     function=payload.get("function"),
        #     exception_type=payload.get("exception_type"),
        #     message=payload.get("message"),
        #     traceback=payload.get("traceback"),
        #     severity=payload.get("severity"),
        #     request_path=payload.get("request_path"),
        #     http_method=payload.get("http_method"),
        # )
        # db.add(rec); db.commit(); db.close()
        raise NotImplementedError("DB persistence not implemented in this file")
    except Exception:
        # fallback to JSONL so logs are not lost
        _write_jsonl_line(_FALLBACK_FILE, payload)


def _enqueue_persist(payload) -> None:
    """Persist payload in a background thread (non-blocking)."""
    try:
        t = threading.Thread(target=_persist_to_db, args=(payload,), daemon=True)
        t.start()
    except Exception:
        # if thread spawn fails, attempt synchronous persist
        _persist_to_db(payload)



def log_exception(exc: Exception,*,service: Optional[str] = None,function: Optional[str] = None,request: Optional[Any] = None,severity: str = "ERROR") -> None:
    """
    Record an exception.
    """
    try:
        short_message = str(exc)
    except Exception:
        short_message = "<error reading exception message>"

    try:
        full_trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    except Exception:
        full_trace = "<error reading traceback>"

    payload = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "service": service or "<unknown>",
        "function": function or "<unknown>",
        "exception_type": type(exc).__name__,
        "message": short_message,
        "traceback": full_trace,
        "severity": severity,
        "request_path": getattr(request, "path", None) if request is not None else None,
        "http_method": getattr(request, "method", None) if request is not None else None,
    }

    # write asynchronously
    try:
        _enqueue_persist(payload)
    except Exception:
        _persist_to_db(payload)
