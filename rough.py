def _compute_total_score(questions: list[Dict[str, Any]]):
    """Compute total score from frontend questions."""
    total = 0
    metadata = {'budget': None, 'project_type': None, 'product_type': None}
    
    if not isinstance(questions, list):
        return 0, metadata['budget'], metadata['project_type'], metadata['product_type']
    
    for q in questions:
        try:
            if not isinstance(q, dict):
                continue
            
            total += _process_question(q, metadata)
            
        except Exception:
            logger.warning(
                "Could not parse question score, ignoring: %s",
                q,
                exc_info=False,
            )
    
    return int(total), metadata['budget'], metadata['project_type'], metadata['product_type']


def _process_question(q: dict, metadata: dict) -> int:
    """Process a single question and extract relevant data."""
    text = q.get("text")
    if not isinstance(text, str):
        return 0
    
    t = text.strip().lower()
    _extract_question_metadata(t, q, metadata)
    return _get_question_score(q)


def _extract_question_metadata(t: str, q: dict, metadata: dict):
    """Extract budget, project_type, and product_type from question."""
    if t.startswith("what is your expected budget"):
        metadata['budget'] = q.get("answer")
    elif t.startswith("can you specify your project type"):
        metadata['project_type'] = q.get("answer")
    elif t == "is your project product related?":
        metadata['product_type'] = q.get("answer")


def _get_question_score(q: dict) -> int:
    """Get score from question, checking both direct score and options."""
    if q.get("score") is not None:
        return int(q.get("score") or 0)
    
    opts = q.get("options") or []
    if isinstance(opts, list) and opts:
        first = opts[0]
        if isinstance(first, dict) and first.get("score") is not None:
            return int(first.get("score") or 0)
    
    return 0
