import time
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings

settings = get_settings()

# In-memory store per IP — swap for Redis in production
_request_counts: dict = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # WebSocket upgrades and health checks bypass the rate limit
        if request.url.path.startswith("/ws") or request.url.path in ("/health", "/"):
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60  # seconds

        # Remove old timestamps
        _request_counts[ip] = [t for t in _request_counts[ip] if now - t < window]

        if len(_request_counts[ip]) >= settings.RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again in a minute.",
            )

        _request_counts[ip].append(now)
        return await call_next(request)
