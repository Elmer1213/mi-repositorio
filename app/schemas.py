from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


class ExcelPreviewRow(BaseModel):
    row_number: int
    name: str
    email: str
    is_valid: bool
    errors: List[str] = []


class ExcelPreviewResponse(BaseModel):
    total_rows: int
    preview_rows: List[ExcelPreviewRow]
    columns: List[str]
    has_errors: bool


class UploadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadProgressResponse(BaseModel):
    current: int
    total: int
    percentage: float
    status: str


class UploadLogResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    status: str
    total_rows: int
    successful_rows: int
    failed_rows: int
    error_message: Optional[str] = None

    class Config:
        from_attributes = True