import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI

from app.db.services import add_questionnaire_data as questionnaire_module
from app.db.services.add_questionnaire_data import router


# --------------------
# FastAPI test app
# --------------------
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# --------------------
# Shared mock session
# --------------------
def make_mock_session(existing_record=None, raise_on_execute=False):
    session = MagicMock()

    if raise_on_execute:
        session.execute = AsyncMock(side_effect=Exception("db error"))
    else:
        result = MagicMock()
        result.scalar_one_or_none.return_value = existing_record
        session.execute = AsyncMock(return_value=result)

    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


# --------------------
# ADD path (no record exists)
# --------------------
@pytest.mark.asyncio
def test_seed_questionnaire_add(monkeypatch):
    mock_session = make_mock_session(existing_record=None)

    # Override DB dependency
    app.dependency_overrides[
        questionnaire_module.get_db_session
    ] = lambda: mock_session

    questions = [{
        "question_id": 1,
        "question_text": "What is your name?",
        "question_type": "text",
        "order_index": 1
    }]

    response = client.post("/questionnaire/seed", json=questions)

    assert response.status_code == 200
    assert response.json()["added"] == 1
    assert response.json()["updated"] == 0
    assert response.json()["total"] == 1

    app.dependency_overrides.clear()


# --------------------
# UPDATE path (record exists)
# --------------------
@pytest.mark.asyncio
def test_seed_questionnaire_update(monkeypatch):
    existing_record = MagicMock()
    mock_session = make_mock_session(existing_record=existing_record)

    app.dependency_overrides[
        questionnaire_module.get_db_session
    ] = lambda: mock_session

    questions = [{
        "question_id": 1,
        "question_text": "Updated text",
        "question_type": "text",
        "order_index": 1
    }]

    response = client.post("/questionnaire/seed", json=questions)

    assert response.status_code == 200
    assert response.json()["added"] == 0
    assert response.json()["updated"] == 1
    assert response.json()["total"] == 1

    app.dependency_overrides.clear()


# --------------------
# ERROR path (DB failure)
# --------------------
@pytest.mark.asyncio
def test_seed_questionnaire_error(monkeypatch):
    mock_session = make_mock_session(raise_on_execute=True)

    app.dependency_overrides[
        questionnaire_module.get_db_session
    ] = lambda: mock_session

    questions = [{
        "question_id": 1,
        "question_text": "What is your name?",
        "question_type": "text",
        "order_index": 1
    }]

    response = client.post("/questionnaire/seed", json=questions)

    assert response.status_code == 500
    assert "Failed to seed questionnaire" in response.text

    app.dependency_overrides.clear()
