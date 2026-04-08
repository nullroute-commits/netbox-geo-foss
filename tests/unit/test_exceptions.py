"""Unit tests for core exceptions."""

from netbox_geo.core.exceptions import (
    CacheError,
    ConfigurationError,
    DatabaseError,
    DataValidationError,
    ImportError,
    NetBoxAPIError,
    NetBoxGeoError,
    RateLimitError,
)


def test_netbox_geo_error_base() -> None:
    """Test NetBoxGeoError base exception."""
    error = NetBoxGeoError("base error")
    assert str(error) == "base error"
    assert isinstance(error, Exception)


def test_netbox_api_error() -> None:
    """Test NetBoxAPIError creation and attributes."""
    error = NetBoxAPIError("Test error", status_code=500)
    assert str(error) == "Test error"
    assert error.status_code == 500


def test_netbox_api_error_no_status_code() -> None:
    """Test NetBoxAPIError with no status code."""
    error = NetBoxAPIError("Test error")
    assert error.status_code is None


def test_netbox_api_error_inherits_base() -> None:
    """Test NetBoxAPIError inherits from NetBoxGeoError."""
    error = NetBoxAPIError("test")
    assert isinstance(error, NetBoxGeoError)


def test_rate_limit_error() -> None:
    """Test RateLimitError creation and attributes."""
    error = RateLimitError("Rate limit exceeded", retry_after=60.0)
    assert "Rate limit exceeded" in str(error)
    assert error.retry_after == 60.0


def test_rate_limit_error_defaults() -> None:
    """Test RateLimitError default values."""
    error = RateLimitError()
    assert "Rate limit exceeded" in str(error)
    assert error.retry_after is None


def test_data_validation_error() -> None:
    """Test DataValidationError creation and attributes."""
    error = DataValidationError("Invalid data", field="country_code")
    assert "Invalid data" in str(error)
    assert error.field == "country_code"


def test_data_validation_error_no_field() -> None:
    """Test DataValidationError with no field."""
    error = DataValidationError("Invalid data")
    assert error.field is None


def test_import_error() -> None:
    """Test ImportError creation and attributes."""
    error = ImportError("Import failed", source="geonames", record_id="123")
    assert "Import failed" in str(error)
    assert error.source == "geonames"
    assert error.record_id == "123"


def test_import_error_no_optional_fields() -> None:
    """Test ImportError with no optional fields."""
    error = ImportError("Import failed")
    assert error.source is None
    assert error.record_id is None


def test_configuration_error() -> None:
    """Test ConfigurationError creation."""
    error = ConfigurationError("Bad config")
    assert str(error) == "Bad config"
    assert isinstance(error, NetBoxGeoError)


def test_cache_error() -> None:
    """Test CacheError creation."""
    error = CacheError("Cache miss")
    assert str(error) == "Cache miss"
    assert isinstance(error, NetBoxGeoError)


def test_database_error() -> None:
    """Test DatabaseError creation."""
    error = DatabaseError("Connection failed")
    assert str(error) == "Connection failed"
    assert isinstance(error, NetBoxGeoError)
