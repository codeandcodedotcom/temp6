from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.upload_file_service import process_upload

router = APIRouter()

# Allowed file types (match service + config)
ALLOWED_FILE_TYPES = {
    "pilm",
    "par",
    "aorta",
    "henry",
    "skills"
}

# Allowed extensions
ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".csv"}


def get_file_extension(filename: str) -> str:
    return "." + filename.split(".")[-1].lower()


@router.post("/upload-file/{file_type}")
async def upload_file(file_type: str, file: UploadFile = File(...)):

    # --------------------------
    # 1. Normalize file_type
    # --------------------------
    file_type = file_type.strip().lower().replace(" ", "_")

    # handle frontend mismatch
    if file_type == "skills_and_responsibilities":
        file_type = "skills"

    # --------------------------
    # 2. Validate file type
    # --------------------------
    if file_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {list(ALLOWED_FILE_TYPES)}"
        )

    # --------------------------
    # 3. Validate file presence
    # --------------------------
    if not file:
        raise HTTPException(
            status_code=400,
            detail="File is required"
        )

    # --------------------------
    # 4. Validate extension
    # --------------------------
    extension = get_file_extension(file.filename)

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only .pdf, .xlsx, .csv files are allowed"
        )

    # --------------------------
    # 5. Call service layer
    # --------------------------
    return await process_upload(file_type, file)
