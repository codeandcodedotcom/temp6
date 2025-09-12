import pytest
from unittest.mock import patch, MagicMock
import requests

from app.services import databricks


# _post_with_retry (indirect tests via patching requests.post)
@patch("app.services.databricks.requests.post")
def test__post_with_retry_success(mock_post):
    """
    _post_with_retry should return parsed json when requests.post succeeds on first try.
    """
    fake_resp = MagicMock()
    fake_resp.raise_for_status.return_value = None
    fake_resp.json.return_value = {"ok": True}
    mock_post.return_value = fake_resp

    # call helper via run_job by giving a job id (it calls _post_with_retry internally)
    result = databricks._post_with_retry("https://example.com/api", headers={}, payload={"x": 1})
    assert result == {"ok": True}
    assert mock_post.call_count == 1


@patch("app.services.databricks.requests.post")
def test__post_with_retry_retries_on_timeout_then_succeeds(mock_post):
    """
    If the first request raises a Timeout, the helper should retry and succeed on the second attempt.
    """
    # First call: raise Timeout, second call: success
    mock_post.side_effect = [
        requests.Timeout("timeout"),
        MagicMock(**{"raise_for_status.return_value": None, "json.return_value": {"ok": "second"}})
    ]

    result = databricks._post_with_retry("https://example.com/api", headers={}, payload={"x": 1})
    assert result == {"ok": "second"}
    assert mock_post.call_count == 2


@patch("app.services.databricks.requests.post")
def test__post_with_retry_fails_on_4xx_and_does_not_retry(mock_post):
    """
    If the response is a 4xx error, the helper should raise and not keep retrying.
    """
    fake_resp = MagicMock()
    fake_resp.raise_for_status.side_effect = requests.HTTPError(response=MagicMock(status_code=401, text="unauth"))
    fake_resp.status_code = 401
    fake_resp.text = "unauth"
    mock_post.return_value = fake_resp

    with pytest.raises(Exception):
        databricks._post_with_retry("https://example.com/api", headers={}, payload={"x": 1})
    # Only one call because 4xx should fail fast
    assert mock_post.call_count == 1


# run_job
@patch("app.services.databricks._post_with_retry")
def test_run_job_calls_post_with_job_id(mock_post_with_retry):
    """
    run_job should build the payload with job_id and optional notebook_params.
    We patch _post_with_retry to return a value and assert run_job returns it.
    """
    mock_post_with_retry.return_value = {"run_id": 123}
    res = databricks.run_job(job_id="42", params={"a": "b"})
    assert res == {"run_id": 123}
    mock_post_with_retry.assert_called_once()
    # verify payload correctness by inspecting the last call args
    called_url, called_headers, called_payload = mock_post_with_retry.call_args[0]
    assert "jobs/run-now" in called_url or "run-now" in called_url
    assert isinstance(called_payload, dict)
    assert called_payload["job_id"] == "42"
    assert called_payload["notebook_params"] == {"a": "b"}


# retrieve_context
@patch("app.services.databricks.run_job")
def test_retrieve_context_success(mock_run_job):
    fake_result = {
        "documents": [
            {"id": "d1", "content": "one", "score": 0.9},
            {"id": "d2", "content": "two", "score": 0.8}
        ]
    }
    mock_run_job.return_value = fake_result

    docs = databricks.retrieve_context([0.1, 0.2], top_k=2)
    assert isinstance(docs, list)
    assert len(docs) == 2
    assert docs[0]["id"] == "d1"
    mock_run_job.assert_called_once()


@patch("app.services.databricks.run_job")
def test_retrieve_context_handles_missing_documents_key(mock_run_job):
    """
    If run_job returns a payload without 'documents', retrieve_context should return empty list.
    """
    mock_run_job.return_value = {"some": "value"}
    docs = databricks.retrieve_context([0.1], top_k=1)
    assert docs == []
    mock_run_job.assert_called_once()
