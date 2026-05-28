"""Rate limiting implementation using token bucket algorithm."""

import time
from functools import wraps
from threading import Lock
from typing import Any, Callable, ParamSpec, TypeVar

from netbox_geo.core.exceptions import RateLimitError

P = ParamSpec("P")
R = TypeVar("R")


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, calls_per_minute: int = 100) -> None:
        """Initialize the rate limiter.

        Args:
            calls_per_minute: Maximum number of API calls allowed per minute.
        """
        if calls_per_minute < 1:
            raise ValueError("calls_per_minute must be at least 1")

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
        if tokens < 1:
            raise ValueError("tokens must be at least 1")
        if tokens > self.max_tokens:
            raise ValueError("tokens cannot exceed the configured bucket capacity")

        while True:
            with self._lock:
                self._refill()

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                retry_after = (tokens - self.tokens) / self.refill_rate
                if not blocking:
                    raise RateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after:.2f} seconds.",
                        retry_after=retry_after,
                    )

            # Wait outside the lock, then re-check token availability.
            time.sleep(retry_after)

    def __enter__(self) -> "RateLimiter":
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        pass


def rate_limit(calls_per_minute: int = 100) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Rate limit function calls with a decorator.

    Note: Creates a separate RateLimiter instance per decorated function.
    If you need a global rate limit, use a shared RateLimiter instance instead.

    Args:
        calls_per_minute: Maximum number of calls allowed per minute.

    Returns:
        Decorated function with rate limiting.
    """
    limiter = RateLimiter(calls_per_minute=calls_per_minute)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            limiter.acquire()
            return func(*args, **kwargs)

        return wrapper

    return decorator
