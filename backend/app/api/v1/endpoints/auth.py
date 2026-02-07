from fastapi import APIRouter, Depends, HTTPException, status, Request
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
import secrets
from datetime import datetime, timedelta, timezone
from app.services.email_service import email_service
from app.core.logging_config import logger

router = APIRouter()

# Rate limiter - disabled in testing to allow tests to run freely
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.ENVIRONMENT != "testing"  # Disable in test mode
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# OAuth configuration for Google
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
        'timeout': 30.0  # Increase timeout for Docker environments
    }
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode token
    payload = decode_access_token(token)
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
    
    # Create new user
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
@limiter.limit("50/hour")  # Increased for testing - reduce in production
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """
    Email/password login with production-grade security tracking
    """
    # Find user by email (username field in OAuth2 form)
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
    
    # Track login activity (production-grade security)
    client_ip = request.client.host if request.client else "unknown"
    user.last_login = datetime.now(timezone.utc)
    user.last_login_ip = client_ip
    user.login_count = (user.login_count or 0) + 1
    if not user.login_method:  # Set default for existing users
        user.login_method = "email"
    
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
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
    # Update only provided fields
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
async def logout(current_user: Annotated[User, Depends(get_current_active_user)]):
    return {"message": "Successfully logged out"}


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/hour")  # Max 3 forgot password requests per hour per IP
async def forgot_password(
    request: Request,
    forgot_request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    # Find user by email
    user = db.query(User).filter(User.email == forgot_request.email).first()
    
    # Always return success to prevent email enumeration attacks
    # (Don't reveal if email exists or not)
    if not user:
        return {"message": "If that email exists, a password reset link has been sent."}
    
    # Generate secure reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Token expires in 1 hour
    user.reset_token = reset_token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    
    db.commit()
    
    # Send password reset email
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    try:
        await email_service.send_password_reset_email(
            to_email=user.email,
            reset_link=reset_link,
            user_name=user.full_name
        )
    except Exception as e:
        # Log error but don't reveal to user
        logger.error("Failed to send password reset email", exc_info=e, extra={"email": email_lower})
        # Still return success to prevent email enumeration
    
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
    if not user.reset_token_expires or user.reset_token_expires < datetime.now(timezone.utc):
        # Clear expired token
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_request.new_password)
    
    # Clear reset token
    user.reset_token = None
    user.reset_token_expires = None
    
    db.commit()
    
    return {"message": "Password has been reset successfully. You can now login with your new password."}


@router.get("/google/login")
@limiter.limit("10/minute")  # Rate limit: 10 Google login attempts per minute per IP
async def google_login(request: Request):
    """
    Initiate Google OAuth login flow.
    Rate limited to prevent abuse and excessive redirects.
    """
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
@limiter.limit("20/minute")  # Rate limit: 20 OAuth callbacks per minute per IP
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback after user authentication.
    Creates or updates user account and returns JWT token via frontend redirect.
    """
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
        google_id = user_info.get('sub')  # Google's unique user ID
        picture = user_info.get('picture')  # Profile picture URL
        
        # Get client IP for security tracking
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user with OAuth defaults
            logger.info(f"[OAUTH] Creating new user account for Google user: {email}")
            user = User(
                email=email,
                full_name=name,
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),  # Random secure password
                is_active=True,
                preferred_language="en",
                notification_enabled=True,
                # OAuth fields
                oauth_provider="google",
                oauth_id=google_id,
                profile_picture_url=picture,
                login_method="google",
                # Email is verified by Google
                email_verified=True,
                email_verified_at=datetime.now(timezone.utc),
                # Login tracking
                last_login=datetime.now(timezone.utc),
                last_login_ip=client_ip,
                login_count=1
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"[OAUTH] Successfully created user account: {email} (login_count=1)")
        else:
            # Update existing user - track login activity
            logger.info(f"[OAUTH] User {email} already exists, updating login tracking")
            
            # Update OAuth info if not set
            if not user.oauth_provider:
                user.oauth_provider = "google"
            if not user.oauth_id:
                user.oauth_id = google_id
            if not user.profile_picture_url and picture:
                user.profile_picture_url = picture
            
            # Mark email as verified (Google verified it)
            if not user.email_verified:
                user.email_verified = True
                user.email_verified_at = datetime.now(timezone.utc)
                logger.info(f"[OAUTH] Marked email as verified for {email}")
            
            # Update defaults if missing
            if user.preferred_language is None:
                user.preferred_language = "en"
            if user.notification_enabled is None:
                user.notification_enabled = True
            
            # Track login activity (production-grade security)
            user.last_login = datetime.now(timezone.utc)
            user.last_login_ip = client_ip
            user.login_count = (user.login_count or 0) + 1
            user.login_method = "google"
            
            db.commit()
            db.refresh(user)
            logger.info(f"[OAUTH] Updated login tracking: {email} (login_count={user.login_count}, ip={client_ip})")
        
        # Create JWT token
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        # Redirect to frontend with token
        frontend_url = f"{settings.FRONTEND_URL}/auth/google/callback?token={access_token}"
        logger.info(f"[OAUTH] Successfully authenticated user {email}, redirecting to frontend")
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        # Production-grade error handling with detailed logging
        import traceback
        error_type = type(e).__name__
        error_msg = str(e)
        
        # Log detailed error for monitoring and debugging
        logger.error(f"[OAUTH] Google OAuth callback failed - Error type: {error_type}")
        logger.error(f"[OAUTH] Error message: {error_msg}")
        logger.error(f"[OAUTH] Stack trace:\n{traceback.format_exc()}")
        
        # Redirect to frontend with error (never expose internal errors to users)
        frontend_url = f"{settings.FRONTEND_URL}/login?error=google_auth_failed"
        logger.warning(f"[OAUTH] Redirecting user to frontend login page with error flag")
        return RedirectResponse(url=frontend_url)

