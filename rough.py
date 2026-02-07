import pytest
from app.api.generation import _compute_total_score


def test_empty_questions():
    total, budget, project_type, product_type = _compute_total_score([])
    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_non_list_input():
    total, budget, project_type, product_type = _compute_total_score("invalid")
    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_direct_score_present():
    questions = [
        {"score": 5},
        {"score": 3},
    ]
    total, *_ = _compute_total_score(questions)
    assert total == 8


def test_score_as_string():
    questions = [
        {"score": "4"},
    ]
    total, *_ = _compute_total_score(questions)
    assert total == 4


def test_options_score_used_when_score_missing():
    questions = [
        {
            "options": [
                {"score": 6}
            ]
        }
    ]
    total, *_ = _compute_total_score(questions)
    assert total == 6


def test_invalid_question_structure_is_ignored():
    questions = [
        {"score": 5},
        "invalid",
        None,
        {"options": "wrong"},
    ]
    total, *_ = _compute_total_score(questions)
    assert total == 5


def test_budget_extraction():
    questions = [
        {
            "text": "What is your expected budget?",
            "answer": "10000"
        }
    ]
    _, budget, _, _ = _compute_total_score(questions)
    assert budget == "10000"


def test_project_type_extraction():
    questions = [
        {
            "text": "Can you specify your project type?",
            "answer": "Web App"
        }
    ]
    _, _, project_type, _ = _compute_total_score(questions)
    assert project_type == "Web App"


def test_product_type_extraction():
    questions = [
        {
            "text": "Is your project product related?",
            "answer": "Yes"
        }
    ]
    _, _, _, product_type = _compute_total_score(questions)
    assert product_type == "Yes"


def test_mixed_questions_all_paths():
    questions = [
        {"score": 2},
        {
            "options": [{"score": 3}]
        },
        {
            "text": "What is your expected budget?",
            "answer": "5000"
        },
        {
            "text": "Can you specify your project type?",
            "answer": "Mobile"
        },
        {
            "text": "Is your project product related?",
            "answer": "No"
        }
    ]

    total, budget, project_type, product_type = _compute_total_score(questions)

    assert total == 5
    assert budget == "5000"
    assert project_type == "Mobile"
    assert product_type == "No"
