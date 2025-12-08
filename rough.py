def _sanitize_string(value: str) -> str:
    # Convert to Windows-1252, replacing unsupported chars with '?'
    return value.encode("cp1252", errors="replace").decode("cp1252")


def _sanitize_for_db(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _sanitize_for_db(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_db(v) for v in obj]
    if isinstance(obj, str):
        return _sanitize_string(obj)
    return obj
