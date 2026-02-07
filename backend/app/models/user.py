from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    # User preferences
    favorite_crops = Column(JSON, nullable=True, default=list)  # ["Rice", "Wheat"]
    preferred_language = Column(String, default="en")  # en, hi, ta, te, bn
    notification_enabled = Column(Boolean, default=True)
    
    # New user account fields
    user_type = Column(String, default="FARMER")  # FARMER, TRADER, ADMIN
    farm_size = Column(Integer, nullable=True)  # In acres
    farm_location_lat = Column(Integer, nullable=True)
    farm_location_lon = Column(Integer, nullable=True)
    language_preference = Column(String, default="en")
    sms_enabled = Column(Boolean, default=False)
    whatsapp_enabled = Column(Boolean, default=False)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    # Password reset
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # OAuth and Login Tracking (Production-grade security)
    oauth_provider = Column(String, nullable=True)  # google, github, microsoft
    oauth_id = Column(String, nullable=True, index=True)  # Provider's user ID
    profile_picture_url = Column(String, nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String, nullable=True)
    login_count = Column(Integer, default=0)
    login_method = Column(String, default="email")  # email, google, github
    email_verified = Column(Boolean, default=False)  # Separate from is_verified for granular control
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    price_alerts = relationship("PriceAlert", back_populates="user", cascade="all, delete-orphan")
    user_crops = relationship("UserCrop", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(email={self.email}, name={self.full_name})>"
