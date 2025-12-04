from typing import Any, Dict, List

def get_pm_profiles_for_score(total_score: int, project_type: str) -> List[Dict[str, Any]]:
    """
    Based on total_score and project_type (Q3 answer), return a list of
    job-profile dicts for the PM / Resource Recommendation section.

    - 1–27  -> no roles
    - 28–39 -> Project Lead (or IT Project Lead for IT Program Management)
    - 40–51 -> Project Manager
    - 52–60 -> multiple roles, dependent on project_type
    """
    role_names: List[str] = []

    # ---- Find matching score band ----
    for band in _PM_BANDS:
        try:
            min_s = int(band.get("min_score", 0))
            max_s = int(band.get("max_score", 0))
        except Exception:
            continue

        if min_s <= total_score <= max_s:
            roles_spec = band.get("roles")

            # Case 1: old style: simple list of roles
            if isinstance(roles_spec, list):
                role_names = roles_spec or []

            # Case 2: new style: dict keyed by project_type / 'default'
            elif isinstance(roles_spec, dict):
                # exact match on project_type (Q3 answer, e.g. "IT Program Management")
                if project_type in roles_spec:
                    role_names = roles_spec[project_type] or []
                # fall back to 'default' if present (e.g. 28–39 band -> Project Lead)
                elif "default" in roles_spec:
                    role_names = roles_spec["default"] or []
                else:
                    # last-resort: flatten all role lists
                    all_roles = set()
                    for vals in roles_spec.values():
                        all_roles.update(vals or [])
                    role_names = list(all_roles)

            else:
                role_names = []

            break
    else:
        # no band matched
        return []

    # self-managed / no-role case
    if not role_names:
        return []

    # ---- Map role names to full job_profile blocks ----
    results: List[Dict[str, Any]] = []
    for rn in role_names:
        for prof in _JOB_PROFILES:
            if prof.get("job_profile") == rn:
                results.append(prof)
                break  # stop after first match

    return results
