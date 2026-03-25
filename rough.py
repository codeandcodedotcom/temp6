# Databricks
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

# Volume base path
DATABRICKS_VOLUME_BASE_PATH = "/Volumes/dev_cdp_eng_adb_catalog/raw/apdlit"

# File specific paths
DATABRICKS_FILE_PATHS = {
    "pilm": f"{DATABRICKS_VOLUME_BASE_PATH}/pilm/",
    "par": f"{DATABRICKS_VOLUME_BASE_PATH}/par/",
    "aorta": f"{DATABRICKS_VOLUME_BASE_PATH}/aorta/",
    "henry": f"{DATABRICKS_VOLUME_BASE_PATH}/henry/",
    "skills": f"{DATABRICKS_VOLUME_BASE_PATH}/skills/",
}


import io
import requests
import pandas as pd
from fastapi import UploadFile, HTTPException
from app.config import Config


# ==============================
# COLUMN VALIDATIONS
# ==============================

REQUIRED_COLUMNS = {
    "aorta": {"Finding", "Action"},
    "henry": {
        "Context of project",
        "Category",
        "Sub-category",
        "Lesson Description",
        "Impact",
        "Short term action",
        "Long term action",
    },
    "skills": {
        "Job Profile",
        "Skills",
        "Responsibilities",
        "Tasks",
    },
}


# ==============================
# MAIN SERVICE FUNCTION
# ==============================

async def process_upload(file_type: str, file: UploadFile):

    # --------------------------
    # 1. Get config
    # --------------------------
    host = Config.DATABRICKS_HOST
    token = Config.DATABRICKS_TOKEN
    file_paths = Config.DATABRICKS_FILE_PATHS

    if not host or not token:
        raise HTTPException(
            status_code=500,
            detail="Databricks configuration missing"
        )

    # --------------------------
    # 2. Validate file type
    # --------------------------
    if file_type not in file_paths:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file_type}"
        )

    filename = file.filename.lower()

    # --------------------------
    # 3. PDF validation
    # --------------------------
    if file_type in ["pilm", "par"]:
        if not filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files allowed"
            )

        if file_type not in filename:
            raise HTTPException(
                status_code=400,
                detail=f"Filename must contain '{file_type}'"
            )

        contents = await file.read()

    # --------------------------
    # 4. Excel/CSV validation
    # --------------------------
    else:
        if not (filename.endswith(".xlsx") or filename.endswith(".csv")):
            raise HTTPException(
                status_code=400,
                detail="Only Excel or CSV files allowed"
            )

        contents = await file.read()

        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid file format"
            )

        required_cols = REQUIRED_COLUMNS.get(file_type, set())
        file_cols = set(df.columns.str.strip())

        missing = required_cols - file_cols

        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing columns: {list(missing)}"
            )

    # --------------------------
    # 5. Upload to Databricks
    # --------------------------
    upload_path = file_paths[file_type] + file.filename

    url = f"{host}/api/2.0/fs/files{upload_path}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream"
    }

    response = requests.put(url, headers=headers, data=contents)

    if response.status_code not in [200, 201]:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {response.text}"
        )

    # --------------------------
    # 6. Success response
    # --------------------------
    return {
        "message": "File uploaded successfully",
        "file_type": file_type,
        "file_name": file.filename,
        "path": upload_path
}





from app.services.upload_file_service import process_upload

@router.post("/upload-file/{file_type}")
async def upload_file(file_type: str, file: UploadFile = File(...)):
    return await process_upload(file_type, file)
