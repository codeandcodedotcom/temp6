@router.get("/pdf/{filename}")
async def serve_pdf(filename: str):
    pdf_path = PDF_DIR / filename

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename
    )
