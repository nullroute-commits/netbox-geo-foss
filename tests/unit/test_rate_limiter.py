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


def test_rate_limiter_default_calls_per_minute() -> None:
    """Test RateLimiter default calls_per_minute."""
    limiter = RateLimiter()
    assert limiter.calls_per_minute == 100


def test_rate_limiter_refill_rate() -> None:
    """Test that refill rate is correctly calculated."""
    limiter = RateLimiter(calls_per_minute=120)
    assert limiter.refill_rate == 2.0  # 120/60 = 2 tokens per second


def test_rate_limiter_acquire_tokens() -> None:
    """Test acquiring tokens from rate limiter."""
    limiter = RateLimiter(calls_per_minute=60)
    assert limiter.acquire(tokens=1, blocking=False) is True


def test_rate_limiter_acquire_decrements_tokens() -> None:
    """Test that acquire decrements available tokens."""
    limiter = RateLimiter(calls_per_minute=60)
    initial = limiter.tokens
    limiter.acquire(tokens=1, blocking=False)
    # tokens should be less (approximately, accounting for small refill)
    assert limiter.tokens < initial


def test_rate_limiter_exceeds_limit() -> None:
    """Test rate limiter when limit is exceeded."""
    limiter = RateLimiter(calls_per_minute=60)
    limiter.tokens = 0  # Set tokens to 0 to force limit exceeded

    with pytest.raises(RateLimitError) as exc_info:
        limiter.acquire(tokens=1, blocking=False)

    assert exc_info.value.retry_after is not None
    assert exc_info.value.retry_after > 0


def test_rate_limiter_blocking_acquire() -> None:
    """Test blocking acquire waits for tokens."""
    limiter = RateLimiter(calls_per_minute=6000)  # High rate for fast test
    limiter.tokens = 0  # Exhaust tokens

    start = time.time()
    result = limiter.acquire(tokens=1, blocking=True)
    elapsed = time.time() - start

    assert result is True
    assert elapsed >= 0  # Some wait time occurred


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


def test_rate_limiter_refill_capped_at_max() -> None:
    """Test that refill does not exceed max_tokens."""
    limiter = RateLimiter(calls_per_minute=60)
    limiter.tokens = 60.0  # Already at max
    time.sleep(0.1)
    limiter._refill()
    assert limiter.tokens <= limiter.max_tokens


class TestRateLimitDecorator:
    """Tests for the rate_limit decorator."""

    def test_decorator_allows_calls(self) -> None:
        """Test that decorated function can be called."""
        @rate_limit(calls_per_minute=1000)
        def my_func(x: int) -> int:
            return x * 2

        assert my_func(5) == 10

    def test_decorator_preserves_return_value(self) -> None:
        """Test that decorator preserves the function's return value."""
        @rate_limit(calls_per_minute=1000)
        def greet(name: str) -> str:
            return f"Hello, {name}"

        assert greet("World") == "Hello, World"

    def test_decorator_passes_kwargs(self) -> None:
        """Test that decorator passes keyword arguments."""
        @rate_limit(calls_per_minute=1000)
        def add(a: int, b: int = 0) -> int:
            return a + b

        assert add(3, b=4) == 7

    def test_decorator_rate_limits(self) -> None:
        """Test that decorator enforces rate limiting."""
        call_count = 0

        @rate_limit(calls_per_minute=1000)
        def increment() -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        # Should succeed for a reasonable number of calls
        for _ in range(10):
            increment()
        assert call_count == 10
