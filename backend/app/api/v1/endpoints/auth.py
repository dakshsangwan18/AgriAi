from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Annotated
from slowapi import Limiter
from slowapi.util import get_remote_address
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
import logging

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, Token, UserUpdate,
    ForgotPasswordRequest, ResetPasswordRequest, MessageResponse
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from app.core.config import settings
from app.core.validators import validate_email, validate_password
from app.models.refresh_token import RefreshToken
import asyncio
import secrets
import time
import hashlib
from datetime import datetime, timedelta, timezone
from app.services.email_service import email_service
from app.core.logging_config import logger

router = APIRouter()

limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.ENVIRONMENT != "testing"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

config = Config(environ={
    'GOOGLE_CLIENT_ID': settings.GOOGLE_CLIENT_ID or '',
    'GOOGLE_CLIENT_SECRET': settings.GOOGLE_CLIENT_SECRET or '',
})

oauth = OAuth(config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'timeout': 30.0
    }
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _set_cookie(
    response: Response,
    name: str,
    value: str,
    max_age: int,
    http_only: bool,
    path: str = "/"
):
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age,
        expires=max_age,
        httponly=http_only,
        secure=settings.cookie_secure(),
        samesite=settings.cookie_samesite(),
        domain=settings.COOKIE_DOMAIN,
        path=path,
    )


def _clear_cookie(response: Response, name: str, path: str = "/"):
    response.delete_cookie(
        key=name,
        domain=settings.COOKIE_DOMAIN,
        path=path,
    )


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str, csrf_token: str):
    access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    _set_cookie(response, settings.ACCESS_TOKEN_COOKIE_NAME, access_token, access_max_age, True, "/")
    _set_cookie(response, settings.REFRESH_TOKEN_COOKIE_NAME, refresh_token, refresh_max_age, True, "/api/v1/auth")
    _set_cookie(response, settings.CSRF_COOKIE_NAME, csrf_token, refresh_max_age, False, "/")


async def get_current_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode token
    raw_token = token or request.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
    if not raw_token:
        raise credentials_exception

    payload = decode_access_token(raw_token)
    if payload is None:
        logger.warning("Invalid token received", endpoint="/api/auth/verify")
        raise credentials_exception
    
    email: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    
    if email is None or user_id is None:
        logger.warning("Token missing required fields", user_id=user_id, email=email)
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning("User not found from valid token", user_id=user_id)
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")  # Max 5 registrations per hour per IP
async def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    # Validate email and password
    validated_email = validate_email(user_data.email)
    validated_password = validate_password(user_data.password)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == validated_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(validated_password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        location=user_data.location,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info("New user registered", user_id=new_user.id, email=new_user.email)
    
    # Send welcome email (optional, won't fail registration if email fails)
    try:
        await email_service.send_welcome_email(
            to_email=new_user.email,
            user_name=new_user.full_name
        )
    except Exception as e:
        logger.error("Failed to send welcome email", exc_info=e, user_id=new_user.id)
    
    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("50/hour")
async def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning("Failed login attempt", email=form_data.username, endpoint="/api/auth/login")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning("Inactive user login attempt", user_id=user.id, email=user.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    client_ip = request.client.host if request.client else "unknown"
    user.last_login = datetime.now(timezone.utc)
    user.last_login_ip = client_ip
    user.login_count = (user.login_count or 0) + 1
    if not user.login_method:
        user.login_method = "email"
    
    db.commit()
    db.refresh(user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )

    refresh_token = secrets.token_urlsafe(48)
    refresh_hash = _hash_token(refresh_token)
    refresh_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_expires,
            user_agent=request.headers.get("user-agent"),
            ip_address=client_ip
        )
    )
    db.commit()

    csrf_token = secrets.token_urlsafe(32)
    _set_auth_cookies(response, access_token, refresh_token, csrf_token)
    
    logger.info(f"User logged in successfully: {user.email} (login_count={user.login_count}, ip={client_ip})")
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name
    if update_data.phone is not None:
        current_user.phone = update_data.phone
    if update_data.location is not None:
        current_user.location = update_data.location
    if update_data.favorite_crops is not None:
        current_user.favorite_crops = update_data.favorite_crops
    if update_data.preferred_language is not None:
        current_user.preferred_language = update_data.preferred_language
    if update_data.notification_enabled is not None:
        current_user.notification_enabled = update_data.notification_enabled
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    raw_refresh = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if raw_refresh:
        token_hash = _hash_token(raw_refresh)
        token_row = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None)
        ).first()
        if token_row:
            token_row.revoked_at = datetime.now(timezone.utc)
            token_row.last_used_at = datetime.now(timezone.utc)
            db.commit()

    _clear_cookie(response, settings.ACCESS_TOKEN_COOKIE_NAME, "/")
    _clear_cookie(response, settings.REFRESH_TOKEN_COOKIE_NAME, "/api/v1/auth")
    _clear_cookie(response, settings.CSRF_COOKIE_NAME, "/")

    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
@limiter.limit("30/hour")
async def refresh_tokens(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    raw_refresh = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if not raw_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    token_hash = _hash_token(raw_refresh)
    token_row = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked_at.is_(None)
    ).first()

    if not token_row or token_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalid or expired")

    user = db.query(User).filter(User.id == token_row.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

    token_row.revoked_at = datetime.now(timezone.utc)
    token_row.last_used_at = datetime.now(timezone.utc)

    new_refresh = secrets.token_urlsafe(48)
    new_refresh_hash = _hash_token(new_refresh)
    new_refresh_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=new_refresh_hash,
            expires_at=new_refresh_expires,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None
        )
    )
    db.commit()

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    csrf_token = secrets.token_urlsafe(32)
    _set_auth_cookies(response, access_token, new_refresh, csrf_token)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/hour")  # Max 3 forgot password requests per hour per IP
