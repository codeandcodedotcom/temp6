import json
from flask import Blueprint, request, jsonify, current_app
from app.services import azure_openai, databricks, prompt_builder, scoring
from app.config import Config
from app.utils.logger import get_logger
from datetime import datetime, timezone
import uuid

bp = Blueprint("generation", __name__)
logger = get_logger(__name__)

@bp.route("/ask", methods=["POST"])
def ask():
    """
    Orchestrates: user input -> embedding -> Databricks retrieval -> prompt -> Azure LLM -> response.
    Expects JSON payload matching frontend->backend contract.
    """

    data = request.json or {}
    submission_id = data.get("submission_id")

    project_id = submission_id or str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    questions = data.get("questions", [])
    if not isinstance(questions, list):
        return jsonify({"error": "Missing or invalid 'questions' field"}), 400

    # Compute total score
    total_score = 0
    for q in questions:
        if not isinstance(q, dict):
            continue
        try:
            total_score += int(q.get("score", 0))
        except Exception:
            logger.warning(f"Invalid score for question {q.get('id')}, treating as 0")

    # Interpret score
    scoring_info = scoring.interpret_score(total_score)
    scoring_summary = (
        f"Complexity: {scoring_info.get('complexity')}. "
        f"Recommendation: {scoring_info.get('recommendation')}"
        f"Rationale: {scoring_info.get('rationale')}"
        f"Recommended PM Count: {scoring_info.get('recommended_pm_count')}"
    )

    # Model tuning params
    top_k = int(getattr(Config, "TOP_K", 3))
    max_tokens = int(getattr(Config, "MAX_TOKENS", 500))
    temperature = float(getattr(Config, "TEMPERATURE", 0.3))

    logger.info(
        f"/ask start (questions={len(questions)}, total_score={total_score}, "
        f"top_k={top_k}, max_tokens={max_tokens}, temperature={temperature})"
    )

    # Build query text for embeddings
    parts = []

    title = (data.get("project_title") or "").strip()
    desc = (data.get("project_description") or "").strip()
    domain = (data.get("domain") or "").strip()
    budget_range = (data.get("budget_range") or "").strip()
    timeline = (data.get("timeline") or "").strip()
    project_description = (data.get("project_description") or "").strip()
    extra = (data.get("additional_context") or "").strip()

    if title:
        parts.append(f"Title: {title}")
    if desc:
        parts.append(f"Description: {desc}")
    if domain:
        parts.append(f"Domain: {domain}")
    if budget_range:
        parts.append(f"Budget Range: {budget_range}")
    if timeline:
        parts.append(f"Timeline: {timeline}")
    if extra:
        parts.append(f"Additional context: {extra}")

    user_id = data.get("user_id") or data.get("user") or ""
    if user_id:
        parts.append(f"User ID: {user_id}")

    # Questions and answers
    for q in questions:
        q_text = q.get("text") or ""
        ans = q.get("options")[0]["label"] or ""
        if q_text or ans:
            parts.append(f"Question: {q_text} Answer: {ans}")

    raw_query = "\n\n".join(parts).strip()

    # Avoid sending extremely long strings to the embedder; truncate if needed.
    MAX_EMBED_CHARS = int(getattr(Config, "EMBED_MAX_CHARS", 20000))
    if len(raw_query) > MAX_EMBED_CHARS:
        logger.info(f"Truncating query for embedding from {len(raw_query)} to {MAX_EMBED_CHARS} chars")
        raw_query = raw_query[:MAX_EMBED_CHARS]

    query_text = raw_query if raw_query else (title or desc or "")

    # Get embedding
    try:
        embedding = azure_openai.embed_text(query_text)
    except Exception:
        logger.exception("Embedding failed")
        return jsonify({"error": "Failed to compute embedding"}), 502

    # Retrieve context from Databricks
    try:
        docs = databricks.retrieve_context(embedding, top_k=top_k)
    except Exception:
        logger.exception("Databricks retrieval failed")
        docs = []

    # Build prompt
    prompt = prompt_builder.build_prompt(
        questions=questions,
        docs=docs,
        instructions="",
        scoring_summary=scoring_summary,
    )

    # Generate answer with Azure OpenAI
    try:
        llm_text = azure_openai.generate_answer(
            prompt=prompt, max_tokens=max_tokens, temperature=temperature
        )
    except Exception:
        logger.exception("LLM generation failed")
        return jsonify({"error": "LLM generation failed"}), 502

    # Try to parse JSON output
    parsed = {}
    try:
        parsed = json.loads(llm_text)
    except Exception:
        logger.warning("LLM output not valid JSON; returning raw text")
        parsed = {}

    # Build response payload
    resp = {
        "project_id": project_id or "",
        "created_at": created_at or "",
        "project_title": parsed.get("project_title", data.get("project_title", "Untitled Project")),
        "domain": parsed.get("domain", data.get("domain", "")),
        "project_description": parsed.get("project_description", ""),
        "objectives": parsed.get("objectives", []),
        "project_scope": parsed.get("project_scope", ""),
        "timeline": parsed.get("timeline", []),
        "budget": parsed.get("budget", {}),
        "risks": parsed.get("risks", []),
        "team": parsed.get("team", []),
        "success_criteria": parsed.get("success_criteria", []),
        "resources_required": parsed.get("resources_required", {}),
        "tools_and_technologies": parsed.get("tools_and_technologies", []),
        "complexity_score": total_score or 0,
        "recommendation": parsed.get("recommendation", scoring_info.get("recommendation")),
        "rationale": parsed.get("rationale", scoring_info.get("rationale", "")),
        "supporting_documents": docs,
        "diagnostics": {
            "submission_id": submission_id,
            "used_top_k": top_k,
        },
        "raw_llm_output": llm_text,
    }

    # Persist result
    try:
        from app.services.storage import save_result

        if submission_id:
            save_result(submission_id, resp)
    except Exception:
        current_app.logger.exception("Failed to persist result")

    # Return to frontend
    return jsonify(resp), 200
