from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import uuid
import time
from app.core.logging_config import logger
from app.core.config import settings


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Log request info
            process_time = (time.time() - start_time) * 1000
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code}",
                request_id=request_id,
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                process_time_ms=process_time
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except HTTPException as exc:
            # Log HTTP exceptions
            logger.warning(
                f"HTTP Exception: {exc.status_code} - {exc.detail}",
                request_id=request_id,
                endpoint=request.url.path,
                status_code=exc.status_code,
                detail=exc.detail
            )
            
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail, "request_id": request_id},
                headers={"X-Request-ID": request_id}
            )
            
        except Exception as exc:
            # Log unexpected errors
            logger.error(
                f"Unhandled exception: {str(exc)}",
                exc_info=exc,
                request_id=request_id,
                endpoint=request.url.path
            )
            
            include_error_detail = settings.ENVIRONMENT != "production"

            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id,
                    "error": str(exc) if include_error_detail else None
                },
                headers={"X-Request-ID": request_id}
            )
