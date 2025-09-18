from flask import Blueprint, jsonify, request
from app.services import kpi_view
from app.utils.logger import get_logger

bp = Blueprint("kpi", __name__)
logger = get_logger(__name__)

@bp.route("/kpi/department-charters", methods=["GET"])
def department_charters():
    try:
        return jsonify(kpi_view.get_department_charters()), 200
    except Exception:
        logger.exception("Failed to fetch department charters")
        return jsonify({"error": "Failed to fetch department charters"}), 500

@bp.route("/kpi/returning-users", methods=["GET"])
def returning_users():
    days_raw = request.args.get("days", "15")
    try:
        days = int(days_raw)
    except Exception:
        logger.warning(f"Invalid days param: {days_raw}, defaulting to 15")
        days = 15
    try:
        data = kpi_view.get_returning_users(days=days)
        return jsonify(data), 200
    except Exception:
        logger.exception("Failed to fetch returning users")
        return jsonify({"error": "Failed to fetch returning users"}), 500

@bp.route("/kpi/user-activity", methods=["GET"])
def user_activity():
    limit_raw = request.args.get("limit", "10")
    try:
        limit = int(limit_raw)
    except Exception:
        logger.warning(f"Invalid limit param: {days_raw}, defaulting to 10")
        limit = 10
    try:
        data = kpi_view.get_user_activity(limit=limit)
        return jsonify(data), 200
    except Exception:
        logger.exception("Failed to fetch user activity")
        return jsonify({"error": "Failed to fetch users activity"}), 500


@bp.route("/kpi/charters-per-month", methods=["GET"])
def charters_per_month():
    try:
        data = kpi_view.get_charters_per_month()
        return jsonify(data), 200
    except Exception:
        logger.exception("Failed to fetch charters per month")
        return jsonify({"error": "Failed to fetch charters per month"}), 500
