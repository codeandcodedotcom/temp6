import os
import pandas as pd
from datetime import datetime
from fastapi import UploadFile, HTTPException

# ===== CONFIG =====
BASE_PATH = "/dbfs/Volumes/your_catalog/your_schema/your_volume/files"


# ===== COMMON HELPERS =====

def _save_file(file: UploadFile, base_name: str):
    os.makedirs(BASE_PATH, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    versioned_name = f"{base_name}_{timestamp}"
    latest_name = f"{base_name}_latest"

    versioned_path = os.path.join(BASE_PATH, versioned_name)
    latest_path = os.path.join(BASE_PATH, latest_name)

    file.file.seek(0)
    with open(versioned_path, "wb") as f:
        f.write(file.file.read())

    file.file.seek(0)
    with open(latest_path, "wb") as f:
        f.write(file.file.read())

    return versioned_name


def _read_tabular_file(file: UploadFile):
    try:
        if file.filename.endswith(".csv"):
            return pd.read_csv(file.file)
        return pd.read_excel(file.file)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid file. Unable to read Excel/CSV"
        )


def _validate_columns(df, required_columns):
    df_cols = [col.strip() for col in df.columns]

    missing = [col for col in required_columns if col not in df_cols]

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {missing}"
        )


def _validate_pdf_name(file: UploadFile, keyword: str):
    if keyword not in file.filename.lower():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file name. Must contain '{keyword}'"
        )


# ===== SERVICE FUNCTIONS =====

# 1️⃣ PILM
async def handle_pilm_upload(file: UploadFile):
    _validate_pdf_name(file, "pilm")

    saved = _save_file(file, "pilm.pdf")

    return {
        "message": "PILM uploaded successfully",
        "version": saved
    }


# 2️⃣ PAR
async def handle_par_upload(file: UploadFile):
    _validate_pdf_name(file, "par")

    saved = _save_file(file, "par.pdf")

    return {
        "message": "PAR uploaded successfully",
        "version": saved
    }


# 3️⃣ AORTA
async def handle_aorta_upload(file: UploadFile):
    df = _read_tabular_file(file)

    _validate_columns(df, ["Finding", "Action"])

    saved = _save_file(file, "aorta.xlsx")

    return {
        "message": "AORTA uploaded successfully",
        "version": saved
    }


# 4️⃣ HENRY
async def handle_henry_upload(file: UploadFile):
    df = _read_tabular_file(file)

    required_columns = [
        "Context of project",
        "Category",
        "Sub-category",
        "Lesson Description",
        "Impact",
        "Short term action",
        "Long term action"
    ]

    _validate_columns(df, required_columns)

    saved = _save_file(file, "henry.xlsx")

    return {
        "message": "Henry uploaded successfully",
        "version": saved
    }


# 5️⃣ SKILLS & RESPONSIBILITIES
async def handle_skills_upload(file: UploadFile):
    df = _read_tabular_file(file)

    _validate_columns(df, [
        "Job Profile",
        "Skills",
        "Responsibilities",
        "Tasks"
    ])

    saved = _save_file(file, "skills.xlsx")

    return {
        "message": "Skills file uploaded successfully",
        "version": saved
    }



from app.services.upload_file_service import (
    handle_pilm_upload,
    handle_par_upload,
    handle_aorta_upload,
    handle_henry_upload,
    handle_skills_upload
              )

if file_type == "pilm":
    return await handle_pilm_upload(file)

elif file_type == "par":
    return await handle_par_upload(file)

elif file_type == "aorta":
    return await handle_aorta_upload(file)

elif file_type == "henry":
    return await handle_henry_upload(file)

elif file_type == "skills_and_responsibilities":
    return await handle_skills_upload(file)
