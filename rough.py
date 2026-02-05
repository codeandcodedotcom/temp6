# tests/utils/test_lessons_learnt.py

import pytest
from unittest.mock import MagicMock, patch

import app.utils.lessons_learnt as lessons_learnt


# -----------------------------
# _is_transient tests
# -----------------------------

def test_is_transient_with_http_status():
    class FakeError(Exception):
        response = MagicMock(status_code=503)

    assert lessons_learnt._is_transient(FakeError()) is True


def test_is_transient_with_timeout_message():
    err = Exception("Request timeout occurred")
    assert lessons_learnt._is_transient(err) is True


def test_is_transient_false_for_non_transient():
    err = Exception("validation failed")
    assert lessons_learnt._is_transient(err) is False


# -----------------------------
# get_endpoint_ready tests
# -----------------------------

@patch("app.utils.lessons_learnt.VectorSearchClient")
def test_get_endpoint_ready_success(mock_client):
    mock_index = MagicMock()
    mock_client.return_value.get_index.return_value = mock_index

    lessons_learnt.get_endpoint_ready(
        endpoint_name="endpoint",
        index_name="index",
        timeout=10,
    )

    mock_client.return_value.wait_for_endpoint.assert_called_once()
    mock_index.wait_until_ready.assert_called_once()


@patch("app.utils.lessons_learnt.VectorSearchClient")
def test_get_endpoint_ready_failure(mock_client):
    mock_client.return_value.wait_for_endpoint.side_effect = Exception("boom")

    with pytest.raises(Exception):
        lessons_learnt.get_endpoint_ready("endpoint", "index")


# -----------------------------
# get_project_search_tool tests
# -----------------------------

@patch("app.utils.lessons_learnt.get_endpoint_ready")
@patch("app.utils.lessons_learnt.DatabricksVectorSearch")
def test_get_project_search_tool_success(mock_vs, mock_ready):
    tool = lessons_learnt.get_project_search_tool("index", "endpoint")

    mock_ready.assert_called_once()
    mock_vs.assert_called_once()
    assert tool is not None


@patch("app.utils.lessons_learnt.get_endpoint_ready")
@patch("app.utils.lessons_learnt.DatabricksVectorSearch")
def test_get_project_search_tool_failure(mock_vs, mock_ready):
    mock_vs.side_effect = Exception("init failed")

    with pytest.raises(Exception):
        lessons_learnt.get_project_search_tool("index", "endpoint")


# -----------------------------
# retrieve tests
# -----------------------------

def test_retrieve_success(monkeypatch):
    fake_store = MagicMock()
    fake_store.similarity_search_with_score.return_value = [("doc", 0.1)]

    monkeypatch.setattr(lessons_learnt, "vector_store", fake_store)

    result = lessons_learnt.retrieve("project description", top_k=1)

    assert result == [("doc", 0.1)]


def test_retrieve_retry_then_success(monkeypatch):
    fake_store = MagicMock()

    fake_store.similarity_search_with_score.side_effect = [
        Exception("timeout"),
        [("doc", 0.2)],
    ]

    monkeypatch.setattr(lessons_learnt, "vector_store", fake_store)

    result = lessons_learnt.retrieve("project description", top_k=1)

    assert result == [("doc", 0.2)]


def test_retrieve_fails_after_retries(monkeypatch):
    fake_store = MagicMock()
    fake_store.similarity_search_with_score.side_effect = Exception("timeout")

    monkeypatch.setattr(lessons_learnt, "vector_store", fake_store)

    with pytest.raises(Exception):
        lessons_learnt.retrieve("project description", top_k=1)
