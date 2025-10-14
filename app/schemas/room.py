from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RoomCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: Optional[bool] = False
    members: Optional[List[int]] = []  # User IDs to add to room

class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None

class RoomRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_private: bool
    owner_id: int
    created_at: datetime
    member_count: Optional[int] = None

    class Config:
        from_attributes = True

class RoomMemberCreate(BaseModel):
    user_id: int
    role: Optional[str] = "member"

class RoomMemberRead(BaseModel):
    id: int
    user_id: int
    room_id: int
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True
