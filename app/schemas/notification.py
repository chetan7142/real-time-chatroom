from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class NotificationCreate(BaseModel):
    user_id: int
    type: str
    title: str
    content: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class NotificationRead(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    content: Optional[str]
    payload: Optional[Dict[str, Any]]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationUpdate(BaseModel):
    is_read: bool
