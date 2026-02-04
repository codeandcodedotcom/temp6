import uuid
from datetime import datetime
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
        "user_id": "550e8400-e29b-41d4-a716-446655440001",
        "projectTitle": "Test Project",
        "projectDescription": "Project description",
        "projectSponsor": "Sponsor name",
        "timeline": "Q1",
        "totalScore": 10,
        "questions": [
            {
                "qid": "q1",
                "text": "What is the goal of the project?",
                "aid": "550e8400-e29b-41d4-a716-446655440001",
                "answer": "Deliver MVP",
                "score": 10,
            }
        ],
    }


def mock_llm_answer(**_):
    return {
        "project_id": uuid.uuid4(),
        "charter_id": uuid.uuid4(),
        "created_at": datetime.utcnow(),
        "project_title": "Test Project",
        "description": "Test description",
        "industry": "IT",
        "duration": "6 months",
        "budget": "100k",
        "complexity_score": 10,
        "project_sponsor": "Sponsor",
        "managed_by": "LLM",
        "charter_pdf_url": "http://example.com/file.pdf",
        "context_used": "unit-test",

        "current_state": [],
        "objectives": [],
        "future_state": [],
        "high_level_requirement": [],
        "business_benefit": [],
        "dependencies": [],
        "lesson_learnt": [],
        "success_criteria": [],
        "assumptions": [],

        "project_scope": {},
        "budget_breakdown": {"allocation": {}},
        "timeline": {},

        "risks_and_mitigation": [],
        "pm_resource_recommendation": [],
    }


# -------------------------
# Tests
# -------------------------
def test_ask_route_success(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.generation.get_llm_answer",
        mock_llm_answer,
    )

    monkeypatch.setattr("app.api.generation.scoring", MagicMock())
    monkeypatch.setattr("app.api.generation.set_databricks_env", lambda: None)
    monkeypatch.setattr(
        "app.api.generation.get_project_search_tool",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr("app.api.generation.get_par", lambda: "")
    monkeypatch.setattr("app.api.generation.get_plim", lambda: "")
    monkeypatch.setattr(
        "app.api.generation.generate_charter_pdf",
        lambda *_: "file.pdf",
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

    with patch(
        "app.api.generation.AsyncSession",
        return_value=MagicMock(),
    ):
        response = client.post("/generation/ask", json=valid_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["managed_by"] == "LLM"
    assert "budget_breakdown" in body
    assert "allocation" in body["budget_breakdown"]


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
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr("app.api.generation.get_par", lambda: "")
    monkeypatch.setattr("app.api.generation.get_plim", lambda: "")

    with patch(
        "app.api.generation.AsyncSession",
        return_value=MagicMock(),
    ):
        response = client.post("/generation/ask", json=valid_payload())

    assert response.status_code in (502, 504)
