import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

import app.utils.lessons_learnt as lessons


# -------------------------
# init_lessons_learnt
# -------------------------

def test_init_lessons_learnt_sets_env(monkeypatch):
    monkeypatch.setattr(
        "app.utils.lessons_learnt.set_databricks_env",
        lambda: None,
    )

    lessons.init_lessons_learnt()


# -------------------------
# _is_transient
# -------------------------

def test_is_transient_by_status_code():
    e = Exception("error")
    e.response = MagicMock(status_code=503)

    assert lessons._is_transient(e) is True


def test_is_transient_by_message():
    e = Exception("Request timeout")

    assert lessons._is_transient(e) is True


def test_is_not_transient():
    e = Exception("some other failure")

    assert lessons._is_transient(e) is False


# -------------------------
# get_endpoint_ready
# -------------------------

def test_get_endpoint_ready_success(monkeypatch):
    mock_client = MagicMock()
    mock_index = MagicMock()

    mock_client.get_index.return_value = mock_index

    monkeypatch.setattr(
        "app.utils.lessons_learnt.VectorSearchClient",
        lambda: mock_client,
    )

    lessons.get_endpoint_ready("ep", "idx")


def test_get_endpoint_ready_failure(monkeypatch):
    mock_client = MagicMock()
    mock_client.wait_for_endpoint.side_effect = Exception("boom")

    monkeypatch.setattr(
        "app.utils.lessons_learnt.VectorSearchClient",
        lambda: mock_client,
    )

    with pytest.raises(Exception):
        lessons.get_endpoint_ready("ep", "idx")


# -------------------------
# get_project_search_tool
# -------------------------

def test_get_project_search_tool(monkeypatch):
    monkeypatch.setattr(
        "app.utils.lessons_learnt.get_endpoint_ready",
        lambda *args, **kwargs: None,
    )

    mock_vs = MagicMock()
    monkeypatch.setattr(
        "app.utils.lessons_learnt.DatabricksVectorSearch",
        lambda **kwargs: mock_vs,
    )

    tool = lessons.get_project_search_tool("index", "endpoint")

    assert callable(tool)


# -------------------------
# retrieve
# -------------------------

def test_retrieve_success(monkeypatch):
    mock_vs = MagicMock()
    mock_vs.similarity_search_with_score.return_value = [
        (Document(page_content="test"), 0.1)
    ]

    monkeypatch.setattr(
        "app.utils.lessons_learnt.vector_store",
        mock_vs,
    )

    results = lessons.retrieve("project desc")

    assert len(results) == 1
    assert isinstance(results[0][0], Document)


def test_retrieve_empty_results(monkeypatch):
    mock_vs = MagicMock()
    mock_vs.similarity_search_with_score.return_value = []

    monkeypatch.setattr(
        "app.utils.lessons_learnt.vector_store",
        mock_vs,
    )

    results = lessons.retrieve("project desc")

    assert results == []


def test_retrieve_transient_then_success(monkeypatch):
    mock_vs = MagicMock()

    transient_exc = Exception("timeout")
    mock_vs.similarity_search_with_score.side_effect = [
        transient_exc,
        [(Document(page_content="ok"), 0.2)],
    ]

    monkeypatch.setattr(
        "app.utils.lessons_learnt.vector_store",
        mock_vs,
    )

    results = lessons.retrieve("project desc")

    assert len(results) == 1


def test_retrieve_non_transient_failure(monkeypatch):
    mock_vs = MagicMock()
    mock_vs.similarity_search_with_score.side_effect = Exception("fatal")

    monkeypatch.setattr(
        "app.utils.lessons_learnt.vector_store",
        mock_vs,
    )

    with pytest.raises(Exception):
        lessons.retrieve("project desc")
