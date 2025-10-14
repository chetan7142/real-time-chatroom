from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class MessageCreate(BaseModel):
    content: str
    mentions: Optional[List[int]] = []  # User IDs to mention

class MessageUpdate(BaseModel):
    content: str

class MessageRead(BaseModel):
    id: int
    room_id: int
    user_id: int
    content: str
    created_at: datetime
    edited_at: Optional[datetime]
    is_deleted: bool
    username: Optional[str] = None  # For display purposes
    files: Optional[List[dict]] = []  # Attached files

    class Config:
        from_attributes = True

class MessageWithUser(BaseModel):
    id: int
    room_id: int
    user_id: int
    content: str
    created_at: datetime
    edited_at: Optional[datetime]
    is_deleted: bool
    user: dict  # User information

    class Config:
        from_attributes = True
