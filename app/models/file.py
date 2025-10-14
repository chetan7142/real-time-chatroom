from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, BigInteger
from sqlalchemy.orm import relationship
from app.db.base import Base

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey('messages.id', ondelete='CASCADE'), nullable=True)
    uploader_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    uploader = relationship('User')
    message = relationship('Message')
