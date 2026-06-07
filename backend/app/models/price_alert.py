from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    crop = Column(String(50), nullable=False, index=True)
    city = Column(String(100), nullable=False)
    alert_type = Column(String(20), nullable=False)  # 'ABOVE', 'BELOW', 'CHANGE'
    threshold_price = Column(Float, nullable=True)  # For ABOVE/BELOW alerts
    threshold_percentage = Column(Float, nullable=True)  # For CHANGE alerts (e.g., 5.0 for 5%)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    notification_method = Column(String(20), default='EMAIL', nullable=False)  # EMAIL, SMS, BOTH
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="price_alerts")

    def __repr__(self):
        return f"<PriceAlert(id={self.id}, crop={self.crop}, type={self.alert_type}, user={self.user_id})>"
