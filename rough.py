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


def test_direct_score_is_ignored_due_to_exception():
    questions = [
        {"score": 5}
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_score_inside_options_is_ignored():
    questions = [
        {"options": [{"score": 4}]}
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_budget_question_does_not_extract_budget():
    questions = [
        {
            "text": "What is your expected budget?",
            "answer": "10000"
        }
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_project_type_not_extracted():
    questions = [
        {
            "text": "Can you specify your project type?",
            "answer": "Internal"
        }
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_product_type_not_extracted():
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
    assert product_type is None


def test_mixed_questions_all_ignored():
    questions = [
        {"score": 2},
        {"options": [{"score": 3}]},
        {"text": "What is your expected budget?", "answer": "5000"},
        {"text": "Can you specify your project type?", "answer": "External"},
        {"text": "Is your project product related?", "answer": "No"},
    ]

    total, budget, project_type, product_type = _compute_total_score(questions)

    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None
