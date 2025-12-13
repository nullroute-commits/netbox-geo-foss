"""Unit tests for rate limiter."""

import time

import pytest

from netbox_geo.core.exceptions import RateLimitError
from netbox_geo.netbox.rate_limiter import RateLimiter


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
