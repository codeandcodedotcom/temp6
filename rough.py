import pytest
from unittest.mock import MagicMock

import app.utils.lessons_learnt as lessons_learnt


# -----------------------------
# Shared mocks
# -----------------------------

@pytest.fixture
def fake_vector_store():
    store = MagicMock()
    store.similarity_search_with_score.return_value = []
    return store


@pytest.fixture
def patch_common(monkeypatch, fake_vector_store):
    # Prevent env / databricks side effects
    monkeypatch.setattr(
        "app.utils.lessons_learnt.set_databricks_env",
        lambda: None,
    )

    # Skip endpoint readiness logic
    monkeypatch.setattr(
        "app.utils.lessons_learnt.get_endpoint_ready",
        lambda *_, **__: None,
    )

    # Patch VectorSearch client constructor
    monkeypatch.setattr(
        "app.utils.lessons_learnt.VectorSearchClient",
        MagicMock,
    )

    # Patch DatabricksVectorSearch constructor (THIS IS CRITICAL)
    monkeypatch.setattr(
        "app.utils.lessons_learnt.DatabricksVectorSearch",
        lambda **kwargs: fake_vector_store,
    )


# -----------------------------
# Tests
# -----------------------------

def test_get_project_search_tool_returns_callable(patch_common):
    tool = lessons_learnt.get_project_search_tool(
        index_name="idx",
        endpoint_name="ep",
    )

    assert callable(tool)


def test_retrieve_returns_empty_list_when_no_results(patch_common):
    retrieve = lessons_learnt.get_project_search_tool(
        index_name="idx",
        endpoint_name="ep",
    )

    results = retrieve(
        project_description="test project",
        top_k=1,
        filters=None,
    )

    assert results == []


def test_retrieve_calls_similarity_search_with_expected_args(
    patch_common,
    fake_vector_store,
):
    retrieve = lessons_learnt.get_project_search_tool(
        index_name="idx",
        endpoint_name="ep",
    )

    retrieve(
        project_description="sample",
        top_k=3,
        filters={"key": "value"},
    )

    fake_vector_store.similarity_search_with_score.assert_called_once()
    args, kwargs = fake_vector_store.similarity_search_with_score.call_args

    assert kwargs["query"] == "sample"
    assert kwargs["k"] == 3
    assert kwargs["query_type"] == "HYBRID"
    assert kwargs["filter"] == {"key": "value"}


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
