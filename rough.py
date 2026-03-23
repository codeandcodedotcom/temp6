from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

router = APIRouter()

# ✅ Allowed file types (business types)
ALLOWED_FILE_TYPES = {
    "pilm",
    "par",
    "aorta",
    "henry",
    "skills_and_responsibilities"
}

# ✅ Allowed extensions
ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".csv"}


def get_file_extension(filename: str) -> str:
    return "." + filename.split(".")[-1].lower()


@router.post("/upload-file/{file_type}")
async def upload_file(file_type: str, file: UploadFile = File(...)):
    
    # ✅ Normalize file_type (handle frontend variations)
    file_type = file_type.strip().lower().replace(" ", "_")

    # ✅ Validate file_type
    if file_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {list(ALLOWED_FILE_TYPES)}"
        )

    # ✅ Validate file presence
    if not file:
        raise HTTPException(
            status_code=400,
            detail="File is required"
        )

    # ✅ Validate extension
    extension = get_file_extension(file.filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only .pdf, .xlsx, .csv files are allowed"
        )

    # 🚀 Pass to service layer (to be implemented next)
    # Example:
    # await file_upload_service.upload_file(file_type, file)

    return {
        "message": "File validation successful (API layer)",
        "file_type": file_type,
        "file_name": file.filename,
        "extension": extension
}

from app.api.upload_file import router as upload_router

app.include_router(upload_router, prefix="/api")
