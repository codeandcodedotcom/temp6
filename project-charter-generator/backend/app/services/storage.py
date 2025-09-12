import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.config import Config
from app.utils.logger import get_logger

logger = get_logger(__name__)

_db_default = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "database.db"))
DB_PATH = getattr(Config, "DB_PATH", None) or os.getenv("DATABASE_URL") or _db_default
DB_PATH = os.path.abspath(DB_PATH)

MAX_RESULT_CHARS = int(getattr(Config, "MAX_RESULT_CHARS", 200_000))


def _get_conn():
    """Return a sqlite3 connection configured for simple concurrent use."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        # Better concurrency and foreign key enforcement
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.close()
    except Exception:
        logger.exception("Failed to set sqlite pragmas")
    return conn


def _ensure_db():
    """Create submissions table if not exists (convenience for dev)."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                sponsor TEXT,
                payload_json TEXT,
                result_json TEXT,
                complexity_score REAL,
                recommended_pm_count INTEGER,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.commit()
        cur.close()
    except Exception:
        logger.exception("Failed to ensure DB schema")
        raise
    finally:
        conn.close()


def store_submission(payload: Dict[str, Any]) -> int:
    """
    Insert the incoming submission payload (raw JSON).
    Returns the inserted row id (int).
    """
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        project_name = payload.get("project_title") or payload.get("project_name") or None
        sponsor = payload.get("sponsor") or None
        payload_text = json.dumps(payload, ensure_ascii=False)

        created_at = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """
            INSERT INTO submissions
            (project_name, sponsor, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_name, sponsor, payload_text, created_at, created_at),
        )
        rowid = cur.lastrowid
        conn.commit()
        cur.close()
        logger.info(f"Stored submission id={rowid}")
        return int(rowid)
    except Exception:
        conn.rollback()
        logger.exception("Failed to store submission")
        raise
    finally:
        conn.close()


def save_result(submission_id: int, result: Dict[str, Any]) -> None:
    """
    Save LLM result (a dict) for the given submission id.
    Updates result_json, complexity_score and recommended_pm_count where available.
    """
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        try:
            result_text = json.dumps(result, ensure_ascii=False)
        except Exception:
            logger.exception("Failed to JSON-serialize result; storing stringified version")
            result_text = str(result)

        # Truncate if too large (or switch to blob storage in future)
        if len(result_text) > MAX_RESULT_CHARS:
            logger.warning(
                "Result JSON too large (%d chars); truncating to %d chars", len(result_text), MAX_RESULT_CHARS
            )
            result_text = result_text[:MAX_RESULT_CHARS]

        complexity = None
        pm_count = None
        if isinstance(result, dict):
            try:
                complexity = float(result.get("complexity_score") or result.get("total_score") or None)
            except Exception:
                complexity = None
            try:
                pm_count = int(result.get("recommended_pm_count") or result.get("pm_count") or 0)
            except Exception:
                pm_count = None

        updated_at = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """
            UPDATE submissions
            SET result_json = ?, complexity_score = ?, recommended_pm_count = ?, updated_at = ?
            WHERE id = ?
            """,
            (result_text, complexity, pm_count, updated_at, submission_id),
        )
        if cur.rowcount == 0:
            logger.warning("save_result: no submission found with id=%s", submission_id)
        conn.commit()
        cur.close()
    except Exception:
        conn.rollback()
        logger.exception("Failed to save result for submission_id=%s", submission_id)
        raise
    finally:
        conn.close()


def list_submissions(limit: int = 100) -> List[Dict[str, Any]]:
    """Return most recent submissions (as plain dicts)."""
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, project_name, sponsor, payload_json, result_json, complexity_score, recommended_pm_count, created_at, updated_at
            FROM submissions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()

        out = []
        for r in rows:
            payload = None
            result = None
            try:
                payload = json.loads(r["payload_json"]) if r["payload_json"] else None
            except Exception:
                payload = r["payload_json"]
            try:
                result = json.loads(r["result_json"]) if r["result_json"] else None
            except Exception:
                result = r["result_json"]

            out.append(
                {
                    "id": r["id"],
                    "project_name": r["project_name"],
                    "sponsor": r["sponsor"],
                    "payload": payload,
                    "result": result,
                    "complexity_score": r["complexity_score"],
                    "recommended_pm_count": r["recommended_pm_count"],
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                }
            )
        return out
    except Exception:
        logger.exception("Failed to list submissions")
        raise
    finally:
        conn.close()


def get_submission(submission_id: int) -> Optional[Dict[str, Any]]:
    """Return a single submission by id or None."""
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, project_name, sponsor, payload_json, result_json, complexity_score, recommended_pm_count, created_at, updated_at
            FROM submissions
            WHERE id = ?
            """,
            (submission_id,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return None

        payload = None
        result = None
        try:
            payload = json.loads(row["payload_json"]) if row["payload_json"] else None
        except Exception:
            payload = row["payload_json"]
        try:
            result = json.loads(row["result_json"]) if row["result_json"] else None
        except Exception:
            result = row["result_json"]

        return {
            "id": row["id"],
            "project_name": row["project_name"],
            "sponsor": row["sponsor"],
            "payload": payload,
            "result": result,
            "complexity_score": row["complexity_score"],
            "recommended_pm_count": row["recommended_pm_count"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    except Exception:
        logger.exception("Failed to get submission id=%s", submission_id)
        raise
    finally:
        conn.close()
