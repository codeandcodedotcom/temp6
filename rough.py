import pytest
from unittest.mock import MagicMock, patch

import app.utils.lessons_learnt as lessons_learnt


# ------------------------------------------------------------------
# _is_transient (PRIVATE FUNCTION — TEST DIRECTLY)
# ------------------------------------------------------------------

def test__is_transient_with_http_status():
    class FakeError(Exception):
        response = MagicMock(status_code=503)

    assert lessons_learnt._is_transient(FakeError()) is True


def test__is_transient_with_timeout_message():
    err = Exception("Request timeout occurred")
    assert lessons_learnt._is_transient(err) is True


def test__is_transient_false_for_non_transient():
    err = Exception("validation failed")
    assert lessons_learnt._is_transient(err) is False


# ------------------------------------------------------------------
# get_endpoint_ready
# ------------------------------------------------------------------

@patch("app.utils.lessons_learnt.VectorSearchClient")
def test_get_endpoint_ready_success(mock_client):
    mock_index = MagicMock()
    mock_client.return_value.get_index.return_value = mock_index

    lessons_learnt.get_endpoint_ready(
        endpoint_name="endpoint",
        index_name="index",
        timeout=5,
    )

    mock_client.return_value.wait_for_endpoint.assert_called_once()
    mock_index.wait_until_ready.assert_called_once()


@patch("app.utils.lessons_learnt.VectorSearchClient")
def test_get_endpoint_ready_failure(mock_client):
    mock_client.return_value.wait_for_endpoint.side_effect = Exception("boom")

    with pytest.raises(Exception):
        lessons_learnt.get_endpoint_ready("endpoint", "index")


# ------------------------------------------------------------------
# get_project_search_tool + retrieve (CLOSURE-AWARE TESTING)
# ------------------------------------------------------------------

@patch("app.utils.lessons_learnt.get_endpoint_ready")
@patch("app.utils.lessons_learnt.DatabricksVectorSearch")
def test_retrieve_success(mock_vs, mock_ready):
    fake_store = MagicMock()
    fake_store.similarity_search_with_score.return_value = [("doc", 0.1)]
    mock_vs.return_value = fake_store

    retrieve = lessons_learnt.get_project_search_tool("index", "endpoint")
    result = retrieve("project description", top_k=1)

    assert result == [("doc", 0.1)]


@patch("app.utils.lessons_learnt.get_endpoint_ready")
@patch("app.utils.lessons_learnt.DatabricksVectorSearch")
def test_retrieve_retry_then_success(mock_vs, mock_ready):
    fake_store = MagicMock()
    fake_store.similarity_search_with_score.side_effect = [
        Exception("timeout"),
        [("doc", 0.2)],
    ]
    mock_vs.return_value = fake_store

    retrieve = lessons_learnt.get_project_search_tool("index", "endpoint")
    result = retrieve("project description", top_k=1)

    assert result == [("doc", 0.2)]


@patch("app.utils.lessons_learnt.get_endpoint_ready")
@patch("app.utils.lessons_learnt.DatabricksVectorSearch")
def test_retrieve_fails_after_retries(mock_vs, mock_ready):
    fake_store = MagicMock()
    fake_store.similarity_search_with_score.side_effect = Exception("timeout")
    mock_vs.return_value = fake_store

    retrieve = lessons_learnt.get_project_search_tool("index", "endpoint")

    with pytest.raises(Exception):
        retrieve("project description", top_k=1)
