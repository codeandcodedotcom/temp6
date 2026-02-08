def _compute_total_score(
    questions: list[dict[str, any]],
    frontend_total_score: int | None = None,
):
    if not isinstance(questions, list):
        return 0, None, None, None

    total = 0
    budget = None
    project_type = None
    product_type = None

    for q in questions:
        score, budget, project_type, product_type = _process_question(
            q, budget, project_type, product_type
        )
        total += score

    # FINAL FALLBACK: use frontend totalScore only if backend failed
    if (
        total <= 0
        and isinstance(frontend_total_score, (int, float))
        and frontend_total_score > 0
    ):
        logger.warning(
            "Backend score calculation failed. Falling back to frontend totalScore=%s",
            frontend_total_score,
        )
        total = int(frontend_total_score)

    return int(total), budget, project_type, product_type
