from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.room import Room
from app.models.room_member import RoomMember, RoomRole
from app.models.user import User
from app.schemas.room import RoomCreate, RoomUpdate, RoomMemberCreate
from app.core.exceptions import RoomNotFoundError, UserNotFoundError, UnauthorizedError

async def create_room(db: AsyncSession, room_data: RoomCreate, owner_id: int) -> Room:
    """Create a new room and add the owner as admin"""
    # Create the room
    room = Room(
        name=room_data.name,
        description=room_data.description,
        is_private=room_data.is_private,
        owner_id=owner_id
    )
    db.add(room)
    await db.flush()  # Get the room ID
    
    # Add owner as room admin
    owner_membership = RoomMember(
        user_id=owner_id,
        room_id=room.id,
        role=RoomRole.OWNER
    )
    db.add(owner_membership)
    
    # Add other members if specified
    if room_data.members:
        for user_id in room_data.members:
            if user_id != owner_id:  # Don't add owner twice
                member = RoomMember(
                    user_id=user_id,
                    room_id=room.id,
                    role=RoomRole.MEMBER
                )
                db.add(member)
    
    await db.commit()
    await db.refresh(room)
    return room

async def get_room(db: AsyncSession, room_id: int) -> Optional[Room]:
    """Get a room by ID"""
    result = await db.execute(
        select(Room)
        .options(selectinload(Room.owner))
        .where(Room.id == room_id)
    )
    return result.scalar_one_or_none()

async def get_user_rooms(db: AsyncSession, user_id: int) -> List[Room]:
    """Get all rooms a user is a member of"""
    result = await db.execute(
        select(Room)
        .join(RoomMember)
        .where(RoomMember.user_id == user_id)
        .options(selectinload(Room.owner))
    )
    return result.scalars().all()

async def update_room(db: AsyncSession, room_id: int, room_data: RoomUpdate, user_id: int) -> Optional[Room]:
    """Update room details (only by owner or admin)"""
    room = await get_room(db, room_id)
    if not room:
        raise RoomNotFoundError("Room not found")
    
    # Check if user has permission to update
    if not await user_can_manage_room(db, room_id, user_id):
        raise UnauthorizedError("You don't have permission to update this room")
    
    # Update fields
    if room_data.name is not None:
        room.name = room_data.name
    if room_data.description is not None:
        room.description = room_data.description
    if room_data.is_private is not None:
        room.is_private = room_data.is_private
    
    await db.commit()
    await db.refresh(room)
    return room

async def delete_room(db: AsyncSession, room_id: int, user_id: int) -> bool:
    """Delete a room (only by owner)"""
    room = await get_room(db, room_id)
    if not room:
        raise RoomNotFoundError("Room not found")
    
    if room.owner_id != user_id:
        raise UnauthorizedError("Only room owner can delete the room")
    
    await db.delete(room)
    await db.commit()
    return True

async def add_room_member(db: AsyncSession, room_id: int, member_data: RoomMemberCreate, user_id: int) -> RoomMember:
    """Add a member to a room (only by room admin/owner)"""
    # Check if user has permission to add members
    if not await user_can_manage_room(db, room_id, user_id):
        raise UnauthorizedError("You don't have permission to add members to this room")
    
    # Check if user exists
    user_result = await db.execute(select(User).where(User.id == member_data.user_id))
    if not user_result.scalar_one_or_none():
        raise UserNotFoundError("User not found")
    
    # Check if user is already a member
    existing_member = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == member_data.user_id
        )
    )
    if existing_member.scalar_one_or_none():
        raise ValueError("User is already a member of this room")
    
    # Add member
    member = RoomMember(
        user_id=member_data.user_id,
        room_id=room_id,
        role=RoomRole(member_data.role.upper())
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member

async def remove_room_member(db: AsyncSession, room_id: int, member_user_id: int, user_id: int) -> bool:
    """Remove a member from a room (only by room admin/owner)"""
    # Check if user has permission to remove members
    if not await user_can_manage_room(db, room_id, user_id):
        raise UnauthorizedError("You don't have permission to remove members from this room")
    
    # Find the membership
    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == member_user_id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise ValueError("User is not a member of this room")
    
    await db.delete(member)
    await db.commit()
    return True

async def get_room_members(db: AsyncSession, room_id: int) -> List[RoomMember]:
    """Get all members of a room"""
    result = await db.execute(
        select(RoomMember)
        .options(selectinload(RoomMember.user))
        .where(RoomMember.room_id == room_id)
    )
    return result.scalars().all()

async def user_can_manage_room(db: AsyncSession, room_id: int, user_id: int) -> bool:
    """Check if user can manage room (owner or admin)"""
    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
            RoomMember.role.in_([RoomRole.OWNER, RoomRole.ADMIN])
        )
    )
    return result.scalar_one_or_none() is not None

async def user_is_room_member(db: AsyncSession, room_id: int, user_id: int) -> bool:
    """Check if user is a member of the room"""
    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id
        )
    )
    return result.scalar_one_or_none() is not None
