"""
FileForge – Storage service
Handles saving / deleting files from disk.
"""
import logging
import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff",
    ".pdf", ".txt", ".csv", ".json", ".xml",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".tar", ".gz",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
}


def is_extension_allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


async def save_upload(file: UploadFile) -> tuple[str, int]:
    """
    Save an uploaded file to UPLOAD_DIR.
    Returns (stored_filename, size_bytes).
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    ext           = Path(file.filename or "upload").suffix.lower()
    stored_name   = f"{uuid.uuid4()}{ext}"
    dest_path     = os.path.join(settings.UPLOAD_DIR, stored_name)

    size = 0
    with open(dest_path, "wb") as dest:
        while True:
            chunk = await file.read(1024 * 1024)  # 1 MB chunks
            if not chunk:
                break
            if size + len(chunk) > settings.MAX_UPLOAD_BYTES:
                dest.close()
                os.remove(dest_path)
                raise ValueError(
                    f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_MB} MB"
                )
            dest.write(chunk)
            size += len(chunk)

    logger.info(f"Saved upload: {stored_name} ({size} bytes)")
    return stored_name, size


def delete_file(directory: str, filename: str) -> bool:
    """Delete a file from disk, return True if deleted."""
    path = os.path.join(directory, filename)
    if os.path.exists(path):
        os.remove(path)
        logger.info(f"Deleted: {path}")
        return True
    return False


def output_file_path(filename: str) -> str:
    return os.path.join(settings.OUTPUT_DIR, filename)


def output_file_exists(filename: str) -> bool:
    return os.path.exists(output_file_path(filename))
