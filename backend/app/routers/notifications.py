from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Annotated
from datetime import datetime, timezone
import json
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.logging_config import logger

from app.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.api.v1.endpoints.auth import get_current_active_user
from pydantic import BaseModel


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# Schemas
class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    is_read: bool
    priority: str
    created_at: datetime
    read_at: datetime | None
    extra_data: dict | None  # Renamed from metadata
    
    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    type: str
    title: str
    message: str
    priority: str = "normal"
    extra_data: dict | None = None  # Renamed from metadata


class MarkReadRequest(BaseModel):
    notification_ids: List[int]


@router.get("/", response_model=List[NotificationResponse])
@limiter.limit("200/hour")
async def get_notifications(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    unread_only: bool = False,
    limit: int = 50
):
    
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(desc(Notification.created_at)).limit(limit).all()
    
    # Parse extra_data JSON strings
    for notif in notifications:
        if notif.extra_data:
            try:
                notif.extra_data = json.loads(notif.extra_data)
            except (json.JSONDecodeError, TypeError):
                notif.extra_data = None
    
    return notifications


@router.get("/unread-count")
@limiter.limit("500/hour")  # Frontend polls this frequently
async def get_unread_count(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    
    count = db.query(Notification).filter(
        and_(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    ).count()
    
    return {"unread_count": count}


@router.post("/mark-read")
@limiter.limit("100/hour")
async def mark_notifications_read(
    request: Request,
    mark_request: MarkReadRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    
    db.query(Notification).filter(
        and_(
            Notification.id.in_(mark_request.notification_ids),
            Notification.user_id == current_user.id
        )
    ).update({
        "is_read": True,
        "read_at": datetime.now(timezone.utc)
    }, synchronize_session=False)
    
    db.commit()
    
    return {"message": f"Marked {len(mark_request.notification_ids)} notifications as read"}


@router.post("/mark-all-read")
@limiter.limit("20/hour")
async def mark_all_read(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    
    result = db.query(Notification).filter(
        and_(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    ).update({
        "is_read": True,
        "read_at": datetime.now(timezone.utc)
    }, synchronize_session=False)
    
    db.commit()
    
    return {"message": f"Marked {result} notifications as read"}


@router.delete("/{notification_id}")
@limiter.limit("100/hour")
async def delete_notification(
    request: Request,
    notification_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted"}


