from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from app.models.message import Message
from app.models.mention import Mention
from app.models.user import User
from app.schemas.message import MessageCreate, MessageUpdate
from app.core.exceptions import MessageNotFoundError, UnauthorizedError
from app.services.room_service import user_is_room_member

async def create_message(db: AsyncSession, message_data: MessageCreate, room_id: int, user_id: int) -> Message:
    """Create a new message in a room"""
    # Check if user is a member of the room
    if not await user_is_room_member(db, room_id, user_id):
        raise UnauthorizedError("You are not a member of this room")
    
    # Create the message
    message = Message(
        content=message_data.content,
        room_id=room_id,
        user_id=user_id
    )
    db.add(message)
    await db.flush()  # Get the message ID
    
    # Create mentions if any
    if message_data.mentions:
        for mentioned_user_id in message_data.mentions:
            mention = Mention(
                message_id=message.id,
                mentioned_user_id=mentioned_user_id
            )
            db.add(mention)
    
    await db.commit()
    await db.refresh(message)
    return message

async def get_messages(db: AsyncSession, room_id: int, page: int = 1, limit: int = 50) -> List[Message]:
    """Get messages from a room with pagination"""
    offset = (page - 1) * limit
    result = await db.execute(
        select(Message)
        .options(selectinload(Message.user))
        .where(Message.room_id == room_id, Message.is_deleted == False)
        .order_by(desc(Message.created_at))
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()

async def get_message(db: AsyncSession, message_id: int) -> Optional[Message]:
    """Get a specific message by ID"""
    result = await db.execute(
        select(Message)
        .options(selectinload(Message.user))
        .where(Message.id == message_id)
    )
    return result.scalar_one_or_none()

async def update_message(db: AsyncSession, message_id: int, message_data: MessageUpdate, user_id: int) -> Optional[Message]:
    """Update a message (only by the author)"""
    message = await get_message(db, message_id)
    if not message:
        raise MessageNotFoundError("Message not found")
    
    if message.user_id != user_id:
        raise UnauthorizedError("You can only edit your own messages")
    
    message.content = message_data.content
    message.edited_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(message)
    return message

async def delete_message(db: AsyncSession, message_id: int, user_id: int) -> bool:
    """Soft delete a message (only by the author or room admin)"""
    message = await get_message(db, message_id)
    if not message:
        raise MessageNotFoundError("Message not found")
    
    # Check if user is the author or has admin rights
    if message.user_id != user_id:
        # Check if user is room admin
        from app.services.room_service import user_can_manage_room
        if not await user_can_manage_room(db, message.room_id, user_id):
            raise UnauthorizedError("You can only delete your own messages")
    
    message.is_deleted = True
    await db.commit()
    return True

async def get_room_message_count(db: AsyncSession, room_id: int) -> int:
    """Get total message count for a room"""
    result = await db.execute(
        select(func.count(Message.id))
        .where(Message.room_id == room_id, Message.is_deleted == False)
    )
    return result.scalar() or 0
