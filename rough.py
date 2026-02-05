import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI

from app.db.services import add_options_data as options_module
from app.db.services.add_options_data import router


# --------------------
# FastAPI test app
# --------------------
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# --------------------
# Helper: mock DB session
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


# =========================================================
# ADD PATH — option does NOT exist
# =========================================================
@pytest.mark.asyncio
def test_seed_questionnaire_options_add():
    mock_session = make_mock_session(existing_record=None)

    app.dependency_overrides[
        options_module.get_db_session
    ] = lambda: mock_session

    options = [{
        "option_id": 1,
        "question_id": 1,
        "option_key": "A",
        "option_text": "Option A",
        "option_score": 1,
        "order_index": 1
    }]

    response = client.post("/questionnaire/options/seed", json=options)

    assert response.status_code == 200
    assert response.json()["added"] == 1
    assert response.json()["updated"] == 0
    assert response.json()["total"] == 1

    app.dependency_overrides.clear()


# =========================================================
# UPDATE PATH — option already exists
# =========================================================
@pytest.mark.asyncio
def test_seed_questionnaire_options_update():
    existing_record = MagicMock()
    mock_session = make_mock_session(existing_record=existing_record)

    app.dependency_overrides[
        options_module.get_db_session
    ] = lambda: mock_session

    options = [{
        "option_id": 1,
        "question_id": 1,
        "option_key": "A",
        "option_text": "Updated Option A",
        "option_score": 2,
        "order_index": 1
    }]

    response = client.post("/questionnaire/options/seed", json=options)

    assert response.status_code == 200
    assert response.json()["added"] == 0
    assert response.json()["updated"] == 1
    assert response.json()["total"] == 1

    app.dependency_overrides.clear()


# =========================================================
# ERROR PATH — DB failure
# =========================================================
@pytest.mark.asyncio
def test_seed_questionnaire_options_error():
    mock_session = make_mock_session(raise_on_execute=True)

    app.dependency_overrides[
        options_module.get_db_session
    ] = lambda: mock_session

    options = [{
        "option_id": 1,
        "question_id": 1,
        "option_key": "A",
        "option_text": "Option A",
        "option_score": 1,
        "order_index": 1
    }]

    response = client.post("/questionnaire/options/seed", json=options)

    assert response.status_code == 500
    assert "Failed to seed options" in response.text

    app.dependency_overrides.clear()
