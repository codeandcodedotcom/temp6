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
    description = resp.get("description") or resp.get("project_description") or ""
    # new / changed fields
    project_sponsor = resp.get("project_sponsor") or resp.get("projectSponsor") or ""
    high_level_requirement = resp.get("high_level_requirement") or resp.get("high_level_requirements") or []
    objectives = resp.get("objectives", [])
    project_scope = resp.get("project_scope", "")
    timeline = resp.get("timeline", {})
    budget_breakdown = resp.get("budget breakdown") or resp.get("budget_breakdown") or resp.get("budget") or {}
    risks = resp.get("risks_and_mitigation") or resp.get("risks") or []
    project_manager = resp.get("project_manager") or resp.get("projectManager") or {}
    success_criteria = resp.get("success_criteria") or []
    assumptions = resp.get("assumptions") or []
    dependencies = resp.get("dependencies") or []

    # Build HTML pieces
    # High-level requirements (compact bullet list)
    if high_level_requirement:
        high_level_html = "<ul>" + "".join(f"<li>{esc(str(h))}</li>" for h in high_level_requirement) + "</ul>"
    else:
        high_level_html = "<p><em>Not provided</em></p>"

    # Objectives
    if objectives:
        objectives_html = "<ul>" + "".join(f"<li>{esc(str(o))}</li>" for o in objectives) + "</ul>"
    else:
        objectives_html = "<p><em>Not provided</em></p>"

    # Project Scope (object with scope, in_scope, out_scope)
    if isinstance(project_scope, dict) and project_scope:
        scope_text = project_scope.get("scope") or ""
        in_scope = project_scope.get("in_scope") or project_scope.get("inScope") or []
        out_scope = project_scope.get("out_scope") or project_scope.get("outScope") or []
        scope_html = f"{esc(scope_text)}"
        if in_scope:
            scope_html += "<p><strong>In scope:</strong></p><ul>" + "".join(f"<li>{esc(str(s))}</li>" for s in in_scope) + "</ul>"
        if out_scope:
            scope_html += "<p><strong>Out of scope:</strong></p><ul>" + "".join(f"<li>{esc(str(s))}</li>" for s in out_scope) + "</ul>"
    else:
        scope_html = esc(str(project_scope)) if project_scope else "<p><em>Not provided</em></p>"

    # Timeline (unchanged logic)
    if isinstance(timeline, dict) and timeline:
        timeline_html = ""
        for phase_key, phase_val in timeline.items():
            timeline_html += f"<h4>{esc(str(phase_key)).replace('_',' ').title()}</h4>"
            if isinstance(phase_val, dict):
                p_duration = phase_val.get("duration")
                p_tasks = phase_val.get("tasks", [])
                if p_duration:
                    timeline_html += f"<p><strong>Duration:</strong> {esc(str(p_duration))}</p>"
                if p_tasks:
                    timeline_html += "<p><strong>Tasks:</strong></p><ul>"
                    for t in p_tasks:
                        timeline_html += f"<li>{esc(str(t))}</li>"
                    timeline_html += "</ul>"
            else:
                timeline_html += f"<p>{render_value(phase_val)}</p>"
    else:
        timeline_html = "<p><em>Not provided</em></p>"

    # Budget breakdown (unchanged)
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

    # Risks & Mitigation (rendered below together with assumptions and dependencies)
    if isinstance(risks, list) and risks:
        risks_html = "<ul>"
        for r in risks:
            if isinstance(r, dict):
                rr = esc(str(r.get("risk") or r.get("title") or "Risk"))
                impact = esc(str(r.get("impact") or ""))
                mit = esc(str(r.get("mitigation") or r.get("mitigation_plan") or ""))
                risks_html += f"<li><strong>{rr}</strong> — Impact: {impact}<br/>Mitigation: {mit}</li>"
            else:
                risks_html += f"<li>{esc(str(r))}</li>"
        risks_html += "</ul>"
    else:
        risks_html = "<p><em>Not provided</em></p>"

    # Project Manager (replaces team structure)
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
    success_html = "<ul>" + "".join(f"<li>{esc(str(s))}</li>" for s in success_criteria) + "</ul>" if success_criteria else "<p><em>Not provided</em></p>"

    # Assumptions
    assumptions_html = "<ul>" + "".join(f"<li>{esc(str(a))}</li>" for a in assumptions) + "</ul>" if assumptions else "<p><em>Not provided</em></p>"

    # Dependencies
    dependencies_html = "<ul>" + "".join(f"<li>{esc(str(d))}</li>" for d in dependencies) + "</ul>" if dependencies else "<p><em>Not provided</em></p>"

    # Build the HTML document
    html_doc = f"""<!doctype html>
        <html>
        <head>
        <meta charset="utf-8" />
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
            .small{{font-size:0.9em; color:#666'}}
        </style>
        </head>
        <body>
        <div class="card">
            <h1>{esc(title)}</h1>
            <div class="meta">{esc(description)}</div>

            <div class="section">
            <strong>Industry:</strong> {esc(industry)} &nbsp; | &nbsp; <strong>Duration:</strong> {esc(str(duration) if duration else "")} &nbsp; | &nbsp; <strong>Budget:</strong> {esc(str(budget) if budget else "Not provided")} &nbsp; | &nbsp; <strong>Complexity Score:</strong> {esc(str(complexity_score) if complexity_score is not None else "null")} &nbsp; | &nbsp; <strong>Project Sponsor:</strong> {esc(project_sponsor)}
            </div>

            <h2>High-level Requirements</h2>
            <div class="section">{high_level_html}</div>

            <h2>Objectives</h2>
            <div class="section">{objectives_html}</div>

            <h2>Project Scope</h2>
            <div class="section">{scope_html}</div>

            <h2>Timeline</h2>
            <div class="section">{timeline_html}</div>

            <h2>Budget Breakdown</h2>
            <div class="section">{bb_html}</div>

            <h2>Assumptions, Risks & Mitigation, and Dependencies</h2>
            <div class="section">
                <h4>Assumptions</h4>
                {assumptions_html}
                <h4>Risks & Mitigation</h4>
                {risks_html}
                <h4>Dependencies</h4>
                {dependencies_html}
            </div>

            <h2>Project Manager</h2>
            <div class="section">{pm_html}</div>

            <h2>Success Criteria</h2>
            <div class="section">{success_html}</div>

            <div class="section">
            <h2>Recommendation</h2>
            <div>{esc(str(resp.get("recommendation") or resp.get("recommendation", "") or ""))}</div>
            </div>

            <div class="small" style="margin-top:18px">Generated at: {esc(str(resp.get("created_at") or ""))} | Project ID: {esc(str(resp.get("project_id") or ""))}</div>
        </div>
        </body>
        </html>
        """
    return html_doc
