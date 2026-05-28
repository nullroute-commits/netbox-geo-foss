"""Unit tests for rate limiter."""

import time

import pytest

from netbox_geo.core.exceptions import RateLimitError
from netbox_geo.netbox.rate_limiter import RateLimiter, rate_limit


def test_rate_limiter_initialization() -> None:
    """Test RateLimiter initialization."""
    limiter = RateLimiter(calls_per_minute=60)
    assert limiter.calls_per_minute == 60
    assert limiter.max_tokens == 60.0


def test_rate_limiter_acquire_tokens() -> None:
    """Test acquiring tokens from rate limiter."""
    limiter = RateLimiter(calls_per_minute=60)
    assert limiter.acquire(tokens=1, blocking=False) is True


def test_rate_limiter_exceeds_limit() -> None:
    """Test rate limiter when limit is exceeded."""
    limiter = RateLimiter(calls_per_minute=60)
    limiter.tokens = 0  # Set tokens to 0 to force limit exceeded

    with pytest.raises(RateLimitError) as exc_info:
        limiter.acquire(tokens=1, blocking=False)

    assert exc_info.value.retry_after is not None
    assert exc_info.value.retry_after > 0


def test_rate_limiter_context_manager() -> None:
    """Test rate limiter as context manager."""
    limiter = RateLimiter(calls_per_minute=60)

    with limiter:
        pass  # Context manager should work without errors


def test_rate_limiter_refill() -> None:
    """Test that tokens refill over time."""
    limiter = RateLimiter(calls_per_minute=60)
    limiter.tokens = 0
    initial_tokens = limiter.tokens

    # Wait a bit for refill
    time.sleep(0.1)
    limiter._refill()

    assert limiter.tokens > initial_tokens


def test_rate_limiter_rejects_invalid_rate() -> None:
    """Verify that RateLimiter rejects non-positive call rates."""
    with pytest.raises(ValueError, match="calls_per_minute must be at least 1"):
        RateLimiter(calls_per_minute=0)


def test_rate_limiter_rejects_invalid_token_requests() -> None:
    """Verify that RateLimiter rejects non-positive token requests."""
    limiter = RateLimiter(calls_per_minute=60)

    with pytest.raises(ValueError, match="tokens must be at least 1"):
        limiter.acquire(tokens=0)


def test_rate_limiter_rejects_requests_larger_than_bucket() -> None:
    """Verify that RateLimiter rejects requests larger than the bucket capacity."""
    limiter = RateLimiter(calls_per_minute=60)

    with pytest.raises(ValueError, match="bucket capacity"):
        limiter.acquire(tokens=61)


def test_rate_limit_decorator_preserves_metadata() -> None:
    """The rate_limit decorator should preserve wrapped function metadata."""

    @rate_limit(calls_per_minute=60)
    def sample_function() -> str:
        """Return a sentinel value for testing."""
        return "ok"

    assert sample_function() == "ok"
    assert sample_function.__name__ == "sample_function"
    assert sample_function.__doc__ == "Return a sentinel value for testing."
