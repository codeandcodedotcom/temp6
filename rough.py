from typing import List, Dict

def _get_managed_by(total_score: int, pm_profiles: List[Dict[str, Any]]) -> str:
    """
    Decide the 'managed_by' label for the project.

    - Bands (by total_score):
        1–27  -> Self managed
        28–39 -> Project Lead
        40–51 -> Project Manager
        52+   -> Team of PM professionals
    - For non-last bands, use the job_profile from pm_profiles if available.
    """

    # Last band: score >= 52  -> always "Team of PM professionals"
    if total_score >= 52:
        return "Team of PM professionals"

    # Other bands: try to use job_profile from pm_profiles[0]
    if pm_profiles:
        jp = (pm_profiles[0].get("job_profile") or "").strip()
        if jp:
            return jp

    # Fallback purely from score (in case pm_profiles is empty or malformed)
    if total_score <= 27:
        return "Self managed"
    elif total_score <= 39:
        return "Project Lead"
    elif total_score <= 51:
        return "Project Manager"
    else:
        return "Team of PM professionals"
