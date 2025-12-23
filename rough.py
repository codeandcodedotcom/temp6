from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.charter import Charter as DBCharter
from app.schemas.project import Project
from pathlib import Path

router = APIRouter()

PDF_DIR = Path("src/generated_pdf")

@router.get("/pdf/{filename}")
async def serve_pdf(filename: str, session: AsyncSession = Depends(get_db)):
    pdf_path = PDF_DIR / filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    # filename = project_charter_<charter_id>_<timestamp>.pdf
    charter_id = filename.replace("project_charter_", "").split("_")[0]

    charter = await session.get(DBCharter, charter_id)
    project_title = "Project Charter"

    if charter and charter.project_id:
        project = await session.get(Project, charter.project_id)
        if project and project.project_title:
            project_title = project.project_title

    safe_name = project_title.replace(" ", "_") + ".pdf"

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{safe_name}"'
        }
    )

----

from app.api import pdf
app.include_router(pdf.router)
