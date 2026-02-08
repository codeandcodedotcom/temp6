import pytest
from app.api.generation import _compute_total_score


def test_empty_questions_no_frontend_score():
    total, budget, project_type, product_type = _compute_total_score([], None)

    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_empty_questions_with_frontend_score_fallback():
    total, budget, project_type, product_type = _compute_total_score([], 42)

    assert total == 42
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_backend_score_zero_triggers_frontend_fallback():
    questions = [
        {"text": "Can you specify your project type?", "answer": "External"},
        {"text": "Is your project product related?", "answer": "Yes"},
    ]

    total, budget, project_type, product_type = _compute_total_score(
        questions,
        frontend_total_score=55,
    )

    assert total == 55
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_backend_score_non_zero_does_not_use_frontend_score():
    questions = [
        {"score": 10},
        {"score": 5},
    ]

    total, budget, project_type, product_type = _compute_total_score(
        questions,
        frontend_total_score=99,
    )

    assert total == 15
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_frontend_score_ignored_if_not_number():
    questions = []

    total, budget, project_type, product_type = _compute_total_score(
        questions,
        frontend_total_score="42",  # invalid type
    )

    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_mixed_questions_backend_zero_uses_frontend():
    questions = [
        {"score": 0},
        {"options": [{"score": 0}]},
        {"text": "What is your expected budget?", "answer": "5000"},
    ]

    total, budget, project_type, product_type = _compute_total_score(
        questions,
        frontend_total_score=30,
    )

    assert total == 30
    assert budget is None
    assert project_type is None
    assert product_type is None
