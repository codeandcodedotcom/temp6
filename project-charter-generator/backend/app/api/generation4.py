import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import Blueprint, request, jsonify, Response

from app.config import Config
from app.utils.logger import get_logger
from app.services import azure_openai, prompt_builder, scoring

import html as html_lib

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
            if q.get("text") is not None and q.get("text") == "What is your expected budget?":
                budget = q.get("answer")
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
    return int(total), budget


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


def _render_html_from_response(resp: Dict[str, Any]) -> str:
    """
    Render a complete HTML document
    """
    esc = html_lib.escape

    # render a key/value pair
    def kv(label: str, value: Any) -> str:
        if value is None or (isinstance(value, (list, dict)) and not value):
            return f"<p><strong>{esc(label)}:</strong> <em>Not provided</em></p>"
        if isinstance(value, (list, dict)):
            return f"<p><strong>{esc(label)}:</strong></p>" + render_value(value)
        return f"<p><strong>{esc(label)}:</strong> {esc(str(value))}</p>"

    # Render lists and dicts recursively into HTML
    def render_value(value: Any) -> str:
        if value is None:
            return "<div><em>null</em></div>"
        if isinstance(value, dict):
            html = "<div class='dict-block'><dl>"
            for k, v in value.items():
                html += f"<dt><strong>{esc(str(k))}</strong></dt><dd>{render_value(v)}</dd>"
            html += "</dl></div>"
            return html
        if isinstance(value, list):
            if not value:
                return "<div><em>[]</em></div>"
            html = "<ul>"
            for itm in value:
                if isinstance(itm, (dict, list)):
                    html += f"<li>{render_value(itm)}</li>"
                else:
                    html += f"<li>{esc(str(itm))}</li>"
            html += "</ul>"
            return html

        # fallback primitive
        return esc(str(value))

    title = resp.get("project_name") or resp.get("project_title") or ""
    industry = resp.get("industry") or resp.get("domain") or ""
    budget = resp.get("budget")
    duration = resp.get("duration")
    complexity_score = resp.get("complexity_score") or resp.get("total_score")
    project_sponsor = resp.get("sponsor") or resp.get("project_sponsor") or ""
    # NEW: date support
    date = resp.get("date") or ""
    description = resp.get("description") or resp.get("project_description") or ""
    high_level_requirement = resp.get("high_level_requirement", [])
    objectives = resp.get("objectives", [])

    # NEW: narrative sections
    current_state = resp.get("current_state") or resp.get("current_state_problem") or []
    future_state = resp.get("future_state") or resp.get("future_state_aim") or []
    business_benefit = resp.get("business_benefit") or []

    project_scope = resp.get("project_scope", "")
    timeline = resp.get("timeline", {})
    budget_breakdown = resp.get("budget breakdown") or resp.get("budget_breakdown") or resp.get("budget") or {}
    project_manager = resp.get("project_manager") or {}
    success_criteria = resp.get("success_criteria") or {}
    assumptions = resp.get("assumptions") or {}
    risks = resp.get("risks_and_mitigation") or resp.get("risks") or []
    dependencies = resp.get("dependencies", [])

    # NEW: PM resource recommendation & lessons
    pm_reco = resp.get("pm_resource_recommendation") or ""
    lessons = resp.get("lesson_learnt") or []

    # Build HTML pieces
    # High-level requirements
    if high_level_requirement:
        high_level_html = "<ul>" + "".join(f"<li>{esc(str(h))}</li>" for h in high_level_requirement) + "</ul>"
    else:
        high_level_html = "<p><em>Not provided</em></p>"

    # Objectives
    if objectives:
        objectives_html = "<ul>" + "".join(f"<li>{esc(str(o))}</li>" for o in objectives) + "</ul>"
    else:
        objectives_html = "<p><em>Not provided</em></p>"

    # NEW: narrative sections (list or paragraph)
    def list_or_para(seq: Any) -> str:
        if isinstance(seq, list):
            if not seq:
                return "<p><em>Not provided</em></p>"
            return "<ul>" + "".join(f"<li>{esc(str(x))}</li>" for x in seq) + "</ul>"
        if not seq:
            return "<p><em>Not provided</em></p>"
        return f"<p>{esc(str(seq))}</p>"

    current_state_html = list_or_para(current_state)
    future_state_html = list_or_para(future_state)
    business_benefit_html = list_or_para(business_benefit)

    # Project Scope
    if isinstance(project_scope, dict) and project_scope:
        scope_text = project_scope.get("scope") or ""
        in_scope = project_scope.get("in_scope") or project_scope.get("inScope") or []
        out_scope = project_scope.get("out_scope") or project_scope.get("outScope") or []
        scope_html = f"{esc(scope_text)}"
        if in_scope:
            scope_html += "<h5>In scope:</h5><ul>" + "".join(f"<li>{esc(str(s))}</li>" for s in in_scope) + "</ul>"
        if out_scope:
            scope_html += "<h5>Out of scope:</h5><ul>" + "".join(f"<li>{esc(str(s))}</li>" for s in out_scope) + "</ul>"
    else:
        scope_html = esc(str(project_scope)) if project_scope else "<p><em>Not provided</em></p>"

    # Timeline (add Pre-requisites support)
    if isinstance(timeline, dict) and timeline:
        timeline_html = ""
        for phase_key, phase_val in timeline.items():
            timeline_html += f"<h4>{esc(str(phase_key)).replace('_', ' ').title()}</h4>"
            if isinstance(phase_val, dict):
                p_duration = phase_val.get("duration")
                p_tasks = phase_val.get("tasks", [])
                # NEW: pre-requisites
                p_prereq = phase_val.get("pre_requisites") or phase_val.get("prerequisites")
                if p_duration:
                    timeline_html += f"<p><strong>Duration:</strong> {esc(str(p_duration))}</p>"
                if p_prereq:
                    timeline_html += f"<p><strong>Pre-requisites:</strong> {esc(str(p_prereq))}</p>"
                if p_tasks:
                    timeline_html += "<p><strong>Tasks:</strong></p><ul>"
                    for t in p_tasks:
                        timeline_html += f"<li>{esc(str(t))}</li>"
                    timeline_html += "</ul>"
            else:
                timeline_html += f"<p>{render_value(phase_val)}</p>"
    else:
        timeline_html = "<p><em>Not provided</em></p>"

    # Budget breakdown
    if isinstance(budget_breakdown, dict) and budget_breakdown:
        allocation = budget_breakdown.get("allocation") or {}
        total_cost = budget_breakdown.get("total_cost") or budget_breakdown.get("total_estimated") or ""
        bb_html = f"<p><strong>Total cost:</strong> {esc(str(total_cost))}</p>"
        if allocation and isinstance(allocation, dict):
            bb_html += "<p><strong>Allocation:</strong></p><ul>"
            for k, v in allocation.items():
                bb_html += f"<li><strong>{esc(str(k))}:</strong> {esc(str(v))}</li>"
            bb_html += "</ul>"
    else:
        bb_html = "<p><em>Not provided</em></p>"

    # Risks
    if isinstance(risks, list) and risks:
        risks_html = "<ul>"
        for r in risks:
            if isinstance(r, dict):
                rr = esc(str(r.get("risk") or r.get("title") or "Risk"))
                impact = esc(str(r.get("impact") or ""))
                mit = esc(str(r.get("mitigation") or r.get("mitigation_plan") or ""))
                risks_html += f"<li><strong>{rr}</strong> - Impact: {impact}<br/>Mitigation: {mit}</li>"
            else:
                risks_html += f"<li>{esc(str(r))}</li>"
        risks_html += "</ul>"
    else:
        risks_html = "<p><em>Not provided</em></p>"

    # Project Manager / PM Resource Recommendation
    if pm_reco:
        pm_html = kv("PM / Resource Recommendation", pm_reco)
    else:
        if isinstance(project_manager, dict) and project_manager:
            pm_html = ""
            pm_count = project_manager.get("count")
            if pm_count is not None:
                pm_html += f"<p><strong>Project Manager(s):</strong> {esc(str(pm_count))}</p>"
            responsibilities = project_manager.get("responsibilities") or []
            if responsibilities:
                pm_html += "<p><strong>Responsibilities:</strong></p><ul>"
                for d in responsibilities:
                    pm_html += f"<li>{esc(str(d))}</li>"
                pm_html += "</ul>"
        else:
            pm_html = "<p><em>Not provided</em></p>"

    # Success criteria
    success_html = (
        "<ul>" + "".join(f"<li>{esc(str(s))}</li>" for s in success_criteria) + "</ul>"
        if success_criteria else "<p><em>Not provided</em></p>"
    )

    # Assumptions
    assumptions_html = (
        "<ul>" + "".join(f"<li>{esc(str(a))}</li>" for a in assumptions) + "</ul>"
        if assumptions else "<p><em>Not provided</em></p>"
    )

    # Dependencies
    dependencies_html = (
        "<ul>" + "".join(f"<li>{esc(str(d))}</li>" for d in dependencies) + "</ul>"
        if dependencies else "<p><em>Not provided</em></p>"
    )

    # Lessons (NEW)
    lessons_html = (
        "<ul>" + "".join(f"<li>{esc(str(l))}</li>" for l in lessons) + "</ul>"
        if lessons else "<p><em>Not provided</em></p>"
    )

    # Build the HTML document (meta line updated to include Sponsor and Date)
    html_doc = f"""<!doctype html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>{esc(title)} - Project Charter</title>
    <style>
        body{{font-family: Arial, sans-serif; margin:24px; color:#222}}
        .card{{border:1px solid #e0e0e0; padding:18px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.04)}}
        h1{{margin:0 0 8px 0}}
        h2{{margin-top:20px; color:#333}}
        h4{{margin:10px 0 6px 0}}
        .meta{{color:#555; margin-bottom:12px}}
        .section{{margin-top:12px}}
        ul{{margin:6px 0 6px 20px}}
        dl{{margin:6px 0 6px 0}}
        dt{{font-weight:bold}}
        dd{{margin-left:12px; margin-bottom:8px}}
        small{{font-size:0.9em; color:#666}}
    </style>
    </head>
    <body>
    <div class="card">
        <h1>{esc(title)}</h1>
        <div class="meta">{esc(description)}</div>

        <div class="section">
            <strong>Industry:</strong> {esc(industry)} &nbsp; | 
            &nbsp; <strong>Duration:</strong> {esc(str(duration) if duration else "")} &nbsp; |
            &nbsp; <strong>Budget:</strong> {esc(str(budget) if budget else "Not provided")} &nbsp; |
            &nbsp; <strong>Complexity Score:</strong> {esc(str(complexity_score) if complexity_score is not None else "null")} &nbsp; |
            &nbsp; <strong>Project Sponsor:</strong> {esc(project_sponsor)} &nbsp; |
            &nbsp; <strong>Date:</strong> {esc(date)}
        </div>

        <!-- NEW narrative sections per structure -->
        <h2>Current State / Problem</h2>
        <div class="section">{current_state_html}</div>

        <h2>Objectives</h2>
        <div class="section">{objectives_html}</div>

        <h2>Future State / Aim</h2>
        <div class="section">{future_state_html}</div>

        <h2>High-level Requirement</h2>
        <div class="section">{high_level_html}</div>

        <h2>Business Benefit</h2>
        <div class="section">{business_benefit_html}</div>

        <h2>Project Scope</h2>
        <div class="section">{scope_html}</div>

        <h2>Budget Breakdown</h2>
        <div class="section">{bb_html}</div>

        <h2>Timeline</h2>
        <div class="section">{timeline_html}</div>

        <h2>Success Criteria</h2>
        <div class="section">{success_html}</div>

        <h2>Assumptions</h2>
        <div class="section">{assumptions_html}</div>

        <h2>Dependencies</h2>
        <div class="section">{dependencies_html}</div>

        <h2>Risks & Mitigation</h2>
        <div class="section">{risks_html}</div>

        <h2>PM / Resource Recommendation</h2>
        <div class="section">{pm_html}</div>

        <h2>Lesson Learnt</h2>
        <div class="section">{lessons_html}</div>

        <div class="small" style="margin-top:18px">
            Generated at: {esc(str(resp.get("created_at") or ""))} |
            Project ID: {esc(str(resp.get("project_id") or ""))}
        </div>

    </div>
    </body>
    </html>
    """
    return html_doc


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
    total_score, budget = _compute_total_score(questions)
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
    try:
        logger.info("Converting raw llm text to json.")
        parsed = json.loads(llm_text)
    except Exception:
        logger.info("Parsing llm text.")
        parsed = _try_parse_json_from_text(llm_text) or {}

    logger.info(f"Raw LLM response:\n{llm_text}")
    logger.info(f"Parsed LLM response:\n{parsed}")

    # build response using parsed values where available, else fallback to input/defaults
    response = {
        "project_id": project_id,
        "created_at": created_at,
        "project_title": parsed.get("project_title") or data.get("projectTitle") or "",
        "industry": parsed.get("industry") or data.get("projectCategory") or "",
        "budget": parsed.get("budget") or budget or "",
        "duration": parsed.get("duration") or data.get("timeline") or "",
        "sponsor": parsed.get("project_sponsor") or data.get("projectSponsor") or "",
        # NEW: date passthrough
        "date": parsed.get("date") or data.get("date") or datetime.now(timezone.utc).date().isoformat(),
        "description": parsed.get("description") or data.get("projectDescription") or "",
        "high_level_requirement": parsed.get("high_level_requirement", []),
        "objectives": parsed.get("objectives", []),

        # NEW: narratives
        "current_state": parsed.get("current_state") or parsed.get("current_state_problem") or [],
        "future_state": parsed.get("future_state") or parsed.get("future_state_aim") or [],
        "business_benefit": parsed.get("business_benefit") or [],

        "project_scope": parsed.get("project_scope", {}),
        "timeline": parsed.get("timeline", {}),
        "budget_breakdown": parsed.get("budget_breakdown") or parsed.get("budget breakdown") or {},
        "project_manager": parsed.get("project_manager", {}),

        "success_criteria": parsed.get("success_criteria", []),
        "assumptions": parsed.get("assumptions", []),

        # keep Dependencies and move before Risks in HTML
        "dependencies": parsed.get("dependencies", []),

        "risks_and_mitigation": parsed.get("risks_and_mitigation", []),

        # NEW: PM recommendation & lessons passthrough
        "pm_resource_recommendation": parsed.get("pm_resource_recommendation") or "",
        "lesson_learnt": parsed.get("lesson_learnt", []),

        "complexity_score": total_score,
        "complexity": parsed.get("complexity") or scoring_info.get("complexity"),
        "recommendation": parsed.get("recommendation") or scoring_info.get("recommendation"),
        "rationale": parsed.get("rationale") or scoring_info.get("rationale"),
        "recommended_pm_count": parsed.get("recommended_pm_count") or scoring_info.get("recommended_pm_count"),
        "diagnostics": {
            "input_question_count": len(questions),
            "prompt_chars": len(prompt),
        },
    }

    fmt = request.args.get("format", "").lower()
    accept = request.headers.get("Accept", "")
    if fmt == "html" or "text/html" in accept:
        html = _render_html_from_response(response)
        logger.info(f"LLM response in HTML format:\n{html}")
        return Response(html, status=200, mimetype="text/html")

    # default: JSON
    return jsonify(response), 200
