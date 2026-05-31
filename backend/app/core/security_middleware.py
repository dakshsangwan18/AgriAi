
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import re
from typing import Callable
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    CSP_SCRIPT_HASHES = [
        "'sha256-uf+7mNA88XVfCdNJa7MlSLolHXL1jFfDlnxE25IAEuE='",
        "'sha256-GludQzLp2cagXwICMH/bRlmXJvC1iq2D1VUoJv2HmKg='",
    ]
    CSP_STYLE_HASHES = [
        "'sha256-fO/9dcPp2YR4M42g9eXUAJUtoLh6g11o+hXWpz5hZPY='",
    ]
    CSP_IMG_SOURCES = [
        "'self'",
        "data:",
        "https://images.unsplash.com",
    ]
    CSP_FONT_SOURCES = [
        "'self'",
        "https://fonts.gstatic.com",
        "data:",
    ]
    CSP_STYLE_SOURCES = [
        "'self'",
        "https://fonts.googleapis.com",
    ]
    CSP_CONNECT_SOURCES = [
        "'self'",
        "https://agriai-ecxt.onrender.com",
    ]

    def _build_csp(self) -> str:
        connect_sources = list(self.CSP_CONNECT_SOURCES)
        if settings.CSP_CONNECT_SRC:
            connect_sources.extend(
                [origin.strip() for origin in settings.CSP_CONNECT_SRC.split(",") if origin.strip()]
            )

        policy = [
            "default-src 'self'",
            "base-uri 'self'",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            f"img-src {' '.join(self.CSP_IMG_SOURCES)}",
            f"font-src {' '.join(self.CSP_FONT_SOURCES)}",
            f"style-src {' '.join(self.CSP_STYLE_SOURCES + self.CSP_STYLE_HASHES)}",
            "style-src-attr 'unsafe-inline'",
            f"script-src 'self' {' '.join(self.CSP_SCRIPT_HASHES)}",
            f"connect-src {' '.join(connect_sources)}",
            "upgrade-insecure-requests",
        ]

        if settings.CSP_REPORT_URI:
            policy.append(f"report-uri {settings.CSP_REPORT_URI}")

        return "; ".join(policy) + ";"
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        report_only = settings.CSP_REPORT_ONLY
        if report_only is None:
            report_only = settings.ENVIRONMENT != "production"

        csp_header = "Content-Security-Policy-Report-Only" if report_only else "Content-Security-Policy"
        response.headers[csp_header] = self._build_csp()
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    
    # Dangerous patterns to block
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"(UNION.*SELECT)",
        r"(;\s*(DROP|DELETE|UPDATE))",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip validation for OAuth callbacks (Google sends encoded tokens)
        if "/api/auth/google/callback" in request.url.path:
            return await call_next(request)
        
        # Skip validation for all auth endpoints (they handle their own validation)
        if "/api/auth/" in request.url.path or "/api/v1/auth/" in request.url.path:
            return await call_next(request)
        
        # Skip validation for GET requests without query params
        if request.method == "GET" and not request.url.query:
            return await call_next(request)
        
        # Check query parameters
        if request.url.query:
            for param, value in request.query_params.items():
                if self._is_malicious(str(value)):
                    logger.warning(f"Malicious input detected in query param: {param}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "Invalid input detected"}
                    )
        
        # Check request body for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode('utf-8')
                    if self._is_malicious(body_str):
                        logger.warning(f"Malicious input detected in request body")
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": "Invalid input detected"}
                        )
                    
                    # Restore body for next middleware
                    async def receive():
                        return {"type": "http.request", "body": body}
                    request._receive = receive
            except Exception as e:
                logger.error(f"Error validating request body: {e}")
        
        return await call_next(request)
    
    def _is_malicious(self, text: str) -> bool:
        text_upper = text.upper()
        
        # Check SQL injection patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return True
        
        # Check XSS patterns
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self, app, max_size: int | None = None):
        super().__init__(app)
        if max_size is not None:
            self.MAX_REQUEST_SIZE = max_size
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length:
            if int(content_length) > self.MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request too large"}
                )
        
        return await call_next(request)
