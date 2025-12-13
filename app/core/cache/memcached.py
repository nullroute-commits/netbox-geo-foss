"""Memcached client configuration and utilities.

Provides caching functionality for the application.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""
import os
import logging
import hashlib
import threading
import memcache
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Thread local storage for memcached client
_thread_locals = threading.local()


class MemcachedClient:
    """
    Memcached client wrapper with additional functionality.

    Features:
    - Connection pooling
    - Automatic key namespacing
    - Timeout handling
    - Serialization handling
    - Logging and monitoring
    """

    def __init__(self, servers: List[str], namespace: str = 'app', **kwargs):
        """
        Initialize the Memcached client.

        Args:
            servers: List of memcached servers in format 'host:port'
            namespace: Namespace prefix for all keys
            **kwargs: Additional arguments for memcache.Client
        """
        self.namespace = namespace
        self.default_timeout = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '300'))
        self.client = memcache.Client(servers, **kwargs)
        logger.info(f"Initialized Memcached client with servers: {servers}")

    def _make_key(self, key: str) -> str:
        """
        Create a namespaced key with prefix.

        Args:
            key: Original cache key

        Returns:
            Namespaced cache key
        """
        if isinstance(key, str):
            key = key.encode('utf-8')
        return f"{self.namespace}:{hashlib.sha256(key).hexdigest()}"

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        namespaced_key = self._make_key(key)
        value = self.client.get(namespaced_key)
        if value is None:
            logger.debug(f"Cache miss for key: {key}")
            return default

        logger.debug(f"Cache hit for key: {key}")
        return value

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            timeout: Cache timeout in seconds (0 = no expiration)

        Returns:
            True if successful, False otherwise
        """
        namespaced_key = self._make_key(key)
        if timeout is None:
            timeout = self.default_timeout

        result = self.client.set(namespaced_key, value, timeout)
        if result:
            logger.debug(f"Cache set for key: {key} with timeout: {timeout}s")
        else:
            logger.warning(f"Failed to set cache for key: {key}")

        return result

    def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        namespaced_key = self._make_key(key)
        result = self.client.delete(namespaced_key)
        if result:
            logger.debug(f"Cache deleted for key: {key}")
        else:
            logger.warning(f"Failed to delete cache for key: {key}")

        return result

    def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful, False otherwise
        """
        result = self.client.flush_all()
        logger.info("Cache cleared")
        return result

    def stats(self) -> Dict[str, Dict[str, Union[int, str]]]:
        """
        Get cache statistics.

        Returns:
            Dictionary of server statistics
        """
        return self.client.get_stats()


def get_memcached_client() -> MemcachedClient:
    """
    Get or create a thread-local Memcached client.

    Returns:
        MemcachedClient instance
    """
    if not hasattr(_thread_locals, 'memcached_client'):
        servers = os.environ.get('MEMCACHED_SERVERS', 'memcached:11211').split(',')
        namespace = os.environ.get('MEMCACHED_NAMESPACE', 'app')

        _thread_locals.memcached_client = MemcachedClient(
            servers=servers,
            namespace=namespace,
            dead_retry=int(os.environ.get('MEMCACHED_DEAD_RETRY', '60')),
            socket_timeout=float(os.environ.get('MEMCACHED_SOCKET_TIMEOUT', '3.0')),
            retries=int(os.environ.get('MEMCACHED_RETRIES', '2')),
        )

    return _thread_locals.memcached_client


# Helper functions for common cache operations

def cache_get(key: str, default: Any = None) -> Any:
    """
    Get a value from cache.

    Args:
        key: Cache key
        default: Default value if key not found

    Returns:
        Cached value or default
    """
    return get_memcached_client().get(key, default)


def cache_set(key: str, value: Any, timeout: Optional[int] = None) -> bool:
    """
    Set a value in cache.

    Args:
        key: Cache key
        value: Value to cache
        timeout: Cache timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    return get_memcached_client().set(key, value, timeout)


def cache_delete(key: str) -> bool:
    """
    Delete a value from cache.

    Args:
        key: Cache key

    Returns:
        True if successful, False otherwise
    """
    return get_memcached_client().delete(key)


def cached(timeout: Optional[int] = None):
    """
    Decorate function to cache function results.

    Args:
        timeout: Cache timeout in seconds

    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            key = ":".join(key_parts)

            # Try to get from cache first
            cached_value = cache_get(key)
            if cached_value is not None:
                return cached_value

            # Cache miss, call the function
            result = func(*args, **kwargs)

            # Store in cache
            cache_set(key, result, timeout)

            return result
        return wrapper
    return decorator
