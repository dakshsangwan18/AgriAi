from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Date, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class UserCrop(Base):
    __tablename__ = "user_crops"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    crop = Column(String(50), nullable=False, index=True)
    quantity_kg = Column(Float, nullable=True)
    harvest_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="user_crops")

    def __repr__(self):
        return f"<UserCrop(id={self.id}, user={self.user_id}, crop={self.crop}, qty={self.quantity_kg})>"
