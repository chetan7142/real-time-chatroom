from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.notification import NotificationRead, NotificationUpdate
from app.schemas.user import UserRead
from app.db.session import get_db
from app.api.deps import get_current_user
from app.services.notification_service import (
    get_user_notifications, mark_notification_read, mark_all_notifications_read,
    create_notification, get_unread_count
)
from app.core.exceptions import NotificationNotFoundError

router = APIRouter()

@router.get('/', response_model=List[NotificationRead])
async def get_notifications_endpoint(
    page: int = 1,
    limit: int = 50,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Get notifications for the current user"""
    notifications = await get_user_notifications(db, current_user.id, page, limit, unread_only)
    return notifications

@router.get('/unread-count')
async def get_unread_count_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Get count of unread notifications"""
    count = await get_unread_count(db, current_user.id)
    return {"unread_count": count}

@router.put('/{notification_id}', response_model=NotificationRead)
async def mark_notification_read_endpoint(
    notification_id: int,
    notification_data: NotificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Mark a notification as read/unread"""
    try:
        notification = await mark_notification_read(db, notification_id, current_user.id, notification_data.is_read)
        return notification
    except NotificationNotFoundError:
        raise HTTPException(status_code=404, detail="Notification not found")

@router.put('/mark-all-read')
async def mark_all_notifications_read_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Mark all notifications as read"""
    count = await mark_all_notifications_read(db, current_user.id)
    return {"message": f"Marked {count} notifications as read"}
