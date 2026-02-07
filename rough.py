import pytest
from app.api.generation import _compute_total_score


def test_direct_score_field():
    questions = [
        {"text": "score question", "score": 5}
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 5
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_score_inside_options():
    questions = [
        {
            "text": "options question",
            "options": [{"score": 4}]
        }
    ]
    total, _, _, _ = _compute_total_score(questions)
    assert total == 4


def test_budget_extraction():
    questions = [
        {
            "text": "What is your expected budget?",
            "answer": "10000"
        }
    ]
    total, budget, _, _ = _compute_total_score(questions)
    assert total == 0
    assert budget == "10000"


def test_project_type_extraction():
    questions = [
        {
            "text": "Can you specify your project type?",
            "answer": "Internal"
        }
    ]
    total, _, project_type, _ = _compute_total_score(questions)
    assert total == 0
    assert project_type == "Internal"


def test_product_type_extraction():
    questions = [
        {
            "text": "Is your project product related?",
            "answer": "Yes"
        }
    ]
    total, _, _, product_type = _compute_total_score(questions)
    assert total == 0
    assert product_type == "Yes"


def test_mixed_valid_questions_only():
    questions = [
        {"text": "score one", "score": 2},
        {"text": "options score", "options": [{"score": 3}]},
        {"text": "What is your expected budget?", "answer": "5000"},
    ]
    total, budget, _, _ = _compute_total_score(questions)
    assert total == 5
    assert budget == "5000"


def test_invalid_questions_are_ignored():
    questions = [
        {"score": 5},
        {"options": "wrong"},
        None,
        "invalid"
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None
