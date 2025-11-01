from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import List, Optional, Dict, Any
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from app.core.exceptions import NotificationNotFoundError

async def create_notification(
    db: AsyncSession, 
    user_id: int, 
    type: str, 
    title: str, 
    content: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None
) -> Notification:
    """Create a new notification"""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        content=content,
        payload=payload
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification

async def get_user_notifications(
    db: AsyncSession, 
    user_id: int, 
    page: int = 1, 
    limit: int = 50,
    unread_only: bool = False
) -> List[Notification]:
    """Get notifications for a user with pagination"""
    offset = (page - 1) * limit
    query = select(Notification).where(Notification.user_id == user_id)
    
    if unread_only:
        query = query.where(Notification.is_read == False)
    
    result = await db.execute(
        query.order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()

async def get_unread_count(db: AsyncSession, user_id: int) -> int:
    """Get count of unread notifications for a user"""
    result = await db.execute(
        select(func.count(Notification.id))
        .where(Notification.user_id == user_id, Notification.is_read == False)
    )
    return result.scalar() or 0

async def mark_notification_read(
    db: AsyncSession, 
    notification_id: int, 
    user_id: int, 
    is_read: bool
) -> Notification:
    """Mark a notification as read/unread"""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise NotificationNotFoundError("Notification not found")
    
    notification.is_read = is_read
    await db.commit()
    await db.refresh(notification)
    return notification

async def mark_all_notifications_read(db: AsyncSession, user_id: int) -> int:
    """Mark all notifications as read for a user"""
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return result.rowcount

async def delete_notification(db: AsyncSession, notification_id: int, user_id: int) -> bool:
    """Delete a notification"""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise NotificationNotFoundError("Notification not found")
    
    await db.delete(notification)
    await db.commit()
    return True

async def create_mention_notification(
    db: AsyncSession, 
    mentioned_user_id: int, 
    message_id: int, 
    room_id: int,
    mentioner_username: str
) -> Notification:
    """Create a notification for a user mention"""
    return await create_notification(
        db=db,
        user_id=mentioned_user_id,
        type="mention",
        title=f"You were mentioned by {mentioner_username}",
        content=f"You were mentioned in a message",
        payload={
            "message_id": message_id,
            "room_id": room_id,
            "mentioner_username": mentioner_username
        }
    )

async def create_room_invite_notification(
    db: AsyncSession,
    user_id: int,
    room_id: int,
    room_name: str,
    inviter_username: str
) -> Notification:
    """Create a notification for a room invitation"""
    return await create_notification(
        db=db,
        user_id=user_id,
        type="room_invite",
        title=f"You were invited to {room_name}",
        content=f"{inviter_username} invited you to join the room",
        payload={
            "room_id": room_id,
            "room_name": room_name,
            "inviter_username": inviter_username
        }
    )
