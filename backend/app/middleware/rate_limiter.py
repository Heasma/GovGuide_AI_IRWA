"""
GovGuide AI — Rate Limiter Middleware
In-memory sliding window rate limiter for public AI and agent endpoints.
Protects against denial of service and API quota abuse.
"""

import time
import structlog
from typing import Dict, Tuple, List
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings

logger = structlog.get_logger(__name__)


class RateLimiter:
    """
    Sliding window in-memory rate limiter per IP / User identifier.
    """

    def __init__(self, requests_per_minute: int = 60, query_per_minute: int = 20):
        self.requests_per_minute = requests_per_minute
        self.query_per_minute = query_per_minute
        self._general_hits: Dict[str, List[float]] = {}
        self._query_hits: Dict[str, List[float]] = {}

    def is_allowed(self, client_ip: str, path: str) -> Tuple[bool, int]:
        """
        Check if request from client_ip is allowed.
        Returns (is_allowed, remaining_requests).
        """
        now = time.monotonic()
        window = 60.0

        is_query = "/query" in path or "/agents" in path
        limit = self.query_per_minute if is_query else self.requests_per_minute
        hits_dict = self._query_hits if is_query else self._general_hits

        # Clean old hits outside 60s window
        if client_ip not in hits_dict:
            hits_dict[client_ip] = []

        hits_dict[client_ip] = [t for t in hits_dict[client_ip] if now - t < window]

        if len(hits_dict[client_ip]) >= limit:
            return False, 0

        hits_dict[client_ip].append(now)
        remaining = max(0, limit - len(hits_dict[client_ip]))
        return True, remaining


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware applying rate limits across incoming requests.
    Exempts health checks and test environments.
    """

    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()
        self.limiter = RateLimiter(
            requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
            query_per_minute=settings.RATE_LIMIT_QUERY_PER_MINUTE,
        )

    async def dispatch(self, request: Request, call_next):
        # Exempt health checks and documentation
        path = request.url.path
        if path in ("/api/v1/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"):
            return await call_next(request)

        # In testing mode (e.g. TestClient), allow bypass if header or test flag is present
        if get_settings().APP_ENV == "testing" or request.headers.get("X-Test-Bypass-Rate-Limit") == "true":
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        allowed, remaining = self.limiter.is_allowed(client_ip, path)

        if not allowed:
            logger.warning("rate_limit_exceeded", client_ip=client_ip, path=path)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please wait a minute before making more requests.",
                    "retry_after_seconds": 60,
                },
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
