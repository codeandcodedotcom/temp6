import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.generation import router


# -------------------------
# Test client fixture
# -------------------------
@pytest.fixture()
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# -------------------------
# Helpers
# -------------------------
def valid_payload():
    return {
        "user_id": str(uuid.uuid4()),
        "projectTitle": "Test Project",
        "projectCategory": "Category",
        "timeline": "Q1",
        "projectSponsor": "Sponsor",
        "projectDescription": "Description",
        "totalScore": 10,
        "questions": [
            {
                "qid": "q1",
                "text": "Question?",
                "aid": "a1",
                "answer": "Answer",
                "score": 10,
            }
        ],
    }


# -------------------------
# Tests
# -------------------------
def test_ask_route_success(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.generation.get_llm_answer",
        lambda **_: {"timeline": {}, "objectives": []},
    )
    monkeypatch.setattr("app.api.generation.scoring", MagicMock())
    monkeypatch.setattr("app.api.generation.set_databricks_env", lambda: None)
    monkeypatch.setattr(
        "app.api.generation.get_project_search_tool",
        lambda *_ , **__: lambda _: [],
    )
    monkeypatch.setattr("app.api.generation.get_par", lambda: "")
    monkeypatch.setattr("app.api.generation.get_pilm", lambda: "")
    monkeypatch.setattr("app.api.generation.generate_charter_pdf", lambda *_: "file.pdf")
    monkeypatch.setattr(
        "app.api.generation.create_project",
        lambda **_: MagicMock(project_id="pid"),
    )
    monkeypatch.setattr("app.api.generation.create_answers", lambda **_: None)
    monkeypatch.setattr(
        "app.api.generation.create_charter",
        lambda **_: MagicMock(charter_id="cid"),
    )
    monkeypatch.setattr("app.api.generation.create_charter_sections", lambda **_: None)
    monkeypatch.setattr("app.api.generation.create_charter_version", lambda **_: None)

    with patch("app.api.generation.AsyncSession", return_value=MagicMock()):
        response = client.post("/generation/ask", json=valid_payload())

    assert response.status_code == 200


def test_ask_route_missing_questions(client):
    payload = valid_payload()
    payload.pop("questions")

    response = client.post("/generation/ask", json=payload)

    assert response.status_code == 422


def test_ask_route_llm_timeout(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.generation.get_llm_answer",
        lambda **_: (_ for _ in ()).throw(Exception("LLM timeout")),
    )
    monkeypatch.setattr("app.api.generation.scoring", MagicMock())
    monkeypatch.setattr("app.api.generation.set_databricks_env", lambda: None)
    monkeypatch.setattr(
        "app.api.generation.get_project_search_tool",
        lambda *_ , **__: lambda _: [],
    )
    monkeypatch.setattr("app.api.generation.get_par", lambda: "")
    monkeypatch.setattr("app.api.generation.get_pilm", lambda: "")

    with patch("app.api.generation.AsyncSession", return_value=MagicMock()):
        response = client.post("/generation/ask", json=valid_payload())

    assert response.status_code in (502, 504)
