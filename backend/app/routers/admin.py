
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.user import User
from app.models.agent_analysis import AgentAnalysis
from app.models.prediction_history import PredictionHistory
from app.models.audit_log import AuditLog
from app.api.v1.endpoints.auth import get_current_active_user
from app.core.cache import cache_manager
from app.core.audit import log_admin_action

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# Pydantic models
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    location: Optional[str]
    favorite_crops: Optional[List[str]]

    class Config:
        from_attributes = True


class PlatformStats(BaseModel):
    total_users: int
    active_users: int
    total_analyses: int
    analyses_today: int
    total_predictions: int


class SystemLog(BaseModel):
    id: int
    timestamp: datetime
    level: str
    action: str
    user_email: Optional[str]


class AuditLogResponse(BaseModel):
    id: int
    admin_email: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Any]
    ip_address: Optional[str]
    status: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


def verify_admin(current_user: User = Depends(get_current_active_user)):
    
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/stats", response_model=PlatformStats)
@limiter.limit("30/minute")
async def get_platform_stats(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    
    # Total users
    total_users = db.query(func.count(User.id)).scalar()
    
    # Active users (logged in last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    active_users = db.query(func.count(User.id)).filter(
        User.is_active == True,
        User.last_login >= thirty_days_ago,
    ).scalar()
    
    # Total agent analyses
    total_analyses = db.query(func.count(AgentAnalysis.id)).scalar()
    
    # Analyses today
    today = datetime.now().date()
    analyses_today = db.query(func.count(AgentAnalysis.id)).filter(
        func.date(AgentAnalysis.created_at) == today
    ).scalar()
    
    # Total predictions
    total_predictions = db.query(func.count(PredictionHistory.id)).scalar()
    
    return PlatformStats(
        total_users=total_users or 0,
        active_users=active_users or 0,
        total_analyses=total_analyses or 0,
        analyses_today=analyses_today or 0,
        total_predictions=total_predictions or 0
    )


@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    
    query = db.query(User)
    
    # Search filter
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )
    
    # Get total count
    total = query.count()
    
    # Paginate
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    
    return users


@router.put("/users/{user_id}/status")
@limiter.limit("10/minute")
async def update_user_status(
    request: Request,
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deactivating themselves
    if user.id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate your own account"
        )
    
    old_status = user.is_active
    user.is_active = is_active
    db.commit()
    
    # Audit log
    log_admin_action(
        db=db,
        admin=admin,
        action="USER_STATUS_CHANGED",
        resource_type="user",
        resource_id=str(user_id),
        details={
            "user_email": user.email,
            "old_status": old_status,
            "new_status": is_active
        },
        request=request
    )
    
    return {
        "message": f"User {'activated' if is_active else 'deactivated'} successfully",
        "user_id": user_id,
        "is_active": is_active
    }


@router.delete("/users/{user_id}")
@limiter.limit("5/minute")
async def delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if user.id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )
    
    user_email = user.email
    db.delete(user)
    db.commit()
    
    # Audit log
    log_admin_action(
        db=db,
        admin=admin,
        action="USER_DELETED",
        resource_type="user",
        resource_id=str(user_id),
        details={"user_email": user_email},
        request=request
    )
    
    return {
        "message": "User deleted successfully",
        "user_id": user_id
    }


@router.get("/logs")
async def get_system_logs(
    limit: int = Query(50, ge=1, le=500),
    level: Optional[str] = Query(None, pattern="^(info|warning|error)$"),
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    
    # For now, return recent analyses as activity logs
    # In production, you'd have a dedicated logs table
    
    query = db.query(
        AgentAnalysis.id,
        AgentAnalysis.created_at.label('timestamp'),
        AgentAnalysis.crop,
        AgentAnalysis.city,
        User.email
    ).join(User, AgentAnalysis.user_id == User.id, isouter=True)
    
    logs = query.order_by(desc(AgentAnalysis.created_at)).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "level": "info",
            "action": f"Crop analysis: {log.crop} in {log.city}",
            "user": log.email or "System"
        }
        for log in logs
    ]


@router.get("/health")
async def admin_health_check(admin: User = Depends(verify_admin)):
    
    return {
        "status": "healthy",
        "admin_access": True,
        "admin_user": admin.email
    }


@router.get("/cache/stats")
async def get_cache_stats(admin: User = Depends(verify_admin)):
    
    stats = cache_manager.get_stats()
    return {
        "cache": stats,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/cache/clear/{namespace}")
@limiter.limit("10/minute")
async def clear_cache_namespace(
    request: Request,
    namespace: str,
    pattern: str = "*",
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    
    deleted = cache_manager.invalidate_pattern(namespace, pattern)
    
    # Audit log
    log_admin_action(
        db=db,
        admin=admin,
        action="CACHE_CLEARED",
        resource_type="cache",
        resource_id=namespace,
        details={"pattern": pattern, "keys_deleted": deleted},
        request=request
    )
    
    return {
        "success": True,
        "namespace": namespace,
        "pattern": pattern,
        "keys_deleted": deleted
    }


@router.post("/cache/clear-all")
@limiter.limit("3/hour")
async def clear_all_cache(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    
    total_deleted = 0
    namespaces = ["weather:current", "weather:forecast", "prices:prediction"]
    
    for namespace in namespaces:
        deleted = cache_manager.invalidate_pattern(namespace.split(":")[0], "*")
        total_deleted += deleted
    
    # Audit log - critical action
    log_admin_action(
        db=db,
        admin=admin,
        action="ALL_CACHE_CLEARED",
        resource_type="cache",
        resource_id="all",
        details={
            "total_keys_deleted": total_deleted,
            "namespaces": namespaces
        },
        request=request
    )
    
    return {
        "success": True,
        "total_keys_deleted": total_deleted,
        "namespaces_cleared": namespaces
    }


@router.get("/audit-logs", response_model=List[AuditLogResponse])
@limiter.limit("30/minute")
async def get_audit_logs(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    # Single JOIN avoids N+1 lookup of admin email per row
    query = (
        db.query(AuditLog, User.email.label("admin_email"))
        .outerjoin(User, AuditLog.admin_id == User.id)
    )

    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    rows = (
        query.order_by(desc(AuditLog.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for log, admin_email in rows:
        parsed_details: Any = log.details
        if isinstance(log.details, str):
            try:
                parsed_details = json.loads(log.details)
            except (json.JSONDecodeError, TypeError):
                parsed_details = log.details

        result.append(
            AuditLogResponse(
                id=log.id,
                admin_email=admin_email,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=parsed_details,
                ip_address=log.ip_address,
                status=log.status,
                created_at=log.created_at,
            )
        )

    return result

