"""NetBox API client with rate limiting and retry logic."""

import time
from typing import Any

import pynetbox
from loguru import logger
from requests.exceptions import RequestException

from netbox_geo.core.config import NetBoxConfig
from netbox_geo.core.exceptions import NetBoxAPIError, RateLimitError
from netbox_geo.netbox.rate_limiter import RateLimiter


class NetBoxClient:
    """NetBox API client with enhanced error handling and rate limiting."""

    def __init__(self, config: NetBoxConfig, rate_limit_calls_per_minute: int = 100) -> None:
        """Initialize NetBox client.

        Args:
            config: NetBox configuration.
            rate_limit_calls_per_minute: Maximum API calls per minute.
        """
        self.config = config
        self.rate_limiter = RateLimiter(calls_per_minute=rate_limit_calls_per_minute)
        self._client = self._create_client()

    def _create_client(self) -> pynetbox.api:
        """Create pynetbox API client.

        Returns:
            Configured pynetbox API instance.

        Raises:
            NetBoxAPIError: If client creation fails.
        """
        try:
            api = pynetbox.api(
                url=self.config.url,
                token=self.config.token,
            )
            # Configure SSL verification
            if not self.config.verify_ssl:
                import urllib3

                urllib3.disable_warnings()
                api.http_session.verify = False

            return api
        except Exception as e:
            logger.error(f"Failed to create NetBox client: {e}")
            raise NetBoxAPIError(f"Failed to create NetBox client: {e}")

    def _retry_with_backoff(
        self, func: Any, *args: Any, max_retries: int | None = None, **kwargs: Any
    ) -> Any:
        """Execute function with exponential backoff retry logic.

        Args:
            func: Function to execute.
            *args: Positional arguments for the function.
            max_retries: Maximum number of retries. Uses config value if not specified.
            **kwargs: Keyword arguments for the function.

        Returns:
            Result of the function call.

        Raises:
            NetBoxAPIError: If all retries are exhausted.
        """
        retries = max_retries if max_retries is not None else self.config.max_retries
        last_exception = None

        for attempt in range(retries + 1):
            try:
                # Acquire rate limit token
                self.rate_limiter.acquire()

                # Execute the function
                return func(*args, **kwargs)

            except pynetbox.core.query.RequestError as e:
                last_exception = e
                logger.warning(f"NetBox API request failed (attempt {attempt + 1}): {e}")

                if attempt < retries:
                    wait_time = 2**attempt  # Exponential backoff: 1, 2, 4, 8...
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries ({retries}) exhausted")

            except RequestException as e:
                last_exception = e
                logger.warning(f"Request exception (attempt {attempt + 1}): {e}")

                if attempt < retries:
                    wait_time = 2**attempt
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries ({retries}) exhausted")

            except Exception as e:
                logger.error(f"Unexpected error during API call: {e}")
                raise NetBoxAPIError(f"Unexpected error: {e}")

        # All retries exhausted
        error_msg = f"Failed after {retries} retries: {last_exception}"
        raise NetBoxAPIError(error_msg)

    def get(self, endpoint: str, **params: Any) -> Any:
        """Perform GET request to NetBox API.

        Args:
            endpoint: API endpoint to query.
            **params: Query parameters.

        Returns:
            API response data.

        Raises:
            NetBoxAPIError: If the request fails.
        """
        try:
            endpoint_obj = getattr(self._client, endpoint)
            return self._retry_with_backoff(endpoint_obj.all, **params)
        except AttributeError:
            raise NetBoxAPIError(f"Invalid endpoint: {endpoint}")

    def create(self, endpoint: str, data: dict[str, Any]) -> Any:
        """Create a new object in NetBox.

        Args:
            endpoint: API endpoint.
            data: Object data.

        Returns:
            Created object.

        Raises:
            NetBoxAPIError: If the creation fails.
        """
        try:
            endpoint_obj = getattr(self._client, endpoint)
            return self._retry_with_backoff(endpoint_obj.create, data)
        except AttributeError:
            raise NetBoxAPIError(f"Invalid endpoint: {endpoint}")

    def bulk_create(self, endpoint: str, data: list[dict[str, Any]]) -> list[Any]:
        """Bulk create objects in NetBox.

        Args:
            endpoint: API endpoint.
            data: List of object data dictionaries.

        Returns:
            List of created objects.

        Raises:
            NetBoxAPIError: If the bulk creation fails.
        """
        try:
            endpoint_obj = getattr(self._client, endpoint)
            return self._retry_with_backoff(endpoint_obj.create, data)
        except AttributeError:
            raise NetBoxAPIError(f"Invalid endpoint: {endpoint}")

    def update(self, endpoint: str, obj_id: int, data: dict[str, Any]) -> Any:
        """Update an existing object in NetBox.

        Args:
            endpoint: API endpoint.
            obj_id: Object ID.
            data: Updated object data.

        Returns:
            Updated object.

        Raises:
            NetBoxAPIError: If the update fails.
        """
        try:
            endpoint_obj = getattr(self._client, endpoint)
            obj = self._retry_with_backoff(endpoint_obj.get, obj_id)
            for key, value in data.items():
                setattr(obj, key, value)
            return self._retry_with_backoff(obj.save)
        except AttributeError:
            raise NetBoxAPIError(f"Invalid endpoint: {endpoint}")

    def delete(self, endpoint: str, obj_id: int) -> bool:
        """Delete an object from NetBox.

        Args:
            endpoint: API endpoint.
            obj_id: Object ID.

        Returns:
            True if deletion was successful.

        Raises:
            NetBoxAPIError: If the deletion fails.
        """
        try:
            endpoint_obj = getattr(self._client, endpoint)
            obj = self._retry_with_backoff(endpoint_obj.get, obj_id)
            return self._retry_with_backoff(obj.delete)
        except AttributeError:
            raise NetBoxAPIError(f"Invalid endpoint: {endpoint}")

    @property
    def client(self) -> pynetbox.api:
        """Get underlying pynetbox client.

        Returns:
            pynetbox API instance.
        """
        return self._client
