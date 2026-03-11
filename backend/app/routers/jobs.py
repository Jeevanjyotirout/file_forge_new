"""
FileForge – Job status polling routes
"""
import logging

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.database import get_db
from app.models.file_record import FileRecord

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{job_id}", summary="Poll Celery task status")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Returns the status of a Celery task AND the associated file record.
    Frontend polls this to know when the file is ready.
    """
    result = AsyncResult(job_id, app=celery_app)

    task_info = {
        "job_id": job_id,
        "state": result.state,          # PENDING / STARTED / SUCCESS / FAILURE / RETRY
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "result": result.result if result.ready() and result.successful() else None,
        "error": str(result.result) if result.failed() else None,
    }

    # Also attach the DB record for convenience
    record = db.query(FileRecord).filter(FileRecord.job_id == job_id).first()
    if record:
        task_info["record"] = record.to_dict()
    else:
        task_info["record"] = None

    return task_info


@router.get("/by-record/{record_id}", summary="Get job status by record ID")
def get_job_by_record(record_id: str, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")

    if not record.job_id:
        return {"record": record.to_dict(), "job_id": None, "state": "no_job"}

    result = AsyncResult(record.job_id, app=celery_app)
    return {
        "record": record.to_dict(),
        "job_id": record.job_id,
        "state": result.state,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "error": str(result.result) if result.failed() else None,
    }
