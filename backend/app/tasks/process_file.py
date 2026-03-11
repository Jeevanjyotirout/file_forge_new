"""
FileForge – Celery background tasks
"""
import logging
import os
import shutil
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import settings
from app.database import SessionLocal
from app.models.file_record import FileRecord
from app.services.converter import convert_file

logger = logging.getLogger(__name__)


def _get_db() -> Session:
    return SessionLocal()


@celery_app.task(
    bind=True,
    name="process_file",
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def process_file_task(self, record_id: str):
    """
    Main processing task:
    1. Load file record from DB
    2. Run conversion / processing
    3. Update record with output path or error
    """
    db = _get_db()
    try:
        record: FileRecord = db.query(FileRecord).filter(FileRecord.id == record_id).first()
        if not record:
            logger.error(f"[task:{self.request.id}] FileRecord {record_id} not found – aborting.")
            return {"status": "error", "detail": "record not found"}

        logger.info(f"[task:{self.request.id}] Starting processing: {record.original_name} | op={record.operation}")

        # Mark as processing
        record.status = "processing"
        record.job_id = self.request.id
        db.commit()

        # Resolve paths
        input_path  = os.path.join(settings.UPLOAD_DIR, record.stored_name)
        output_name = f"{record.id}_{Path(record.original_name).stem}_output"
        output_path = os.path.join(settings.OUTPUT_DIR, output_name)

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file missing: {input_path}")

        # Perform conversion / processing
        result_path = convert_file(
            input_path=input_path,
            output_base_path=output_path,
            operation=record.operation or "copy",
            original_name=record.original_name,
        )

        result_filename = os.path.basename(result_path)

        # Update record
        record.status      = "done"
        record.output_name = result_filename
        record.expires_at  = datetime.utcnow() + timedelta(seconds=settings.FILE_TTL_SECONDS)
        record.updated_at  = datetime.utcnow()
        db.commit()

        logger.info(f"[task:{self.request.id}] Done: {result_filename}")
        return {"status": "done", "output_name": result_filename}

    except SoftTimeLimitExceeded:
        logger.warning(f"[task:{self.request.id}] Soft time limit exceeded for {record_id}")
        if record:
            record.status    = "error"
            record.error_msg = "Processing timed out"
            db.commit()
        return {"status": "error", "detail": "timeout"}

    except Exception as exc:
        logger.exception(f"[task:{self.request.id}] Processing failed for {record_id}: {exc}")
        try:
            if record:
                record.status    = "error"
                record.error_msg = str(exc)[:1024]
                db.commit()
        except Exception:
            pass
        # Celery retry
        raise self.retry(exc=exc)

    finally:
        db.close()


@celery_app.task(name="cleanup_expired_files")
def cleanup_expired_files():
    """Periodic task – removes expired files and records."""
    db = _get_db()
    try:
        now = datetime.utcnow()
        expired = (
            db.query(FileRecord)
            .filter(FileRecord.expires_at < now, FileRecord.purged == False)  # noqa: E712
            .all()
        )
        count = 0
        for rec in expired:
            # Remove output file
            if rec.output_name:
                p = os.path.join(settings.OUTPUT_DIR, rec.output_name)
                if os.path.exists(p):
                    os.remove(p)
                    logger.debug(f"Removed output: {p}")
            # Remove upload file
            if rec.stored_name:
                p = os.path.join(settings.UPLOAD_DIR, rec.stored_name)
                if os.path.exists(p):
                    os.remove(p)
                    logger.debug(f"Removed upload: {p}")
            rec.purged = True
            count += 1
        db.commit()
        logger.info(f"Cleanup: purged {count} expired records.")
        return {"purged": count}
    except Exception as exc:
        logger.exception(f"Cleanup task failed: {exc}")
        return {"error": str(exc)}
    finally:
        db.close()


# Schedule periodic cleanup every 30 minutes
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "cleanup-expired-files": {
        "task": "cleanup_expired_files",
        "schedule": 1800,   # every 30 minutes
    }
}
