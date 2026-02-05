import json
import pandas as pd
import pytest

from app.utils import get_pilm_content


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "Heading": [
                "### Gate 1 - Concept Review (Stage 1 Exit)",
                "### Gate 1 - Innovation and Business Opportunity Review",
                "### Gate 2 - Preliminary Design Review (Stage 2 Exit)",
                "### Gate 3.5 - Production Readiness Review",
            ],
            "Content": ["C1", "C1b", "C2", "C3"],
        }
    )


def test_get_pilm_basic_success(monkeypatch, sample_df):
    monkeypatch.setattr(
        "app.utils.get_pilm_content.set_databricks_env",
        lambda: None,
    )

    monkeypatch.setattr(
        "app.utils.get_pilm_content.pd.read_sql",
        lambda query, conn: sample_df,
    )

    class FakeConn:
        def __enter__(self): return self
        def __exit__(self, *args): pass

    monkeypatch.setattr(
        "app.utils.get_pilm_content.sql.connect",
        lambda **kwargs: FakeConn(),
    )

    result = get_pilm_content.get_pilm()
    parsed = json.loads(result)

    assert isinstance(parsed, list)
    assert parsed
    assert all("Section" in s for s in parsed)
    assert all("GateContent" in s for s in parsed)


def test_get_pilm_multiple_rows_same_gate(monkeypatch, sample_df):
    monkeypatch.setattr(
        "app.utils.get_pilm_content.set_databricks_env",
        lambda: None,
    )

    monkeypatch.setattr(
        "app.utils.get_pilm_content.pd.read_sql",
        lambda query, conn: sample_df,
    )

    class FakeConn:
        def __enter__(self): return self
        def __exit__(self, *args): pass

    monkeypatch.setattr(
        "app.utils.get_pilm_content.sql.connect",
        lambda **kwargs: FakeConn(),
    )

    parsed = json.loads(get_pilm_content.get_pilm())

    non_empty_sections = [s for s in parsed if s["GateContent"]]
    assert non_empty_sections

    all_contents = []
    for s in non_empty_sections:
        all_contents.extend(s["GateContent"])

    assert {"C1", "C1b"}.issubset(set(all_contents))


def test_get_pilm_no_matching_headings(monkeypatch):
    df = pd.DataFrame(
        {
            "Heading": ["Unrelated Heading"],
            "Content": ["X"],
        }
    )

    monkeypatch.setattr(
        "app.utils.get_pilm_content.set_databricks_env",
        lambda: None,
    )

    monkeypatch.setattr(
        "app.utils.get_pilm_content.pd.read_sql",
        lambda query, conn: df,
    )

    class FakeConn:
        def __enter__(self): return self
        def __exit__(self, *args): pass

    monkeypatch.setattr(
        "app.utils.get_pilm_content.sql.connect",
        lambda **kwargs: FakeConn(),
    )

    parsed = json.loads(get_pilm_content.get_pilm())

    assert parsed
    assert all(s["GateContent"] == [] for s in parsed)


def test_get_pilm_empty_dataframe(monkeypatch):
    df = pd.DataFrame(columns=["Heading", "Content"])

    monkeypatch.setattr(
        "app.utils.get_pilm_content.set_databricks_env",
        lambda: None,
    )

    monkeypatch.setattr(
        "app.utils.get_pilm_content.pd.read_sql",
        lambda query, conn: df,
    )

    class FakeConn:
        def __enter__(self): return self
        def __exit__(self, *args): pass

    monkeypatch.setattr(
        "app.utils.get_pilm_content.sql.connect",
        lambda **kwargs: FakeConn(),
    )

    parsed = json.loads(get_pilm_content.get_pilm())

    assert parsed
    assert all(s["GateContent"] == [] for s in parsed)
