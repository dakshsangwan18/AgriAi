from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.database import get_db
from app.models.user import User
from app.models.user_crop import UserCrop
from app.api.v1.endpoints.auth import get_current_user
from pydantic import BaseModel, Field


router = APIRouter(tags=["profile"])


# Schemas
class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    location: str | None = None
    preferred_language: str | None = Field(None, description="en, hi, mr, pa, ta")
    notification_enabled: bool | None = None
    farm_size: float | None = Field(None, description="Farm size in acres")
    farm_location_lat: float | None = None
    farm_location_lon: float | None = None
    sms_enabled: bool | None = None
    whatsapp_enabled: bool | None = None


class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    phone: str | None
    location: str | None
    preferred_language: str
    notification_enabled: bool
    farm_size: float | None
    sms_enabled: bool
    whatsapp_enabled: bool
    created_at: str

    class Config:
        from_attributes = True


class UserCropCreate(BaseModel):
    crop: str = Field(..., description="Crop name")
    quantity_kg: float | None = Field(None, description="Quantity in kilograms")
    harvest_date: date | None = Field(None, description="Expected harvest date")


class UserCropUpdate(BaseModel):
    quantity_kg: float | None = None
    harvest_date: date | None = None
    is_active: bool | None = None


class UserCropResponse(BaseModel):
    id: str
    crop: str
    quantity_kg: float | None
    harvest_date: date | None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    
    return current_user


@router.patch("/me", response_model=UserProfileResponse)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Update fields
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/crops", response_model=List[UserCropResponse])
async def get_my_crops(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    crops = db.query(UserCrop).filter(
        UserCrop.user_id == current_user.id
    ).order_by(UserCrop.created_at.desc()).all()
    
    return crops


@router.post("/crops", response_model=UserCropResponse, status_code=status.HTTP_201_CREATED)
async def add_my_crop(
    crop: UserCropCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    db_crop = UserCrop(
        user_id=current_user.id,
        crop=crop.crop.lower(),
        quantity_kg=crop.quantity_kg,
        harvest_date=crop.harvest_date
    )
    
    db.add(db_crop)
    db.commit()
    db.refresh(db_crop)
    
    return db_crop


@router.patch("/crops/{crop_id}", response_model=UserCropResponse)
async def update_my_crop(
    crop_id: str,
    crop_update: UserCropUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    crop = db.query(UserCrop).filter(
        UserCrop.id == crop_id,
        UserCrop.user_id == current_user.id
    ).first()
    
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    
    # Update fields
    update_data = crop_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(crop, field, value)
    
    db.commit()
    db.refresh(crop)
    
    return crop


@router.delete("/crops/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_crop(
    crop_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    crop = db.query(UserCrop).filter(
        UserCrop.id == crop_id,
        UserCrop.user_id == current_user.id
    ).first()
    
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    
    db.delete(crop)
    db.commit()
    
    return None
