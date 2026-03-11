"""
FileForge – SQLAlchemy ORM models
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from app.database import Base


def _gen_uuid() -> str:
    return str(uuid.uuid4())


class FileRecord(Base):
    __tablename__ = "file_records"

    id           = Column(String(36), primary_key=True, default=_gen_uuid)
    original_name = Column(String(512), nullable=False)
    stored_name  = Column(String(512), nullable=False)          # name on disk
    mime_type    = Column(String(128), nullable=True)
    size_bytes   = Column(Integer, default=0)

    # Conversion / processing options
    operation    = Column(String(64), nullable=True)             # e.g. "pdf-to-docx"
    output_name  = Column(String(512), nullable=True)

    # Job tracking
    job_id       = Column(String(36), nullable=True, index=True) # Celery task id
    status       = Column(String(32), default="pending")         # pending|processing|done|error
    error_msg    = Column(Text, nullable=True)

    # Timestamps
    created_at   = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at   = Column(DateTime, nullable=True)

    # Soft-delete / purge flag
    purged       = Column(Boolean, default=False)

    def to_dict(self) -> dict:
        return {
            "id":            self.id,
            "original_name": self.original_name,
            "mime_type":     self.mime_type,
            "size_bytes":    self.size_bytes,
            "operation":     self.operation,
            "output_name":   self.output_name,
            "job_id":        self.job_id,
            "status":        self.status,
            "error_msg":     self.error_msg,
            "created_at":    self.created_at.isoformat() if self.created_at else None,
            "updated_at":    self.updated_at.isoformat() if self.updated_at else None,
            "expires_at":    self.expires_at.isoformat() if self.expires_at else None,
        }
