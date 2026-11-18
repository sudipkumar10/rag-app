import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.db.models import Document, DocumentStatus
from app.services.storage.minio_client import minio_client
from app.workers.tasks import process_document_task
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    tenant_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document to MinIO, create a DB record, and trigger async processing.
    """
    # 1. Validation
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ingestion_allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {ext} not allowed."
        )

    # 2. Read file (uploadFile gives a SpooledTemporaryFile)
    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.ingestion_max_file_size_mb:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Max {settings.ingestion_max_file_size_mb}MB."
        )

    # 3. Generate ID and Object Key
    document_id = str(uuid.uuid4())
    safe_filename = Path(file.filename).name
    object_key = f"{tenant_id}/{document_id}/{safe_filename}"

    try:
        # 4. Upload to MinIO (Raw Storage)
        minio_client.upload_raw(
            object_key=object_key,
            data=file_bytes,
            content_type=file.content_type or "application/octet-stream"
        )

        # 5. Create Database Record
        db_doc = Document(
            id=document_id,
            tenant_id=tenant_id,
            original_filename=safe_filename,
            object_key=object_key,
            status=DocumentStatus.PENDING
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        # 6. Trigger Celery Task (Background Job)
        process_document_task.delay(document_id=document_id)

        logger.info(
            "Document uploaded and queued",
            extra={"extra_fields": {"document_id": document_id, "tenant_id": tenant_id}}
        )
        
        return {
            "message": "File uploaded successfully. Processing started.",
            "document_id": document_id,
            "status": DocumentStatus.PENDING.value
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during upload.")


@router.get("/{document_id}/status")
def get_document_status(document_id: str, db: Session = Depends(get_db)):
    """Check the processing status of an uploaded document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return {
        "document_id": doc.id,
        "filename": doc.original_filename,
        "status": doc.status.value,
        "error": doc.error_message
    }