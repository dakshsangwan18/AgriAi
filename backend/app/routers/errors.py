from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.core.logging_config import logger
from app.core.config import settings
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()
limiter = Limiter(key_func=get_remote_address, enabled=settings.ENVIRONMENT != "testing")


class ClientError(BaseModel):
    
    message: str
    stack: Optional[str] = None
    componentStack: Optional[str] = None
    timestamp: str
    userAgent: str
    url: str


@router.post("/client")
@limiter.limit("60/minute")
async def log_client_error(
    error: ClientError,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    
    # Log the error with context
    logger.error(
        f"Client error: {error.message}",
        user_id=current_user.id,
        endpoint=error.url,
        request_id=getattr(request.state, 'request_id', None),
        client_error={
            "message": error.message,
            "stack": error.stack,
            "componentStack": error.componentStack,
            "userAgent": error.userAgent,
            "timestamp": error.timestamp
        }
    )
    
    return {"status": "logged", "request_id": getattr(request.state, 'request_id', None)}


@router.post("/client/anonymous")
@limiter.limit(settings.ANON_ERROR_RATE_LIMIT)
async def log_anonymous_client_error(
    error: ClientError,
    request: Request
):

    if not settings.allow_anonymous_errors():
        raise HTTPException(status_code=404, detail="Not found")
    
    # Log the error without user context
    logger.error(
        f"Anonymous client error: {error.message}",
        endpoint=error.url,
        request_id=getattr(request.state, 'request_id', None),
        client_error={
            "message": error.message,
            "stack": error.stack,
            "componentStack": error.componentStack,
            "userAgent": error.userAgent,
            "timestamp": error.timestamp
        }
    )
    
    return {"status": "logged", "request_id": getattr(request.state, 'request_id', None)}
