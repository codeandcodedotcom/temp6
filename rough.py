from pathlib import Path

safe_tmp = Path(os.getenv("TMPDIR", "/tmp")) / "mcs-apd-lit-tmp"
safe_tmp.mkdir(parents=True, exist_ok=True)
os.environ["DATABRICKS_CONFIG_FILE"] = str(safe_tmp / "dummy")
