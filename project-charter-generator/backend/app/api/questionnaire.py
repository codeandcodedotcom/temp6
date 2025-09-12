from flask import Blueprint, jsonify, current_app
import os, json
from app.config import Config

bp = Blueprint("questionnaire", __name__)

@bp.route("/questionnaire", methods=["GET"])
def get_questionnaire():
    """
    Return the questionnaire JSON used by the frontend.
    """

    path = getattr(Config, "QUESTIONNAIRE_PATH", None)
    if not path:
        current_app.logger.error("QUESTIONNAIRE_PATH not configured in Config")
        return jsonify({"error": "Server misconfiguration"}), 500

    if not os.path.exists(path):
        current_app.logger.error("Questionnaire file not found at %s", path)
        return jsonify({"error": "Questionnaire file not found"}), 404

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as e:
        current_app.logger.exception("Questionnaire JSON decode error at %s: %s", path, e)
        return jsonify({"error": "Questionnaire file is invalid JSON"}), 500
    except Exception as e:
        current_app.logger.exception("Failed to read questionnaire file at %s: %s", path, e)
        return jsonify({"error": "Failed to load questionnaire"}), 500

    current_app.logger.info(f"Loaded questionnaire from {path}")
    return jsonify(data), 200


# http://127.0.0.1:5000/api/questionnaire