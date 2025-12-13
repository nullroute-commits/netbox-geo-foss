"""Rate limiting implementation using token bucket algorithm."""

import time
from threading import Lock
from typing import Any, Callable

from netbox_geo.core.exceptions import RateLimitError


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, calls_per_minute: int = 100) -> None:
        """Initialize the rate limiter.

        Args:
            calls_per_minute: Maximum number of API calls allowed per minute.
        """
        self.calls_per_minute = calls_per_minute
        self.tokens = float(calls_per_minute)
        self.max_tokens = float(calls_per_minute)
        self.refill_rate = calls_per_minute / 60.0  # tokens per second
        self.last_refill = time.time()
        self._lock = Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def acquire(self, tokens: int = 1, blocking: bool = True) -> bool:
        """Acquire tokens for an API call.

        Args:
            tokens: Number of tokens to acquire.
            blocking: If True, wait until tokens are available.

        Returns:
            True if tokens were acquired, False otherwise.

        Raises:
            RateLimitError: If tokens cannot be acquired in non-blocking mode.
        """
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            if not blocking:
                retry_after = (tokens - self.tokens) / self.refill_rate
                raise RateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after:.2f} seconds.",
                    retry_after=retry_after,
                )

            # Calculate wait time
            wait_time = (tokens - self.tokens) / self.refill_rate

        # Wait outside the lock
        time.sleep(wait_time)

        with self._lock:
            self._refill()
            self.tokens -= tokens
            return True

    def __enter__(self) -> "RateLimiter":
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        pass


def rate_limit(calls_per_minute: int = 100) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to rate limit function calls.

    Args:
        calls_per_minute: Maximum number of calls allowed per minute.

    Returns:
        Decorated function with rate limiting.
    """
    limiter = RateLimiter(calls_per_minute=calls_per_minute)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            limiter.acquire()
            return func(*args, **kwargs)

        return wrapper

    return decorator
