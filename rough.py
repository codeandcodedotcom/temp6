import json
import pandas as pd
import pytest

from app.utils import get_pilm_content


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "dummy-host")
    monkeypatch.setenv("DATABRICKS_TOKEN", "dummy-token")
    monkeypatch.setattr(
        "app.utils.get_pilm_content.set_databricks_env",
        lambda: None,
    )


class FakeConn:
    def __enter__(self): return self
    def __exit__(self, *args): pass


@pytest.fixture
def mock_sql(monkeypatch):
    monkeypatch.setattr(
        "app.utils.get_pilm_content.sql.connect",
        lambda **kwargs: FakeConn(),
    )


def test_get_pilm_basic_success(monkeypatch, mock_env, mock_sql):
    df = pd.DataFrame(
        {
            "Heading": [
                "### Gate 1 - Concept Review (Stage 1 Exit)",
                "### Gate 2 - Preliminary Design Review (Stage 2 Exit)",
            ],
            "Content": ["C1", "C2"],
        }
    )

    monkeypatch.setattr(
        "app.utils.get_pilm_content.pd.read_sql",
        lambda query, conn: df,
    )

    parsed = json.loads(get_pilm_content.get_pilm())

    assert parsed
    assert all("Section" in s for s in parsed)
    assert all("GateContent" in s for s in parsed)


def test_get_pilm_multiple_rows_same_gate(monkeypatch, mock_env, mock_sql):
    df = pd.DataFrame(
        {
            "Heading": [
                "### Gate 1 - Concept Review (Stage 1 Exit)",
                "### Gate 1 - Innovation and Business Opportunity Review",
            ],
            "Content": ["C1", "C1b"],
        }
    )

    monkeypatch.setattr(
        "app.utils.get_pilm_content.pd.read_sql",
        lambda query, conn: df,
    )

    parsed = json.loads(get_pilm_content.get_pilm())

    contents = []
    for s in parsed:
        contents.extend(s["GateContent"])

    assert sorted(contents) == ["C1", "C1b"]


def test_get_pilm_no_matching_headings(monkeypatch, mock_env, mock_sql):
    df = pd.DataFrame(
        {
            "Heading": ["Unrelated Heading"],
            "Content": ["X"],
        }
    )

    monkeypatch.setattr(
        "app.utils.get_pilm_content.pd.read_sql",
        lambda query, conn: df,
    )

    parsed = json.loads(get_pilm_content.get_pilm())

    assert parsed
    assert all(s["GateContent"] == [] for s in parsed)


def test_get_pilm_empty_dataframe(monkeypatch, mock_env, mock_sql):
    df = pd.DataFrame(columns=["Heading", "Content"])

    monkeypatch.setattr(
        "app.utils.get_pilm_content.pd.read_sql",
        lambda query, conn: df,
    )

    parsed = json.loads(get_pilm_content.get_pilm())

    assert parsed
    assert all(s["GateContent"] == [] for s in parsed)
