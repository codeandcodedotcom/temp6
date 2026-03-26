import io
import os
import requests
import pandas as pd
from fastapi import UploadFile, HTTPException


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
    # 1. Get CDP Databricks config
    # --------------------------
    host = os.getenv("DATABRICKS_CDP_HOST")
    token = os.getenv("DATABRICKS_CDP_TOKEN")

    if not host or not token:
        raise HTTPException(
            status_code=500,
            detail="CDP Databricks configuration missing"
        )

    # --------------------------
    # 2. Validate file type
    # --------------------------
    file_type = file_type.strip().lower()

    VALID_FILE_TYPES = {"pilm", "par", "aorta", "henry", "skills"}

    if file_type not in VALID_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file_type}"
        )

    filename = file.filename.lower()

    # --------------------------
    # 3. PDF validation (pilm, par)
    # --------------------------
    if file_type in ["pilm", "par"]:

        if not filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files allowed for pilm/par"
            )

        if file_type not in filename:
            raise HTTPException(
                status_code=400,
                detail=f"Filename must contain '{file_type}'"
            )

        contents = await file.read()

    # --------------------------
    # 4. Excel/CSV validation (others)
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
    # 5. Build upload path
    # --------------------------
    BASE_PATH = "/Volumes/dev_cdp_eng_adb_catalog/raw/apdlit"

    FILE_PATHS = {
        "pilm": f"{BASE_PATH}/pilm/",
        "par": f"{BASE_PATH}/par/",
        "aorta": f"{BASE_PATH}/aorta/",
        "henry": f"{BASE_PATH}/henry/",
        "skills": f"{BASE_PATH}/skills/",
    }

    upload_path = FILE_PATHS[file_type] + file.filename

    # --------------------------
    # 6. Upload to Databricks
    # --------------------------
    url = f"{host}/api/2.0/fs/files{upload_path}?overwrite=true"

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
    # 7. Success response
    # --------------------------
    return {
        "message": "File uploaded successfully",
        "file_type": file_type,
        "file_name": file.filename,
        "path": upload_path
}
