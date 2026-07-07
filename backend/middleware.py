"""
Rate-limiting and security middleware for Smart Bharat API.
"""
import time
import logging
from collections import defaultdict
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("smart_bharat")

# Rate limiting configuration
RATE_LIMIT = 30  # requests
RATE_WINDOW = 60  # seconds

# Global request log: IP -> list of timestamps
_request_log: dict[str, list[float]] = defaultdict(list)


async def rate_limit_middleware(request: Request, call_next: Callable) -> JSONResponse:
    """
    Enforce per-IP rate limiting (30 requests per 60 seconds).
    Also add security headers to all responses.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Clean old timestamps outside the rate window
    _request_log[client_ip] = [t for t in _request_log[client_ip] if now - t < RATE_WINDOW]
    
    # Check if limit exceeded
    if len(_request_log[client_ip]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please slow down."}
        )
    
    # Record this request
    _request_log[client_ip].append(now)
    
    # Process request
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    
    return response
