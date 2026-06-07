from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    EXEMPT_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
    }
    EXEMPT_PREFIXES = (
        "/api/v1/auth/google/",
    )

    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            path = request.url.path
            is_exempt = path in self.EXEMPT_PATHS or path.startswith(self.EXEMPT_PREFIXES)
            if not is_exempt:
                csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
                if csrf_cookie:
                    csrf_header = request.headers.get(settings.CSRF_HEADER_NAME)
                    if not csrf_header or csrf_header != csrf_cookie:
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"detail": "CSRF token missing or invalid"}
                        )

        return await call_next(request)
