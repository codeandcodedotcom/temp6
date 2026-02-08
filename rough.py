def _compute_total_score(questions: List[Dict[str, Any]]):

    if not isinstance(questions, list):
        return 0, None, None, None

    total = 0
    budget = None
    project_type = None
    product_type = None

    frontend_total_score = None

    for q in questions:
        # Capture frontend totalScore once if present
        if frontend_total_score is None and isinstance(q, dict):
            frontend_total_score = q.get("totalScore")

        score, budget, project_type, product_type = _process_question(
            q, budget, project_type, product_type
        )
        total += score

    # 🔥 FINAL FALLBACK LOGIC 🔥
    if (not total or total <= 0) and isinstance(frontend_total_score, (int, float)):
        logger.warning(
            "Backend score calculation failed. Falling back to frontend totalScore=%s",
            frontend_total_score
        )
        total = int(frontend_total_score)

    return int(total), budget, project_type, product_type
