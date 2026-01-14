from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import os

ACCOUNT_URL = "https://mcseundevshsa.blob.core.windows.net"   # your storage account

CONTAINER_NAME = "apdlit-v1"
FOLDER = "charter-pdfs"

credential = DefaultAzureCredential()
blob_service = BlobServiceClient(account_url=ACCOUNT_URL, credential=credential)
container = blob_service.get_container_client(CONTAINER_NAME)


------

from io import BytesIO
from app.core.blob import container, FOLDER

buffer = BytesIO()

doc = SimpleDocTemplate(buffer, pagesize=A4, ...)
doc.build(...)

buffer.seek(0)
blob_path = f"{FOLDER}/{pdf_filename}"

container.upload_blob(
    name=blob_path,
    data=buffer,
    overwrite=True,
    content_type="application/pdf"
)

------

from fastapi.responses import StreamingResponse
from app.core.blob import container, FOLDER


@router.get("/pdf/{filename}")
async def serve_pdf(filename: str):
    blob_path = f"{FOLDER}/{filename}"
    blob = container.get_blob_client(blob_path)

    if not blob.exists():
        raise HTTPException(404, "PDF not found")

    return StreamingResponse(
        blob.download_blob(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
)