async def forgot_password(
    request: Request,
    forgot_request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    # Constant-time handling to prevent email enumeration via timing side-channel
    start_time = time.monotonic()
    min_response_seconds = 1.0

    user = db.query(User).filter(User.email == forgot_request.email).first()

    if user:
        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()

        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        try:
            await email_service.send_password_reset_email(
                to_email=user.email,
                reset_link=reset_link,
                user_name=user.full_name
            )
        except Exception as e:
            # Log but never reveal failure to caller
            logger.error("Failed to send password reset email", exc_info=e, extra={"email": forgot_request.email})

    # Pad response to a minimum duration so existence of account cannot be inferred
    elapsed = time.monotonic() - start_time
    if elapsed < min_response_seconds:
        await asyncio.sleep(min_response_seconds - elapsed)

    return {"message": "If that email exists, a password reset link has been sent."}


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/hour")  # Max 5 reset attempts per hour per IP
async def reset_password(
    request: Request,
    reset_request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    # Find user by reset token
    user = db.query(User).filter(User.reset_token == reset_request.token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check if token is expired
    token_expires = user.reset_token_expires
    if token_expires and token_expires.tzinfo is None:
        token_expires = token_expires.replace(tzinfo=timezone.utc)

    if not token_expires or token_expires < datetime.now(timezone.utc):
        # Clear expired token
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user.hashed_password = get_password_hash(reset_request.new_password)

    # Revoke all active refresh tokens after password reset
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None)
    ).update({"revoked_at": datetime.now(timezone.utc)}, synchronize_session=False)
    
    user.reset_token = None
    user.reset_token_expires = None
    
    db.commit()
    
    return {"message": "Password has been reset successfully. You can now login with your new password."}


@router.get("/google/login")
@limiter.limit("10/minute")
async def google_login(request: Request):
    try:
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        logger.info(f"[OAUTH] Initiating Google login flow - redirect_uri: {redirect_uri}")
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        logger.error(f"[OAUTH] Google login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login is temporarily unavailable. Please use email/password login or try again later."
        )


@router.get("/google/callback")
@limiter.limit("20/minute")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        logger.info("[OAUTH] Processing Google OAuth callback")
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Google"
            )
        
        email = user_info.get('email')
        name = user_info.get('name')
        google_id = user_info.get('sub')
        picture = user_info.get('picture')
        
        client_ip = request.client.host if request.client else "unknown"
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            logger.info(f"[OAUTH] Creating new user account for Google user: {email}")
            user = User(
                email=email,
                full_name=name,
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                is_active=True,
                preferred_language="en",
                notification_enabled=True,
                oauth_provider="google",
                oauth_id=google_id,
                profile_picture_url=picture,
                login_method="google",
                email_verified=True,
                email_verified_at=datetime.now(timezone.utc),
                last_login=datetime.now(timezone.utc),
                last_login_ip=client_ip,
                login_count=1
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"[OAUTH] Successfully created user account: {email} (login_count=1)")
        else:
            logger.info(f"[OAUTH] User {email} already exists, updating login tracking")
            
            if not user.oauth_provider:
                user.oauth_provider = "google"
            if not user.oauth_id:
                user.oauth_id = google_id
            if not user.profile_picture_url and picture:
                user.profile_picture_url = picture
            
            if not user.email_verified:
                user.email_verified = True
                user.email_verified_at = datetime.now(timezone.utc)
                logger.info(f"[OAUTH] Marked email as verified for {email}")
            
            if user.preferred_language is None:
                user.preferred_language = "en"
            if user.notification_enabled is None:
                user.notification_enabled = True
            
            user.last_login = datetime.now(timezone.utc)
            user.last_login_ip = client_ip
            user.login_count = (user.login_count or 0) + 1
            user.login_method = "google"
            
            db.commit()
            db.refresh(user)
            logger.info(f"[OAUTH] Updated login tracking: {email} (login_count={user.login_count}, ip={client_ip})")
        
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )

        refresh_token = secrets.token_urlsafe(48)
        refresh_hash = _hash_token(refresh_token)
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=refresh_hash,
                expires_at=refresh_expires,
                user_agent=request.headers.get("user-agent"),
                ip_address=client_ip
            )
        )
        db.commit()

        csrf_token = secrets.token_urlsafe(32)
        response = RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/google/callback")
        _set_auth_cookies(response, access_token, refresh_token, csrf_token)

        # OAuth callbacks must never be cached; a cached 304 would skip the
        # code exchange and leave the user without auth cookies.
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        logger.info(
            f"[OAUTH] Successfully authenticated user {email}, redirecting to frontend",
            extra={
                "frontend_url": settings.FRONTEND_URL,
                "cookie_secure": settings.cookie_secure(),
                "cookie_samesite": settings.cookie_samesite(),
                "cookie_domain": settings.COOKIE_DOMAIN,
            }
        )
        return response
        
    except Exception as e:
        import traceback
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.error(f"[OAUTH] Google OAuth callback failed - Error type: {error_type}")
        logger.error(f"[OAUTH] Error message: {error_msg}")
        logger.error(f"[OAUTH] Stack trace:\n{traceback.format_exc()}")
        
        frontend_url = f"{settings.FRONTEND_URL}/login?error=google_auth_failed"
        logger.warning(f"[OAUTH] Redirecting user to frontend login page with error flag")
        return RedirectResponse(url=frontend_url)

