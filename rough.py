from pathlib import Path
from tempfile import gettempdir

TMP_ROOT = Path(gettempdir()) / "mcs-apd-lit-tmp"
TMP_ROOT.mkdir(parents=True, exist_ok=True)

PDF_DIR = TMP_ROOT / "generated_pdf"
PDF_DIR.mkdir(parents=True, exist_ok=True)

PDF_URL_PREFIX = "/pdf"



from pathlib import Path
from tempfile import gettempdir

safe_tmp = Path(gettempdir()) / "mcs-apd-lit-tmp"
safe_tmp.mkdir(parents=True, exist_ok=True)

os.environ["DATABRICKS_CONFIG_FILE"] = str(safe_tmp / "dummy")
