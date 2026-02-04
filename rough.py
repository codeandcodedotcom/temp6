import uuid
import pytest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.generation import router
from app.models.pydantic_models import AskRequest


# -------------------------------------------------------------------
# Test app + client (correct FastAPI usage)
# -------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def valid_payload_dict():
    return {
        "user_id": str(uuid.UUID("550e8400-e29b-41d4-a716-446655440000")),
        "projectTitle": "Test Project",
        "projectCategory": "IT",
        "timeline": "1 year",
        "projectSponsor": "Sponsor",
        "projectDescription": "Description",
        "questions": [
            {
                "qid": "q1",
                "text": "Q1",
                "aid": "a1",
                "answer": "A1",
                "score": 10,
            }
        ],
        "totalScore": 10,
    }


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------

def test_ask_route_success(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.generation.get_llm_answer",
        lambda **_: {"timeline": {}, "objectives": []},
    )
    monkeypatch.setattr("app.api.generation.scoring", MagicMock())
    monkeypatch.setattr("app.api.generation.set_databricks_env", lambda: None)
    monkeypatch.setattr(
        "app.api.generation.get_project_search_tool",
        lambda *_, **__: lambda x: [],
    )
    monkeypatch.setattr("app.api.generation.get_par", lambda: "")
    monkeypatch.setattr("app.api.generation.get_pillm", lambda: "")
    monkeypatch.setattr(
        "app.api.generation.generate_charter_pdf",
        lambda *_, **__: "dummy.pdf",
    )
    monkeypatch.setattr(
        "app.api.generation.create_project",
        lambda **_: MagicMock(project_id="pid"),
    )
    monkeypatch.setattr("app.api.generation.create_answers", lambda **_: None)
    monkeypatch.setattr(
        "app.api.generation.create_charter",
        lambda **_: MagicMock(charter_id="cid"),
    )
    monkeypatch.setattr(
        "app.api.generation.create_charter_sections",
        lambda **_: None,
    )
    monkeypatch.setattr(
        "app.api.generation.create_charter_version",
        lambda **_: None,
    )

    with patch("app.api.generation.AsyncSession", return_value=MagicMock()):
        response = client.post(
            "/generation/ask",
            json=valid_payload_dict(),
        )

    assert response.status_code == 200
    body = response.json()
    assert "charter_pdf_url" in body


def test_ask_route_invalid_json(client):
    response = client.post(
        "/generation/ask",
        data="not a json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_ask_route_missing_questions(client):
    payload = valid_payload_dict()
    payload.pop("questions")

    response = client.post("/generation/ask", json=payload)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(err["loc"][-1] == "questions" for err in errors)


def test_ask_route_llm_timeout(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.generation.get_llm_answer",
        lambda **_: (_ for _ in ()).throw(Exception("LLM timeout")),
    )
    monkeypatch.setattr("app.api.generation.scoring", MagicMock())
    monkeypatch.setattr("app.api.generation.set_databricks_env", lambda: None)
    monkeypatch.setattr(
        "app.api.generation.get_project_search_tool",
        lambda *_, **__: lambda x: [],
    )
    monkeypatch.setattr("app.api.generation.get_par", lambda: "")
    monkeypatch.setattr("app.api.generation.get_pillm", lambda: "")
    monkeypatch.setattr(
        "app.api.generation.generate_charter_pdf",
        lambda *_, **__: "dummy.pdf",
    )
    monkeypatch.setattr(
        "app.api.generation.create_project",
        lambda **_: MagicMock(project_id="pid"),
    )
    monkeypatch.setattr("app.api.generation.create_answers", lambda **_: None)
    monkeypatch.setattr(
        "app.api.generation.create_charter",
        lambda **_: MagicMock(charter_id="cid"),
    )
    monkeypatch.setattr(
        "app.api.generation.create_charter_sections",
        lambda **_: None,
    )
    monkeypatch.setattr(
        "app.api.generation.create_charter_version",
        lambda **_: None,
    )

    with patch("app.api.generation.AsyncSession", return_value=MagicMock()):
        response = client.post(
            "/generation/ask",
            json=valid_payload_dict(),
        )

    assert response.status_code in (502, 504)
    assert "LLM" in response.json()["detail"]
