from app.api.generation import (
    _extract_score,
    _extract_text_answers,
    _process_question,
)


def test_extract_score_direct():
    q = {"score": 5}
    assert _extract_score(q) == 5


def test_extract_score_from_options():
    q = {"options": [{"score": 4}]}
    assert _extract_score(q) == 4


def test_extract_score_invalid():
    assert _extract_score({"options": ["bad"]}) == 0
    assert _extract_score({}) == 0


def test_extract_text_answers_budget():
    q = {
        "text": "What is your expected budget?",
        "answer": "10000",
    }
    budget, project, product = _extract_text_answers(q, None, None, None)
    assert budget == "10000"
    assert project is None
    assert product is None


def test_extract_text_answers_project_type():
    q = {
        "text": "Can you specify your project type?",
        "answer": "Internal",
    }
    budget, project, product = _extract_text_answers(q, None, None, None)
    assert project == "Internal"


def test_extract_text_answers_product_type():
    q = {
        "text": "Is your project product related?",
        "answer": "Yes",
    }
    budget, project, product = _extract_text_answers(q, None, None, None)
    assert product == "Yes"


def test_extract_text_answers_invalid_text():
    q = {"text": 123}
    budget, project, product = _extract_text_answers(q, "b", "p", "pr")
    assert budget == "b"
    assert project == "p"
    assert product == "pr"


def test_process_question_non_dict():
    score, budget, project, product = _process_question("bad", None, None, None)
    assert score == 0
    assert budget is None
    assert project is None
    assert product is None


def test_process_question_valid_score():
    q = {"score": 3}
    score, budget, project, product = _process_question(q, None, None, None)
    assert score == 3


def test_process_question_exception_path(monkeypatch):
    def boom(*args, **kwargs):
        raise Exception("fail")

    monkeypatch.setattr(
        "app.api.generation._extract_score", boom
    )

    q = {"score": 5}
    score, budget, project, product = _process_question(q, None, None, None)
    assert score == 0
