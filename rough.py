from pathlib import Path
import os


def get_tmp_root() -> Path:
    """
    Determine a safe temporary root directory.

    If TMPDIR is not set, /tmp is used as a base, but an
    application-specific subdirectory is created to avoid
    security risks associated with writing directly to a
    world-writable directory.
    """
    root = Path(os.getenv("TMPDIR", "/tmp"))

    # If using system /tmp, switch to an app-specific subdirectory
    if root == Path("/tmp"):
        root = root / "mcs-apd-lit-tmp"
        root.mkdir(parents=True, exist_ok=True)

    return root


# Base temporary directory for the application
TMP_ROOT = get_tmp_root()

# Directory to store generated PDFs
PDF_DIR = TMP_ROOT / "generated_pdf"
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Public URL prefix for accessing generated PDFs
PDF_URL_PREFIX = "/pdfs"
