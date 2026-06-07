from fastapi import Depends, HTTPException
from typing import Annotated

from app.api.v1.endpoints.auth import get_current_active_user
from app.models.user import User


def verify_admin(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
