from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routers import weather, chatbot, prices, yield_prediction, agent, notifications, admin, errors, alerts, profile, health
from app.api.v1.endpoints import auth
from app.services.scheduler_service import scheduler_service
from app.database import init_db
from app.core.config import settings
from app.core.env_validator import validate_environment
from app.core.security_middleware import (
    SecurityHeadersMiddleware,
    InputValidationMiddleware,
    RequestSizeLimitMiddleware
)
from app.core.logging_config import logger
from app.core.error_tracking import ErrorTrackingMiddleware
from app.core.cache import cache_manager
from app.core.exceptions import AgriAIException
from app.core.request_id_middleware import RequestIDMiddleware
from app.core.performance_middleware import PerformanceMonitoringMiddleware
from fastapi.responses import JSONResponse
import traceback

# Validate environment variables before anything else
validate_environment()

# Load environment variables from .env file
load_dotenv()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Agriculture AI Platform API - Autonomous Agent")

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Error tracking middleware (add first to catch all errors)
app.add_middleware(ErrorTrackingMiddleware)

# Security Middlewares (add first for maximum protection)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)

# HTTPS Enforcement for Production
if settings.ENVIRONMENT == "production":
    from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
    app.add_middleware(HTTPSRedirectMiddleware)
    logger.info("[SECURE] HTTPS enforcement enabled - all HTTP requests will redirect to HTTPS")

# Request ID Middleware for distributed tracing
app.add_middleware(RequestIDMiddleware)
logger.info(" Request ID middleware enabled for distributed tracing")

# Performance Monitoring Middleware
app.add_middleware(PerformanceMonitoringMiddleware)
logger.info("[DATA] Performance monitoring middleware enabled")


# IMPORTANT: SessionMiddleware must be added BEFORE CORSMiddleware for OAuth to work
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY,  # Use same secret as JWT
    session_cookie="oauth_session",
    max_age=600,  # OAuth session expires in 10 minutes
    same_site="lax",
    https_only=settings.ENVIRONMENT == "production"  # Enable HTTPS in production
)

# CORS - Production-grade configuration with explicit origins
CORS_ORIGINS = [
    # Development origins
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    # Production frontend URL
    "https://agri-ai-eight-nu.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Explicit origins (no wildcards for security)
    allow_credentials=True,  # Required for authenticated requests
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all response headers
)


@app.exception_handler(AgriAIException)
async def agri_ai_exception_handler(request: Request, exc: AgriAIException):
    from app.core.request_id_middleware import get_request_id
    
    # Log the error with context
    logger.error(
        f"{exc.error_code}: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "request_id": get_request_id(),
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions with error tracking.
    
    Logs full traceback for debugging but returns generic message to user.
    This prevents exposing internal implementation details.
    """
    from app.core.request_id_middleware import get_request_id
    
    # Log full traceback for debugging
    logger.critical(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "request_id": get_request_id(),
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    )
    
    # Don't expose internal errors to users in production
    if settings.ENVIRONMENT == "production":
        message = "An unexpected error occurred. Please try again later."
    else:
        message = f"Internal error: {str(exc)}"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": message,
                "request_id": get_request_id()
            }
        }
    )

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(prices.router, prefix="/api/prices", tags=["Prices"])
app.include_router(yield_prediction.router, prefix="/api/yield", tags=["Yield Prediction"])
app.include_router(agent.router, prefix="/api/agent", tags=["AI Agent"])  # New autonomous agent
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])  # Notification system
app.include_router(alerts.router, prefix="/api/alerts", tags=["Price Alerts"])  # NEW: Price alerts
app.include_router(profile.router, prefix="/api/profile", tags=["User Profile"])  # NEW: User profiles
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])  # Admin panel
app.include_router(errors.router, prefix="/api/errors", tags=["Error Tracking"])  # Client error logging
app.include_router(health.router, prefix="/api", tags=["Health"])  # Health & monitoring endpoints


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Agriculture AI Platform with Autonomous Agent...")
    
    try:
        # Initialize database tables
        init_db()
        logger.info("Database initialized successfully")
        
        # Start scheduler if not in testing
        if settings.ENVIRONMENT != "testing":
            try:
                scheduler_service.start()
                logger.info("Autonomous agent scheduler started successfully")
                logger.info("Background jobs configured:")
                logger.info("  - Price monitoring: Running continuously")
                logger.info("  - Daily data collection: 6:00 PM IST")
                logger.info("  - Alert processing: Every 5 minutes")
            except Exception as scheduler_error:
                logger.error(f"Failed to start scheduler: {str(scheduler_error)}")
        else:
            logger.info("Scheduler disabled in testing environment")
            
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Agriculture AI Platform...")
    
    if settings.ENVIRONMENT != "testing":
        try:
            if scheduler_service.is_running:
                scheduler_service.stop()
                logger.info("Scheduler stopped successfully")
        except Exception as e:
            logger.warning(f"Scheduler shutdown warning: {str(e)}")
        
        try:
            cache_manager.close()
            logger.info("Cache connection closed")
        except Exception as e:
            logger.warning(f"Cache cleanup warning: {str(e)}")
    
    logger.info("Shutdown complete")

@app.get("/")
def read_root():
    return {
        "message": "Agriculture AI Platform - Autonomous Agent Active",
        "agent_status": "running" if scheduler_service.is_running else "stopped",
        "features": ["Weather", "Chatbot", "Prices", "Yield Prediction", "AI Agent"]
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "agent_running": scheduler_service.is_running
    }
