"""
FileForge – File upload / download / list routes
"""
import logging
import mimetypes
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.file_record import FileRecord
from app.services.storage import (
    delete_file,
    is_extension_allowed,
    output_file_exists,
    output_file_path,
    save_upload,
)
from app.services.converter import SUPPORTED_OPERATIONS
from app.tasks.process_file import process_file_task

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("/upload", summary="Upload a file for processing")
async def upload_file(
    file:      UploadFile = File(...),
    operation: str        = Form("copy"),
    db:        Session    = Depends(get_db),
):
    """
    Upload a file and optionally specify a processing operation.
    Returns a file record with a job_id to poll for status.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    if not is_extension_allowed(file.filename):
        raise HTTPException(
            status_code=415,
            detail=f"File type not supported. Allowed types include images, PDFs, documents, etc.",
        )

    if operation not in SUPPORTED_OPERATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown operation '{operation}'. Supported: {list(SUPPORTED_OPERATIONS.keys())}",
        )

    # Save to disk
    try:
        stored_name, size_bytes = await save_upload(file)
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")

    # Detect MIME
    mime_type, _ = mimetypes.guess_type(file.filename)

    # Create DB record
    record = FileRecord(
        id            = str(uuid.uuid4()),
        original_name = file.filename,
        stored_name   = stored_name,
        mime_type     = mime_type,
        size_bytes    = size_bytes,
        operation     = operation,
        status        = "pending",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Dispatch Celery task
    task = process_file_task.delay(record.id)

    # Save job_id
    record.job_id = task.id
    db.commit()
    db.refresh(record)

    logger.info(f"Uploaded: {file.filename} → record={record.id} task={task.id}")
    return record.to_dict()


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/", summary="List all file records")
def list_files(
    skip:   int           = 0,
    limit:  int           = 50,
    status: Optional[str] = None,
    db:     Session       = Depends(get_db),
):
    query = db.query(FileRecord).filter(FileRecord.purged == False)  # noqa: E712
    if status:
        query = query.filter(FileRecord.status == status)
    total   = query.count()
    records = query.order_by(FileRecord.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total":   total,
        "records": [r.to_dict() for r in records],
    }


# ── Get one ───────────────────────────────────────────────────────────────────

@router.get("/{record_id}", summary="Get a single file record")
def get_file(record_id: str, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File record not found.")
    return record.to_dict()


# ── Download ──────────────────────────────────────────────────────────────────

@router.get("/{record_id}/download", summary="Download processed output")
def download_file(record_id: str, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File record not found.")

    if record.status != "done":
        raise HTTPException(
            status_code=409,
            detail=f"File is not ready for download (status: {record.status}).",
        )

    if not record.output_name or not output_file_exists(record.output_name):
        raise HTTPException(status_code=404, detail="Output file not found on disk.")

    path      = output_file_path(record.output_name)
    mime, _   = mimetypes.guess_type(record.output_name)
    mime      = mime or "application/octet-stream"

    return FileResponse(
        path=path,
        media_type=mime,
        filename=record.output_name,
        headers={"Content-Disposition": f'attachment; filename="{record.output_name}"'},
    )


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{record_id}", summary="Delete a file record and its files")
def delete_record(record_id: str, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File record not found.")

    delete_file(settings.UPLOAD_DIR, record.stored_name)
    if record.output_name:
        delete_file(settings.OUTPUT_DIR, record.output_name)

    db.delete(record)
    db.commit()
    return {"deleted": True, "id": record_id}


# ── Supported operations ──────────────────────────────────────────────────────

@router.get("/meta/operations", summary="List supported operations")
def list_operations():
    return {"operations": SUPPORTED_OPERATIONS}
