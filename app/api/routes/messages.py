from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.message import MessageCreate, MessageRead, MessageUpdate, MessageWithUser
from app.schemas.user import UserRead
from app.db.session import get_db
from app.api.deps import get_current_user
from app.services.message_service import (
    create_message, get_messages, get_message, update_message, delete_message
)
from app.core.exceptions import MessageNotFoundError, UnauthorizedError

router = APIRouter()

@router.get('/{room_id}', response_model=List[MessageWithUser])
async def get_messages_endpoint(
    room_id: int,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Get messages from a room with pagination"""
    messages = await get_messages(db, room_id, page, limit)
    return messages

@router.post('/{room_id}', response_model=MessageWithUser, status_code=201)
async def create_message_endpoint(
    room_id: int,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Create a new message in a room"""
    try:
        message = await create_message(db, message_data, room_id, current_user.id)
        return message
    except UnauthorizedError:
        raise HTTPException(status_code=403, detail="You are not a member of this room")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/{room_id}/{message_id}', response_model=MessageWithUser)
async def get_message_endpoint(
    room_id: int,
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Get a specific message"""
    message = await get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@router.put('/{room_id}/{message_id}', response_model=MessageWithUser)
async def update_message_endpoint(
    room_id: int,
    message_id: int,
    message_data: MessageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Update a message"""
    try:
        message = await update_message(db, message_id, message_data, current_user.id)
        return message
    except MessageNotFoundError:
        raise HTTPException(status_code=404, detail="Message not found")
    except UnauthorizedError:
        raise HTTPException(status_code=403, detail="You can only edit your own messages")

@router.delete('/{room_id}/{message_id}')
async def delete_message_endpoint(
    room_id: int,
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Delete a message"""
    try:
        await delete_message(db, message_id, current_user.id)
        return {"message": "Message deleted successfully"}
    except MessageNotFoundError:
        raise HTTPException(status_code=404, detail="Message not found")
    except UnauthorizedError:
        raise HTTPException(status_code=403, detail="You can only delete your own messages")
