from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(50), nullable=False)  # 'message', 'mention', 'room_invite', etc.
    title = Column(String(255), nullable=False)
    content = Column(String(500), nullable=True)
    payload = Column(JSON, nullable=True)  # Additional data like room_id, message_id
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship('User')
