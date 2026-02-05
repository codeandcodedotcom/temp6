@pytest.mark.asyncio
def test_seed_questionnaire_add(monkeypatch):
    mock_session = MagicMock()

    # Simulate "no existing record" → add
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    monkeypatch.setattr(
        questionnaire_module,
        "get_db_session",
        lambda: mock_session
    )

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


@pytest.mark.asyncio
def test_seed_questionnaire_error(monkeypatch):
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(side_effect=Exception("db error"))
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    monkeypatch.setattr(
        questionnaire_module,
        "get_db_session",
        lambda: mock_session
    )

    questions = [{
        "question_id": 1,
        "question_text": "What is your name?",
        "question_type": "text",
        "order_index": 1
    }]

    response = client.post("/questionnaire/seed", json=questions)

    assert response.status_code == 500
    assert "Failed to seed questionnaire" in response.text
