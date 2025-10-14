from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Mention(Base):
    __tablename__ = "mentions"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    mentioned_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship('Message')
    mentioned_user = relationship('User', foreign_keys=[mentioned_user_id])
