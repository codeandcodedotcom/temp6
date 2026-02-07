import pytest

from app.api.generation import _compute_total_score


def test_empty_questions():
    total, budget, project_type, product_type = _compute_total_score([])
    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_direct_score_field():
    questions = [
        {"score": 5},
        {"score": 3},
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 8
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_score_inside_options():
    questions = [
        {
            "options": [
                {"score": 4}
            ]
        }
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 4
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_budget_extraction():
    questions = [
        {
            "text": "What is your expected budget?",
            "answer": "10000"
        }
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 0
    assert budget == "10000"
    assert project_type is None
    assert product_type is None


def test_project_type_extraction():
    questions = [
        {
            "text": "Can you specify your project type?",
            "answer": "Internal"
        }
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 0
    assert budget is None
    assert project_type == "Internal"
    assert product_type is None


def test_product_type_extraction():
    questions = [
        {
            "text": "Is your project product related?",
            "answer": "Yes"
        }
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type == "Yes"


def test_mixed_questions():
    questions = [
        {"score": 2},
        {
            "options": [
                {"score": 3}
            ]
        },
        {
            "text": "What is your expected budget?",
            "answer": "5000"
        },
        {
            "text": "Can you specify your project type?",
            "answer": "External"
        },
        {
            "text": "Is your project product related?",
            "answer": "No"
        }
    ]

    total, budget, project_type, product_type = _compute_total_score(questions)

    assert total == 5
    assert budget == "5000"
    assert project_type == "External"
    assert product_type == "No"


def test_invalid_entries_are_ignored():
    questions = [
        "invalid",
        {"options": "wrong"},
        {"score": "not_a_number"},
    ]

    total, budget, project_type, product_type = _compute_total_score(questions)

    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None
