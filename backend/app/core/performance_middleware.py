from time import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging_config import logger
from app.core.request_id_middleware import get_request_id


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    
    metrics = {
        "total_requests": 0,
        "slow_requests": 0,
        "total_response_time": 0.0
    }
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time()
        
        # Process request
        response: Response = await call_next(request)
        
        # Calculate duration
        duration = time() - start_time
        
        # Update metrics
        self.metrics["total_requests"] += 1
        self.metrics["total_response_time"] += duration
        
        # Log slow requests
        if duration > 1.0:
            self.metrics["slow_requests"] += 1
            logger.warning(
                f"Slow request detected",
                extra={
                    "duration": f"{duration:.2f}s",
                    "method": request.method,
                    "path": request.url.path,
                    "request_id": get_request_id(),
                    "status_code": response.status_code
                }
            )
        
        # Add performance header
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        return response
    
    @classmethod
    def get_metrics(cls):
        avg_response_time = (
            cls.metrics["total_response_time"] / cls.metrics["total_requests"]
            if cls.metrics["total_requests"] > 0
            else 0
        )
        
        slow_percentage = (
            (cls.metrics["slow_requests"] / cls.metrics["total_requests"]) * 100
            if cls.metrics["total_requests"] > 0
            else 0
        )
        
        return {
            "requests": {
                "total": cls.metrics["total_requests"],
                "slow": cls.metrics["slow_requests"],
                "slow_percentage": round(slow_percentage, 2)
            },
            "response_time": {
                "average": round(avg_response_time, 3),
                "total": round(cls.metrics["total_response_time"], 2)
            }
        }
