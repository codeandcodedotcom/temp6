import pytest
from unittest.mock import patch, MagicMock

from app.services import azure_openai


# embed_text
@patch("app.services.azure_openai.client")
def test_embed_text_success(mock_client):
    """
    embed_text should return the embedding list when Azure client responds normally.
    """
    mock_resp = MagicMock()
    mock_resp.data = [MagicMock(embedding=[0.11, 0.22, 0.33])]
    mock_client.embeddings.create.return_value = mock_resp

    emb = azure_openai.embed_text("hello world")

    assert isinstance(emb, list)
    assert emb == [0.11, 0.22, 0.33]
    mock_client.embeddings.create.assert_called_once()


@patch("app.services.azure_openai.client")
def test_embed_text_raises_when_client_errors(mock_client):
    """
    If the Azure client raises, embed_text should propagate that exception.
    """
    mock_client.embeddings.create.side_effect = Exception("Azure failure")
    with pytest.raises(Exception):
        azure_openai.embed_text("will fail")
    mock_client.embeddings.create.assert_called_once()


@patch("app.services.azure_openai.client")
def test_embed_text_retries_on_transient_failure_then_succeeds(mock_client):
    """
    Simulate transient failure on first call and success on second; embed_text should succeed.
    This depends on the retry wrapper behavior (if present).
    """
    mock_resp = MagicMock()
    mock_resp.data = [MagicMock(embedding=[0.5, 0.6])]
    # First call raises, second returns response
    mock_client.embeddings.create.side_effect = [Exception("temp"), mock_resp]

    emb = azure_openai.embed_text("retry-case")
    assert emb == [0.5, 0.6]
    assert mock_client.embeddings.create.call_count == 2


# generate_answer
@patch("app.services.azure_openai.client")
def test_generate_answer_success(mock_client):
    """
    generate_answer should return the model's text when Azure chat returns a normal response.
    """
    # Arrange a fake response: response.choices[0].message.content
    fake_choice = MagicMock()
    fake_choice.message = MagicMock()
    fake_choice.message.content = "This is the model answer."
    fake_response = MagicMock()
    fake_response.choices = [fake_choice]
    mock_client.chat.completions.create.return_value = fake_response

    answer = azure_openai.generate_answer("hello prompt", max_tokens=10, temperature=0.1)

    assert isinstance(answer, str)
    assert "model answer" in answer.lower()
    mock_client.chat.completions.create.assert_called_once()


@patch("app.services.azure_openai.client")
def test_generate_answer_raises_on_error(mock_client):
    """
    If the chat completion call raises, the exception should bubble up.
    """
    mock_client.chat.completions.create.side_effect = Exception("chat failure")
    with pytest.raises(Exception):
        azure_openai.generate_answer("bad prompt")
    mock_client.chat.completions.create.assert_called_once()
