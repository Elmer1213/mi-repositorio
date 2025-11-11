from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from datetime import datetime, timezone
from app.database import Base
import enum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)


class UploadStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExcelUploadLog(Base):
    __tablename__ = "excel_upload_logs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, datetime.now(timezone.utc))
    status = Column(Enum(UploadStatusEnum), default=UploadStatusEnum.PENDING)
    total_rows = Column(Integer, default=0)
    successful_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    uploaded_by = Column(String(100), nullable=True)  
    
    # Puedes agregar usuario después