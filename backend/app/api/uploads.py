import uuid
from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel
from backend.app.storage.object_store import object_store

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

class PresignedUploadRequest(BaseModel):
    fileName: str

class PresignedUploadResponse(BaseModel):
    uploadUrl: str
    objectKey: str
    method: str
    headers: dict

@router.post("", response_model=PresignedUploadResponse)
async def get_presigned_upload(body: PresignedUploadRequest):
    if not body.fileName.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file: must be a PDF document.")
    
    unique_key = f"uploads/{uuid.uuid4()}/{body.fileName}"
    upload_info = object_store.generate_presigned_upload_url(unique_key)
    return upload_info

@router.put("/direct")
async def direct_upload_dev(key: str = Query(...), request: Request = None):
    # Fallback endpoint for local development without AWS S3 credentials
    body_bytes = await request.body()
    object_store.upload_pdf(key, body_bytes)
    return {"status": "uploaded", "key": key}
