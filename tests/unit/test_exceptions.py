"""Unit tests for core exceptions."""

from netbox_geo.core.exceptions import (
    DataValidationError,
    ImportError,
    NetBoxAPIError,
    RateLimitError,
)


def test_netbox_api_error() -> None:
    """Test NetBoxAPIError creation and attributes."""
    error = NetBoxAPIError("Test error", status_code=500)
    assert str(error) == "Test error"
    assert error.status_code == 500


def test_rate_limit_error() -> None:
    """Test RateLimitError creation and attributes."""
    error = RateLimitError("Rate limit exceeded", retry_after=60.0)
    assert "Rate limit exceeded" in str(error)
    assert error.retry_after == 60.0


def test_data_validation_error() -> None:
    """Test DataValidationError creation and attributes."""
    error = DataValidationError("Invalid data", field="country_code")
    assert "Invalid data" in str(error)
    assert error.field == "country_code"


def test_import_error() -> None:
    """Test ImportError creation and attributes."""
    error = ImportError("Import failed", source="geonames", record_id="123")
    assert "Import failed" in str(error)
    assert error.source == "geonames"
    assert error.record_id == "123"
