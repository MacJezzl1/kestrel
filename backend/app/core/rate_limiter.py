"""
Kestrel Shield — Sliding Window Rate Limiter
In-memory thread-safe rate limiter protecting sensitive authentication and trading endpoints.
Implements the OWASP Top 10 recommendations for brute-force and DDoS prevention.
"""
from collections import defaultdict
from datetime import datetime, timezone
import asyncio
import time
from fastapi import Request, HTTPException, status


class SlidingWindowRateLimiter:
    """Sliding-window counter rate limiter by client IP or User ID."""

    def __init__(self):
        # key -> list of timestamps (seconds)
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
            # Clean expired timestamps
            timestamps = [t for t in self._history[key] if t > cutoff]
            if len(timestamps) >= max_requests:
                retry_after = int(window_seconds - (now - timestamps[0])) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded for {action_name}. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(max(1, retry_after))},
                )

            # Record this request
            timestamps.append(now)
            self._history[key] = timestamps
            return True


# Global rate limiter instance
rate_limiter = SlidingWindowRateLimiter()


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
