def _compute_total_score(questions: List[Dict[str, Any]]):
    """
    Compute total score from frontend questions.
    """
    total = 0

    # ✅ REQUIRED DEFAULTS
    budget = None
    project_type = None
    product_type = None

    if not isinstance(questions, list):
        return 0, budget, project_type, product_type

    for q in questions:
        try:
            if not isinstance(q, dict):
                continue

            text = q.get("text")
            if isinstance(text, str):
                t = text.strip().lower()

                if t.startswith("what is your expected budget"):
                    budget = q.get("answer")

                elif t.startswith("can you specify your project type"):
                    project_type = q.get("answer")

                elif text == "Is your project Product related?":
                    product_type = q.get("answer")

            if q.get("score") is not None:
                total += int(q.get("score") or 0)
                continue

            opts = q.get("options") or []
            if isinstance(opts, list) and opts:
                first = opts[0]
                if isinstance(first, dict) and first.get("score") is not None:
                    total += int(first.get("score") or 0)

        except Exception:
            logger.warning(
                "Could not parse question score, ignoring: %s",
                q,
                exc_info=False,
            )

    return int(total), budget, project_type, product_type
