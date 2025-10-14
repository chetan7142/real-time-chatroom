from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Text
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    profile_pic = Column(String(500), nullable=True)
    status = Column(String(20), default="offline")  # online, offline, away, busy
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    owned_rooms = relationship('Room', back_populates='owner')
    messages = relationship('Message', back_populates='user')
    files = relationship('File', back_populates='uploader')
    notifications = relationship('Notification', back_populates='user')
    room_memberships = relationship('RoomMember', back_populates='user')
    mentions = relationship('Mention', back_populates='mentioned_user')
