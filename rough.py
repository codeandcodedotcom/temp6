import json
import pandas as pd
from unittest.mock import MagicMock
import pytest

import app.utils.get_par_content as par_content


# -------------------------
# Helpers
# -------------------------

class DummyConn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


# -------------------------
# Tests
# -------------------------

def test_get_par_success(monkeypatch):
    # Mock env setup
    monkeypatch.setattr(
        "app.utils.get_par_content.set_databricks_env",
        lambda: None,
    )

    # Mock env vars
    monkeypatch.setenv("DATABRICKS_HOST", "host")
    monkeypatch.setenv("DATABRICKS_TOKEN", "token")

    # Mock SQL connect
    monkeypatch.setattr(
        "app.utils.get_par_content.sql.connect",
        lambda **kwargs: DummyConn(),
    )

    # Fake dataframe
    df = pd.DataFrame(
        {
            "Gate": ["Gate 1", "Gate 2", "Gate 3"],
            "Content": ["C1", "C2", "C3"],
        }
    )

    monkeypatch.setattr(
        "app.utils.get_par_content.pd.read_sql",
        lambda query, conn: df,
    )

    result = par_content.get_par()
    parsed = json.loads(result)

    assert isinstance(parsed, list)
    assert len(parsed) > 0

    # Verify structure
    for section in parsed:
        assert "Section" in section
        assert "GateContent" in section
        assert isinstance(section["GateContent"], list)


def test_get_par_empty_dataframe(monkeypatch):
    monkeypatch.setattr(
        "app.utils.get_par_content.set_databricks_env",
        lambda: None,
    )

    monkeypatch.setenv("DATABRICKS_HOST", "host")
    monkeypatch.setenv("DATABRICKS_TOKEN", "token")

    monkeypatch.setattr(
        "app.utils.get_par_content.sql.connect",
        lambda **kwargs: DummyConn(),
    )

    empty_df = pd.DataFrame(columns=["Gate", "Content"])

    monkeypatch.setattr(
        "app.utils.get_par_content.pd.read_sql",
        lambda query, conn: empty_df,
    )

    result = par_content.get_par()
    parsed = json.loads(result)

    # All sections should exist but have empty GateContent
    for section in parsed:
        assert section["GateContent"] == []


def test_get_par_multiple_rows_same_gate(monkeypatch):
    monkeypatch.setattr(
        "app.utils.get_par_content.set_databricks_env",
        lambda: None,
    )

    monkeypatch.setenv("DATABRICKS_HOST", "host")
    monkeypatch.setenv("DATABRICKS_TOKEN", "token")

    monkeypatch.setattr(
        "app.utils.get_par_content.sql.connect",
        lambda **kwargs: DummyConn(),
    )

    df = pd.DataFrame(
        {
            "Gate": ["Gate 1", "Gate 1", "Gate 2"],
            "Content": ["C1", "C1b", "C2"],
        }
    )

    monkeypatch.setattr(
        "app.utils.get_par_content.pd.read_sql",
        lambda query, conn: df,
    )

    result = par_content.get_par()
    parsed = json.loads(result)

    gate1_sections = [
        s for s in parsed if "Gate 1" in s["Section"].lower()
    ]

    assert gate1_sections
    assert len(gate1_sections[0]["GateContent"]) == 2


def test_get_par_sql_failure(monkeypatch):
    monkeypatch.setattr(
        "app.utils.get_par_content.set_databricks_env",
        lambda: None,
    )

    monkeypatch.setenv("DATABRICKS_HOST", "host")
    monkeypatch.setenv("DATABRICKS_TOKEN", "token")

    monkeypatch.setattr(
        "app.utils.get_par_content.sql.connect",
        lambda **kwargs: DummyConn(),
    )

    monkeypatch.setattr(
        "app.utils.get_par_content.pd.read_sql",
        lambda query, conn: (_ for _ in ()).throw(Exception("sql failed")),
    )

    with pytest.raises(Exception):
        par_content.get_par()
