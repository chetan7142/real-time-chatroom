from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FileCreate(BaseModel):
    file_name: str
    file_type: str
    file_size: int

class FileRead(BaseModel):
    id: int
    message_id: Optional[int]
    uploader_id: int
    file_url: str
    file_name: str
    file_type: str
    file_size: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class FileUploadResponse(BaseModel):
    file_id: int
    upload_url: str
    expires_in: int
