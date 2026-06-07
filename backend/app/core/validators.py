
import re
from typing import Optional
from fastapi import HTTPException, status


def validate_email(email: str) -> str:
    email = email.strip().lower()
    
    # Email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    if len(email) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email too long"
        )
    
    return email


def validate_password(password: str) -> str:
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    if len(password) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password too long (max 128 characters)"
        )
    
    if not re.search(r'[A-Z]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )
    
    if not re.search(r'[a-z]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter"
        )
    
    if not re.search(r'\d', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one digit"
        )
    
    if not re.search(r'[^a-zA-Z0-9\s]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one special character"
        )
    
    return password


def sanitize_string(text: str, max_length: int = 1000) -> str:
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Trim whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_crop_name(crop: str) -> str:
    crop = sanitize_string(crop, max_length=100)
    
    # Only allow letters, spaces, and hyphens
    if not re.match(r'^[a-zA-Z\s\-]+$', crop):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid crop name. Only letters, spaces, and hyphens allowed"
        )
    
    return crop


def validate_city_name(city: str) -> str:
    city = sanitize_string(city, max_length=100)
    
    # Only allow letters, spaces, and hyphens
    if not re.match(r'^[a-zA-Z\s\-]+$', city):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid city name. Only letters, spaces, and hyphens allowed"
        )
    
    return city


def validate_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    
    phone = sanitize_string(phone, max_length=20)
    
    # Remove spaces and dashes
    phone = re.sub(r'[\s\-]', '', phone)
    
    # Check if it's a valid phone number (digits only, optionally starting with +)
    if not re.match(r'^\+?\d{10,15}$', phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    
    return phone


def validate_numeric_range(value: float, min_val: float, max_val: float, field_name: str) -> float:
    if value < min_val or value > max_val:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be between {min_val} and {max_val}"
        )
    
    return value
