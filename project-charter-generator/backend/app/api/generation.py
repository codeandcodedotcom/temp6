import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import Blueprint, request, jsonify

from app.config import Config
from app.utils.logger import get_logger
from app.services import azure_openai, prompt_builder, scoring

bp = Blueprint("generation", __name__)
logger = get_logger(__name__)


def _compute_total_score(questions: List[Dict[str, Any]]) -> int:
    """
    Compute total score from frontend questions.
    """
    total = 0
    if not isinstance(questions, list):
        return 0
    for q in questions:
        try:
            if not isinstance(q, dict):
                continue
            if q.get("score") is not None:
                total += int(q.get("score") or 0)
                continue
            opts = q.get("options") or []
            if isinstance(opts, list) and len(opts) > 0:
                first = opts[0]
                if isinstance(first, dict) and first.get("score") is not None:
                    total += int(first.get("score") or 0)
        except Exception:
            logger.warning("Could not parse question score, ignoring: %s", q, exc_info=False)
    return int(total)


def _try_parse_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Try to extract the first JSON object from text and parse it.
    Returns dict if parse succeeds, else None.
    """
    if not text:
        return None
    # crude extraction: first { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        try:
            return json.loads(text)
        except Exception:
            return None
    candidate = text[start : end + 1]
    try:
        return json.loads(candidate)
    except Exception:
        try:
            return json.loads(text)
        except Exception:
            return None


@bp.route("/ask", methods=["POST"])
def ask():
    """
    Accept frontend payload and return LLM-generated project charter JSON.
    """
    try:
        data: Dict[str, Any] = request.get_json(force=True)
    except Exception:
        logger.exception("Failed to parse request JSON")
        return jsonify({"error": "Invalid JSON"}), 400

    if not isinstance(data, dict):
        return jsonify({"error": "Request JSON must be an object"}), 400

    project_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    questions = data.get("questions", []) or []
    if not isinstance(questions, list):
        return jsonify({"error": "Missing or invalid 'questions' field"}), 400

    # compute score and scoring summary
    total_score = _compute_total_score(questions)
    try:
        scoring_info = scoring.interpret_score(total_score)
    except Exception:
        logger.exception("scoring.interpret_score failed; using fallback")
        scoring_info = {"complexity": None, "recommendation": None, "rationale": None}

    scoring_summary = (
        f"Total score: {total_score}\n"
        f"Complexity (expected): {scoring_info.get('complexity')}\n"
        f"Recommendation (expected): {scoring_info.get('recommendation')}\n"
        f"Rationale (expected): {scoring_info.get('rationale')}\n"
        f"Recommended Project Manager Count: {scoring_info.get('recommended_pm_count')}\n"
    )

    logger.info(f"Total score: {total_score}")

    # Build prompt via prompt_builder (pass full payload + scoring summary)
    try:
        prompt = prompt_builder.build_prompt(data, scoring_summary)
    except Exception:
        logger.exception("prompt_builder.build_prompt failed; falling back to JSON prompt")
        try:
            payload_json = json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            payload_json = str(data)
        prompt = (
            "Generate a project charter JSON object from the input below. Return JSON only.\n\n"
            f"{payload_json}\n\nScoring:\n{scoring_summary}"
        )

    # log prompt size
    try:
        prompt_len = len(prompt)
        logger.info(f"Prompt length: {prompt_len}")
    except Exception:
        pass

    # max_tokens = int(getattr(Config, "AZURE_MAX_TOKENS", getattr(Config, "MAX_TOKENS", 800)))
    # temperature = float(getattr(Config, "AZURE_TEMPERATURE", 0.2))

    # Call Azure LLM
    try:
        llm_text = azure_openai.generate_answer(prompt=prompt)
    except Exception as e:
        logger.exception("LLM generation failed")
        err_str = str(e).lower()
        if "timeout" in err_str:
            return jsonify({"error": "LLM request timed out"}), 504
        return jsonify({"error": "LLM generation failed"}), 502

    # parse LLM output to JSON
    parsed = _try_parse_json_from_text(llm_text) or {}

    # build response using parsed values where available, else fallback to input/defaults
    response = {
        "project_id": project_id,
        "created_at": created_at,
        "project_title": parsed.get("project_title") or data.get("project_title") or "",
        "industry": parsed.get("industry") or data.get("domain") or "",
        "budget": parsed.get("budget") or {"range": data.get("budget_range") or ""},
        "duration": parsed.get("duration") or data.get("timeline") or "",
        "description": parsed.get("description") or data.get("project_description") or "",
        "objectives": parsed.get("objectives", []),
        "project_scope": parsed.get("project_scope", ""),
        "timeline": parsed.get("timeline", {}),
        "budget_breakdown": parsed.get("budget_breakdown", {}),
        "risks_and_mitigation": parsed.get("risks_and_mitigation", []),
        "team_structure": parsed.get("team_structure", {}),
        "resources_required": parsed.get("resources_required", {"skills": [], "tools_and_technologies": []}),
        "success_criteria": parsed.get("success_criteria", []),
        "assumptions": parsed.get("assumptions", []),
        "complexity_score": total_score,
        "complexity": parsed.get("complexity") or scoring_info.get("complexity"),
        "recommendation": parsed.get("recommendation") or scoring_info.get("recommendation"),
        "rationale": parsed.get("rationale") or scoring_info.get("rationale"),
        "recommended_pm_count": parsed.get("recommended_pm_count") or scoring_info.get('recommended_pm_count'),
        "diagnostics": {
            "input_question_count": len(questions),
            "prompt_chars": len(prompt),
        },
    }

    return jsonify(response), 200
