from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.room import RoomCreate, RoomRead, RoomUpdate, RoomMemberCreate, RoomMemberRead
from app.schemas.user import UserRead
from app.db.session import get_db
from app.api.deps import get_current_user
from app.services.room_service import (
    create_room, get_user_rooms, get_room, update_room, delete_room,
    add_room_member, remove_room_member, get_room_members
)
from app.core.exceptions import RoomNotFoundError, UserNotFoundError, UnauthorizedError

router = APIRouter()

@router.post('/', response_model=RoomRead, status_code=201)
async def create_room_endpoint(
    room_in: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Create a new room"""
    try:
        room = await create_room(db, room_in, current_user.id)
        return room
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/', response_model=List[RoomRead])
async def get_user_rooms_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Get all rooms for the current user"""
    rooms = await get_user_rooms(db, current_user.id)
    return rooms

@router.get('/{room_id}', response_model=RoomRead)
async def get_room_endpoint(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Get a specific room"""
    room = await get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@router.put('/{room_id}', response_model=RoomRead)
async def update_room_endpoint(
    room_id: int,
    room_data: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Update room details"""
    try:
        room = await update_room(db, room_id, room_data, current_user.id)
        return room
    except RoomNotFoundError:
        raise HTTPException(status_code=404, detail="Room not found")
    except UnauthorizedError:
        raise HTTPException(status_code=403, detail="You don't have permission to update this room")

@router.delete('/{room_id}')
async def delete_room_endpoint(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Delete a room"""
    try:
        await delete_room(db, room_id, current_user.id)
        return {"message": "Room deleted successfully"}
    except RoomNotFoundError:
        raise HTTPException(status_code=404, detail="Room not found")
    except UnauthorizedError:
        raise HTTPException(status_code=403, detail="Only room owner can delete the room")
