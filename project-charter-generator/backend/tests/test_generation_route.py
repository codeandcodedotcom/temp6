import json
import pytest
from unittest.mock import patch, MagicMock
from app import create_app


@pytest.fixture
def client():
    """
    Flask test client fixture.
    """
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@patch("app.api.generation.azure_openai")
@patch("app.api.generation.databricks")
@patch("app.api.generation.prompt_builder")
def test_ask_orchestration(mock_prompt, mock_databricks, mock_azure, client):
    """
    Integration-style unit test for /api/generation/ask that mocks external services.
    It verifies the orchestration wiring and JSON response shape.
    """
    # Configure mocks to return predictable values
    mock_azure.embed_text.return_value = [0.1, 0.2, 0.3]

    mock_databricks.retrieve_context.return_value = [
        {"id": "d1", "content": "Document one"},
        {"id": "d2", "content": "Document two"},
    ]

    mock_prompt.build_prompt.return_value = "BUILT_PROMPT_TEXT"

    mock_azure.generate_answer.return_value = "LLM GENERATED ANSWER"

    response = client.post(
        "/api/generation/ask",
        data=json.dumps({"query": "Summarize X"}),
        content_type="application/json"
    )

    assert response.status_code == 200, f"unexpected status: {response.status_code} body: {response.data}"
    body = response.get_json()
    assert "answer" in body
    assert body["answer"] == "LLM GENERATED ANSWER"
    assert body["docs_count"] == 2
    assert body["used_top_k"]

    # Verify mocks were called with expected inputs
    mock_azure.embed_text.assert_called_once_with("Summarize X")
    mock_databricks.retrieve_context.assert_called_once()
    mock_prompt.build_prompt.assert_called_once()
    mock_azure.generate_answer.assert_called_once()
