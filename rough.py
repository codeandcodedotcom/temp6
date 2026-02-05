import pytest
import json
import pathlib
from unittest.mock import patch, MagicMock

# --------------------------------------------------
# CRITICAL: patch config BEFORE importing auth module
# --------------------------------------------------
with patch("configparser.ConfigParser.get", return_value="testhost"):
    from app.authentication.databricks_auth import DatabricksAuth, main


# ==================================================
# INIT TEST
# ==================================================
def test_init_reads_config():
    with patch("configparser.ConfigParser.read") as mock_read:
        auth = DatabricksAuth()
        mock_read.assert_called()
        assert hasattr(auth, "config")
        assert auth.token == ""


# ==================================================
# GET TOKEN — SUCCESS
# ==================================================
@patch("subprocess.run")
@patch("pathlib.Path.home")
@patch("builtins.open")
@patch("configparser.ConfigParser.set")
@patch("configparser.ConfigParser.write")
def test_get_token_success(
    mock_write,
    mock_set,
    mock_open,
    mock_home,
    mock_run,
):
    auth = DatabricksAuth()

    token_json = json.dumps({
        "tokens": {
            "testhost": {
                "access_token": "abc123"
            }
        }
    })

    mock_path = MagicMock()
    mock_path.read_text.return_value = token_json
    mock_home.return_value = pathlib.Path("/mockhome")

    with patch("pathlib.Path.read_text", return_value=token_json):
        auth.get_token()

    mock_run.assert_called()
    mock_set.assert_called()
    mock_write.assert_called()
    assert auth.token == "abc123"


# ==================================================
# GET TOKEN — SUBPROCESS ERROR
# ==================================================
@patch("subprocess.run", side_effect=Exception("fail"))
def test_get_token_subprocess_error(mock_run):
    auth = DatabricksAuth()

    with pytest.raises(Exception):
        auth.get_token()


# ==================================================
# MAIN CALLS GET_TOKEN
# ==================================================
def test_main_calls_get_token():
    with patch(
        "app.authentication.databricks_auth.DatabricksAuth.get_token"
    ) as mock_get_token:
        with patch(
            "app.authentication.databricks_auth.DatabricksAuth.__init__",
            return_value=None
        ):
            main()
            mock_get_token.assert_called()
