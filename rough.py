def __compute_total_score(questions: List[Dict[str, Any]]):
    """
    Compute total score from frontend questions.
    """
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

    return int(total), budget, project_type, product_type


def _process_question(q, budget, project_type, product_type):
    if not isinstance(q, dict):
        return 0, budget, project_type, product_type

    try:
        _extract_metadata(q, lambda b: locals().update(b))
        score = _extract_score(q)
        budget, project_type, product_type = _extract_text_answers(
            q, budget, project_type, product_type
        )
        return score, budget, project_type, product_type

    except Exception:
        logger.warning(
            "Could not parse question score, ignoring: %s",
            q,
            exc_info=False,
        )
        return 0, budget, project_type, product_type


def _extract_score(q: dict) -> int:
    if q.get("score") is not None:
        return int(q.get("score") or 0)

    opts = q.get("options") or []
    if isinstance(opts, list) and opts:
        first = opts[0]
        if isinstance(first, dict) and first.get("score") is not None:
            return int(first.get("score") or 0)

    return 0


def _extract_text_answers(q, budget, project_type, product_type):
    text = q.get("text")
    if not isinstance(text, str):
        return budget, project_type, product_type

    t = text.strip().lower()
    answer = q.get("answer")

    if t.startswith("what is your expected budget"):
        budget = answer
    elif t.startswith("can you specify your project type"):
        project_type = answer
    elif t == "is your project timeline flexible?":
        product_type = answer

    return budget, project_type, product_type
