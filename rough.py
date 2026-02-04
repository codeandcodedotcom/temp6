def _try_parse_json_from_text(text: Any) -> Optional[Dict[str, Any]]:
    """
    Try to extract the first JSON object from text and parse it.
    Returns dict if parse succeeds, else None.
    """

    # ✅ FIX 1: already parsed JSON
    if isinstance(text, dict):
        return text

    # ✅ FIX 2: reject non-string early
    if not isinstance(text, str) or not text:
        return None

    # crude extraction: first {...} block
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
