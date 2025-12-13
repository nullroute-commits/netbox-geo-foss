"""Custom exceptions for NetBox Geographic Data Integration."""


class NetBoxGeoError(Exception):
    """Base exception for all netbox-geo errors."""

    pass


class NetBoxAPIError(NetBoxGeoError):
    """Exception raised for NetBox API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize NetBoxAPIError.

        Args:
            message: Error message describing the API error.
            status_code: HTTP status code returned by the API.
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class RateLimitError(NetBoxGeoError):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: float | None = None
    ) -> None:
        """Initialize RateLimitError.

        Args:
            message: Error message describing the rate limit error.
            retry_after: Number of seconds to wait before retrying.
        """
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


class DataValidationError(NetBoxGeoError):
    """Exception raised for data validation errors."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize DataValidationError.

        Args:
            message: Error message describing the validation error.
            field: Name of the field that failed validation.
        """
        self.message = message
        self.field = field
        super().__init__(self.message)


class ImportError(NetBoxGeoError):
    """Exception raised during data import operations."""

    def __init__(
        self, message: str, source: str | None = None, record_id: str | None = None
    ) -> None:
        """Initialize ImportError.

        Args:
            message: Error message describing the import error.
            source: Name of the data source where the error occurred.
            record_id: Identifier of the record that failed to import.
        """
        self.message = message
        self.source = source
        self.record_id = record_id
        super().__init__(self.message)


class ConfigurationError(NetBoxGeoError):
    """Exception raised for configuration errors."""

    pass


class CacheError(NetBoxGeoError):
    """Exception raised for cache-related errors."""

    pass


class DatabaseError(NetBoxGeoError):
    """Exception raised for database-related errors."""

    pass
