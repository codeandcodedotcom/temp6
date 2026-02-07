# tests/test_compute_total_score.py

import logging
from app.api.generation import _compute_total_score


def test_returns_defaults_when_input_not_list():
    total, budget, project_type, product_type = _compute_total_score(None)
    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_score_from_top_level_score_field():
    questions = [
        {"score": 3},
        {"score": 2},
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 5
    assert budget is None
    assert project_type is None
    assert product_type is None


def test_score_from_first_option_score():
    questions = [
        {
            "options": [
                {"score": 4},
                {"score": 10},
            ]
        }
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 4


def test_budget_extraction_from_question_text():
    questions = [
        {
            "text": "What is your expected budget?",
            "answer": "10000",
        }
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 0
    assert budget == "10000"


def test_project_type_extraction():
    questions = [
        {
            "text": "Can you specify your project type?",
            "answer": "Internal",
        }
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert project_type == "Internal"


def test_product_type_extraction():
    questions = [
        {
            "text": "Is your project product related?",
            "answer": "Yes",
        }
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert product_type == "Yes"


def test_mixed_questions_all_paths():
    questions = [
        {"score": 2},
        {
            "options": [
                {"score": 3}
            ]
        },
        {
            "text": "What is your expected budget?",
            "answer": "5000",
        },
        {
            "text": "Can you specify your project type?",
            "answer": "Client",
        },
        {
            "text": "Is your project product related?",
            "answer": "No",
        },
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 5
    assert budget == "5000"
    assert project_type == "Client"
    assert product_type == "No"


def test_invalid_question_does_not_crash(caplog):
    caplog.set_level(logging.WARNING)
    questions = [
        {"score": "invalid"},
        {"options": "wrong"},
    ]
    total, budget, project_type, product_type = _compute_total_score(questions)
    assert total == 0
    assert budget is None
    assert project_type is None
    assert product_type is None
    assert any("Could not parse question score" in r.message for r in caplog.records)
