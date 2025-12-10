# src/app/services/html_to_pdf.py

from pathlib import Path
from typing import Tuple, Union
from uuid import UUID

from xhtml2pdf import pisa

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Root of the src/ directory (this file is src/app/services/html_to_pdf.py)
SRC_ROOT = Path(__file__).resolve().parents[2]

# Folder where PDFs will be written: src/generated_pdf
PDF_ROOT = SRC_ROOT / "generated_pdf"

# URL prefix under which we'll serve these PDFs (see StaticFiles mount in main.py)
PDF_URL_PREFIX = "/pdf"


def generate_project_pdf(
    html_doc: str,
    project_id: Union[str, UUID],
) -> Tuple[Path, str]:
    """
    Render HTML to a PDF file on disk.

    File will be stored as:  <project_id>.pdf  in src/generated_pdf.
    Returns (pdf_path, public_url).
    """

    # Ensure output directory exists
    PDF_ROOT.mkdir(parents=True, exist_ok=True)

    project_id_str = str(project_id)
    filename = f"{project_id_str}.pdf"
    pdf_path = PDF_ROOT / filename

    logger.info("Generating PDF for project %s at %s", project_id_str, pdf_path)

    # xhtml2pdf expects a text (str); normalise input just in case
    if isinstance(html_doc, bytes):
        html_src = html_doc.decode("utf-8", errors="ignore")
    else:
        html_src = html_doc

    # Write PDF
    with pdf_path.open("wb") as f:
        result = pisa.CreatePDF(html_src, dest=f, encoding="utf-8")

    if result.err:
        logger.error(
            "Failed to generate PDF for project %s: %s",
            project_id_str,
            result.err,
        )
        # Best-effort cleanup of a partial / corrupt file
        try:
            pdf_path.unlink(missing_ok=True)
        except Exception:
            logger.exception("Failed to remove partial PDF at %s", pdf_path)
        raise RuntimeError("Failed to generate PDF")

    public_url = f"{PDF_URL_PREFIX}/{filename}"
    logger.info(
        "Successfully generated PDF for project %s. Public URL: %s",
        project_id_str,
        public_url,
    )

    return pdf_path, public_url
