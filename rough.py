from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

SRC_ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = SRC_ROOT / "generated_pdf"

@router.get("/charters/{project_id}/download")
async def download_charter_pdf(project_id: str):
    file_path = PDF_DIR / f"{project_id}.id"
    return FileResponse(
        path=file_path,
        filename=f"{project_id}.pdf",  # name seen by user
        media_type="application/pdf",
    )
