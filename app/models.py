from sqlalchemy import Column, Boolean, Integer, String, DateTime, Text, Enum as SQLEnum, func
from datetime import datetime, timezone
from app.database import Base
import enum

#------------------------
# Enum de estado de carga
#------------------------
class UploadStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
#-----------------------------------------------------------------
# Modelo de usuario (si lo necesitas para relacionar más adelante)
#------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    
    is_active = Column(Boolean, default=True)

#----------------------------------------
# Modelo principal para registro de cargas
#-----------------------------------------
class ExcelUploadLog(Base):
    """
    Modelo para registrar el historial de cargas de Excel
    """
    __tablename__ = "excel_upload_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    status = Column(
        SQLEnum(UploadStatusEnum),
        default=UploadStatusEnum.PENDING,
        nullable=False,
        index=True
    )

    total_rows = Column(Integer, default=0, nullable=False)
    successful_rows = Column(Integer, default=0, nullable=False)
    failed_rows = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ExcelUploadLog(id={self.id}, filename='{self.filename}', status={self.status})>"

    @property
    def success_rate(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return round((self.successful_rows / self.total_rows) * 100, 2)
