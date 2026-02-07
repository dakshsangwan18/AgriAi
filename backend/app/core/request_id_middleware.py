import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from contextvars import ContextVar
from typing import Optional


request_id_context: ContextVar[str] = ContextVar("request_id", default=None)


class RequestIDMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")
        
        if not request_id:
            request_id = str(uuid.uuid4())
        
        request_id_context.set(request_id)
        
        request.state.request_id = request_id
        
        response: Response = await call_next(request)
        
        response.headers["X-Request-ID"] = request_id
        
        return response


def get_request_id() -> Optional[str]:
    return request_id_context.get()
