import pytest

from app.api.generation import _compute_total_score, _get_managed_by


# -----------------------------
# Tests for _compute_total_score
# -----------------------------

def test_compute_total_score_with_direct_scores():
    questions = [
        {"text": "Q1", "score": 10},
        {"text": "Q2", "score": 5},
    ]

    total, budget, project_type, product_type = _compute_total_score(questions)

    assert total == 15
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_compute_total_score_with_options_score():
    questions = [
        {
            "text": "Q1",
            "options": [{"label": "opt1", "score": 7}],
        }
    ]

    total, _, _, _ = _compute_total_score(questions)

    assert total == 7


def test_compute_total_score_extracts_budget_and_project_type():
    questions = [
        {
            "text": "What is your expected budget?",
            "answer": "Between 2-10 million",
            "score": 10,
        },
        {
            "text": "Can you specify your project type?",
            "answer": "Civil",
            "score": 5,
        },
    ]

    total, budget, project_type, product_type = _compute_total_score(questions)

    assert total == 15
    assert budget == "Between 2-10 million"
    assert project_type == "Civil"
    assert product_type is None


def test_compute_total_score_extracts_product_type():
    questions = [
        {
            "text": "Is your project Product related?",
            "answer": "Yes",
            "score": 3,
        }
    ]

    total, _, _, product_type = _compute_total_score(questions)

    assert total == 3
    assert product_type == "Yes"


def test_compute_total_score_ignores_invalid_question_objects():
    questions = [
        "not a dict",
        123,
        {"text": "Q1", "score": 5},
    ]

    total, _, _, _ = _compute_total_score(questions)

    assert total == 5


def test_compute_total_score_invalid_input_returns_zero():
    total, budget, project_type, product_type = _compute_total_score("invalid")

    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None


# -----------------------------
# Tests for _get_managed_by
# -----------------------------

def test_get_managed_by_team_of_pm_professionals_by_score():
    assert _get_managed_by(52, []) == "Team of PM professionals"
    assert _get_managed_by(70, []) == "Team of PM professionals"


def test_get_managed_by_uses_pm_profile_if_present():
    pm_profiles = [
        {"job_profile": "Senior Project Lead"}
    ]

    result = _get_managed_by(30, pm_profiles)

    assert result == "Senior Project Lead"


def test_get_managed_by_fallback_self_managed():
    assert _get_managed_by(20, []) == "Self managed"


def test_get_managed_by_project_lead():
    assert _get_managed_by(35, []) == "Project Lead"


def test_get_managed_by_project_manager():
    assert _get_managed_by(45, []) == "Project Manager"


def test_get_managed_by_pm_profiles_malformed():
    pm_profiles = [{}]  # no job_profile key

    result = _get_managed_by(30, pm_profiles)

    assert result == "Project Lead"
