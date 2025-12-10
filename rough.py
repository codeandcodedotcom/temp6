# src/app/services/html_to_pdf.py

from pathlib import Path
from typing import Tuple, Union
from uuid import UUID

from xhtml2pdf import pisa  # make sure:  pip install xhtml2pdf
from app.core.logging import get_logger

logger = get_logger(__name__)

# src/ directory (this file is src/app/services/html_to_pdf.py)
SRC_ROOT = Path(__file__).resolve().parents[2]

# Folder where PDFs will be written: src/generated_pdf
PDF_ROOT = SRC_ROOT / "generated_pdf"

# URL prefix under which we’ll serve these PDFs
PDF_URL_PREFIX = "/pdf"


def generate_project_pdf(
    html_doc: str,
    project_id: Union[str, UUID],
) -> Tuple[Path, str]:
    """
    Render HTML to a PDF file on disk and return (file_path, public_url).
    File will be stored as  <project_id>.id  in src/generated_pdf.
    """

    PDF_ROOT.mkdir(parents=True, exist_ok=True)

    project_id_str = str(project_id)

    # You asked for `<project_id>.id` as the filename:
    filename = f"{project_id_str}.id"   # content is still a PDF

    pdf_path = PDF_ROOT / filename
    logger.info("Generating PDF at %s", pdf_path)

    # Write PDF
    with pdf_path.open("wb") as f:
        result = pisa.CreatePDF(html_doc, dest=f)

    if result.err:
        logger.error("Failed to generate PDF for project %s: %s", project_id_str, result.err)
        raise RuntimeError("Failed to generate PDF")

    # This URL is what we’ll store in the DB and return to frontend
    public_url = f"{PDF_URL_PREFIX}/{filename}"

    return pdf_path, public_url

    -----

# src/app/main.py

from pathlib import Path
from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI

app = FastAPI(...)

# existing routers...
# app.include_router(...)

# Figure out src/ and generated_pdf path
SRC_ROOT = Path(__file__).resolve().parents[1]   # src/app -> parents[1] = src
PDF_DIR = SRC_ROOT / "generated_pdf"
PDF_DIR.mkdir(exist_ok=True)

# Serve files under /pdf/...
app.mount("/pdf", StaticFiles(directory=str(PDF_DIR)), name="pdf")



------


response = {
    "project_id": project_id,
    "charter_id": charter_id,
    ...
}

# 1. build HTML
html_doc = render_html_from_response(response)

# 2. generate PDF using only project_id
_, pdf_url = generate_project_pdf(html_doc, project_id=project_id)

# 3. attach URL to response so it can be stored + returned
#    use the exact key your DB / Pydantic model expects
response["charter_pdf_url"] = pdf_url   # or "pdf_url", "charter_pdf", etc.
