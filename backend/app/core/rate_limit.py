from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Optional
import time
from collections import defaultdict
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(
        self,
        key: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> bool:
        """Check if request is allowed within rate limits."""
        now = time.time()
        
        # Clean old requests
        self.requests[key] = [
            timestamp for timestamp in self.requests[key]
            if timestamp > now - window_seconds
        ]
        
        # Check if under limit
        if len(self.requests[key]) >= max_requests:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(
    request: Request,
    call_next
):
    """Rate limiting middleware for API endpoints."""
    # Get client identifier (IP or user ID if authenticated)
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit (100 requests per minute per IP)
    if not rate_limiter.is_allowed(client_ip, max_requests=100, window_seconds=60):
        logger.warning(
            "Rate limit exceeded",
            extra={"client_ip": client_ip, "path": request.url.path}
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )
    
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Window"] = "60"
    
    return response
