from typing import Dict
from app.utils.logger import get_logger

logger = get_logger(__name__)

def interpret_score(total_score: int) -> Dict[str, str]:
    """
    Interpret the total score from questionnaire responses.

    Args:
        total_score (int): Sum of all question scores.

    Returns:
        dict: {
            "complexity": str,
            "recommendation": str,
            "rationale": str,
            "recommended_pm_count": int
        }
    """
    try:
        score = int(total_score)
    except Exception as e:
        logger.exception(f"Invalid total_score provided: {total_score} ({e})")
        return {
            "complexity": "Invalid Score",
            "recommendation": "Score not interpretable.",
            "rationale": "Input could not be cast to int.",
            "recommended_pm_count": 0,
        }

    if score == 0:
        return {
            "complexity": "No Score",
            "recommendation": "No scoring data was provided.",
            "rationale": "All question scores were zero or missing.",
            "recommended_pm_count": 0,
        }
    elif 1 <= score <= 27:
        return {
            "complexity": "Low Complexity / Standard execution",
            "recommendation": (
                "At this stage, the project does not require the support of a dedicated "
                "Project Management (PM) professional. Please reach out to your division PMO "
                "for guidance, support, and training recommendations as needed."
            ),
            "rationale": "Score between 1-27 indicates low complexity.",
            "recommended_pm_count": 0,
        }
    elif 28 <= score <= 39:
        return {
            "complexity": "Medium Complexity / Focus on risk",
            "recommendation": (
                "Based on the assessment, this project could be assigned a Project Lead. "
                "A Project Lead could provide the necessary oversight and direction to ensure successful delivery."
            ),
            "rationale": "Score between 28-39 indicates medium complexity.",
            "recommended_pm_count": 0,
        }
    elif 40 <= score <= 51:
        return {
            "complexity": "High Complexity / Need active governance",
            "recommendation": (
                "The assessment indicates that this project should be managed by a Project Manager. "
                "Assigning a Project Manager will help ensure effective planning, execution, and control "
                "throughout the project lifecycle."
            ),
            "rationale": "Score between 40-51 indicates high complexity.",
            "recommended_pm_count": 1,
        }
    elif 52 <= score <= 60:
        return {
            "complexity": "Critical Complexity / Need active governance",
            "recommendation": (
                "The assessment suggests that this initiative is best classified as a Programme. "
                "It should be supported by a team of PM professionals, providing comprehensive programme "
                "management to coordinate multiple related projects and achieve strategic objectives."
            ),
            "rationale": "Score between 52-60 indicates critical complexity.",
            "recommended_pm_count": 2,
        }

    return {
        "complexity": "Invalid Score",
        "recommendation": "Score out of expected range.",
        "rationale": f"Score {score} is outside defined buckets.",
        "recommended_pm_count": 0,
    }
