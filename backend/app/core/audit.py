import json
from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.core.logging_config import logger


def log_admin_action(
    db: Session,
    admin: User,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    request: Optional[Request] = None,
    status: str = "success"
):
    try:
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = (
                request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
                request.headers.get("X-Real-IP") or
                request.client.host if request.client else None
            )
            user_agent = request.headers.get("User-Agent")
        
        audit_entry = AuditLog(
            admin_id=admin.id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
            status=status
        )
        
        db.add(audit_entry)
        db.commit()
        
    except Exception as e:
        logger.error("Failed to log audit entry", exc_info=e, extra={"admin_id": admin.id, "action": action})
        db.rollback()
