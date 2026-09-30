"""
Kestrel Shield — Multi-Tier Rate Limiting
Combines SlowAPI (token bucket / fixed window) for FastAPI route decorators
with in-memory Sliding Window Limiter for per-account granular checks.
Implements OWASP recommendations for brute-force, DDoS, and API protection.
"""
from collections import defaultdict
from typing import Optional
import asyncio
import time
from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_client_ip(request: Request) -> str:
    """Extract real client IP considering forward headers (Cloudflare, AWS WAF, Nginx)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit identifier combining Account/User (if authenticated) and IP.
    """
    account_header = request.headers.get("X-Account-ID") or request.headers.get("X-API-Key")
    ip = get_client_ip(request)
    if account_header:
        return f"acc:{account_header[:16]}:{ip}"
    return f"ip:{ip}"


# Global SlowAPI Limiter instance
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["120/minute"],
    headers_enabled=True,
    storage_uri="memory://",
)


class SlidingWindowRateLimiter:
    """Sliding-window counter rate limiter by client IP or User ID."""

    def __init__(self):
        self._history = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int = 10,
        window_seconds: int = 60,
        action_name: str = "request",
    ) -> bool:
        """
        Check if an action is within limits.
        Raises HTTP 429 if the rate limit is exceeded.
        """
        now = time.time()
        cutoff = now - window_seconds

        async with self._lock:
            timestamps = [t for t in self._history[key] if t > cutoff]
            if len(timestamps) >= max_requests:
                retry_after = int(window_seconds - (now - timestamps[0])) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded for {action_name}. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(max(1, retry_after))},
                )

            timestamps.append(now)
            self._history[key] = timestamps
            return True


rate_limiter = SlidingWindowRateLimiter()
