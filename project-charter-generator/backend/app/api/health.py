from flask import Blueprint, jsonify, current_app
from app.utils.logger import get_logger
import os
import time

bp = Blueprint("health", __name__)
logger = get_logger(__name__)
START_TIME = time.time()

@bp.route("/health", methods=["GET"])
def health():
    """
    Liveness probe - returns 200 if the backend process is alive.
    """
    logger.info("Health check OK")
    return jsonify({"status": "ok"}), 200


@bp.route("/ready", methods=["GET"])
def ready():
    """
    Returns 200 only if essential config/dependencies appear present.
    """
    ok = True
    reasons = []

    # DB path exists (if using sqlite)
    db_path = getattr(current_app.config, "DB_PATH", None) or os.getenv("DATABASE_URL")
    if db_path and not os.path.exists(db_path):
        ok = False
        reasons.append(f"DB not found at {db_path}")

    if not getattr(current_app.config, "AZURE_OPENAI_KEY", None) and not os.getenv("AZURE_OPENAI_KEY"):
        reasons.append("AZURE_OPENAI_KEY not configured")

    # Basic payload
    payload = {
        "status": "ready" if ok else "not_ready",
        "uptime_seconds": int(time.time() - START_TIME),
        "reasons": reasons,
    }
    return jsonify(payload), (200 if ok else 503)

