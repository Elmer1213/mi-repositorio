from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

#------------------------
#        USERS
#-----------------------
class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True
        
#-----------------------------
#         ENUMS
#-----------------------------
class UploadStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    
#-----------------------------
#       EXCEL PREVIEW
#----------------------------


class ExcelPreviewRow(BaseModel):
    
    """Representa una fila del Excel con su validaciones"""
    
    row_number: int
    name: str
    email: str
    is_valid: bool
    errors: List[str] = []
    
class Config:
    from_attributes = True


class ExcelPreviewResponse(BaseModel):
    
    """ Respuesta del endpoint de preview"""
    
    total_rows: int
    preview_rows: List[ExcelPreviewRow]
    columns: List[str]
    has_errors: bool
    sheet_name: Optional[str] = None
    
class Config:
    from_attributes = True
    
#---------------------------
#     VALIDACIÓN
#---------------------------

class ValidationResponse(BaseModel):
    
    """Respuesta del endpoint de validación"""
    
    message: str
    filename: str
    size_ok: bool
    file_id: str
    sheets: List[str]
    total_sheets: int
        
#----------------------------
#      UPLOAD
#----------------------------

class UploadResponse(BaseModel):
    """
    Respuesta del endpoint de upload
    """
    message: str
    upload_id: int
    total_rows: int


class UploadProgressResponse(BaseModel):
    """
    Respuesta de progreso (WebSocket)
    """
    current: Optional[int] = None
    total: Optional[int] = None
    percentage: Optional[float] = None
    successful: Optional[int] = None
    failed: Optional[int] = None
    status: Optional[str] = None
    error: Optional[str] = None


# ---------------------
#         LOGS 
# --------------------

class UploadLogResponse(BaseModel):
    """
    Respuesta del historial de cargas
    """
    id: int
    filename: str
    uploaded_at: datetime
    status: UploadStatusEnum
    total_rows: int
    successful_rows: Optional[int] = None
    failed_rows: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------
#          STATS
# ---------------------

class ChartData(BaseModel):
    """
    Datos para gráficos con Chart.js
    """
    labels: List[str]
    successful: List[int]
    failed: List[int]
    dates: List[str]


class UploadStatsResponse(BaseModel):
    """
    Estadísticas generales para el dashboard
    """
    total_uploads: int
    total_successful: int
    total_failed: int
    chart_data: ChartData