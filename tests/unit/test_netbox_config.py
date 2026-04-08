"""Unit tests for netbox_geo.core.config module."""

import pytest
from pydantic import ValidationError

from netbox_geo.core.config import (
    AppSettings,
    DataManagementConfig,
    DataSourceConfig,
    NetBoxConfig,
    PerformanceConfig,
)


class TestNetBoxConfig:
    """Tests for NetBoxConfig."""

    def test_valid_https_url(self) -> None:
        """Test NetBoxConfig accepts valid HTTPS URLs."""
        config = NetBoxConfig(
            url="https://netbox.example.com",
            token="abc123",
        )
        assert config.url == "https://netbox.example.com"
        assert config.token == "abc123"

    def test_valid_http_url(self) -> None:
        """Test NetBoxConfig accepts valid HTTP URLs."""
        config = NetBoxConfig(
            url="http://netbox.local",
            token="abc123",
        )
        assert config.url == "http://netbox.local"

    def test_url_trailing_slash_stripped(self) -> None:
        """Test that trailing slash is stripped from URL."""
        config = NetBoxConfig(
            url="https://netbox.example.com/",
            token="abc123",
        )
        assert config.url == "https://netbox.example.com"

    def test_invalid_url_rejected(self) -> None:
        """Test that invalid URL is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NetBoxConfig(
                url="ftp://netbox.example.com",
                token="abc123",
            )
        assert "NetBox URL must start with http:// or https://" in str(exc_info.value)

    def test_default_values(self) -> None:
        """Test default values for optional fields."""
        config = NetBoxConfig(
            url="https://netbox.example.com",
            token="abc123",
        )
        assert config.verify_ssl is True
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.api_version == "4.4"

    def test_custom_timeout(self) -> None:
        """Test custom timeout value."""
        config = NetBoxConfig(
            url="https://netbox.example.com",
            token="abc123",
            timeout=60,
        )
        assert config.timeout == 60

    def test_timeout_min_boundary(self) -> None:
        """Test timeout minimum boundary validation."""
        with pytest.raises(ValidationError):
            NetBoxConfig(
                url="https://netbox.example.com",
                token="abc123",
                timeout=0,
            )

    def test_timeout_max_boundary(self) -> None:
        """Test timeout maximum boundary validation."""
        with pytest.raises(ValidationError):
            NetBoxConfig(
                url="https://netbox.example.com",
                token="abc123",
                timeout=301,
            )

    def test_max_retries_boundary(self) -> None:
        """Test max_retries boundary validation."""
        with pytest.raises(ValidationError):
            NetBoxConfig(
                url="https://netbox.example.com",
                token="abc123",
                max_retries=11,
            )

    def test_ssl_verification_disabled(self) -> None:
        """Test SSL verification can be disabled."""
        config = NetBoxConfig(
            url="https://netbox.example.com",
            token="abc123",
            verify_ssl=False,
        )
        assert config.verify_ssl is False

    def test_missing_url_raises(self) -> None:
        """Test that missing URL raises validation error."""
        with pytest.raises(ValidationError):
            NetBoxConfig(token="abc123")

    def test_missing_token_raises(self) -> None:
        """Test that missing token raises validation error."""
        with pytest.raises(ValidationError):
            NetBoxConfig(url="https://netbox.example.com")


class TestDataSourceConfig:
    """Tests for DataSourceConfig."""

    def test_default_urls(self) -> None:
        """Test default URL values."""
        config = DataSourceConfig(geonames_username="testuser")
        assert config.geonames_api_url == "https://api.geonames.org"
        assert "naturalearthdata.com" in config.naturalearth_data_url
        assert "nominatim.openstreetmap.org" in config.osm_api_url

    def test_custom_geonames_username(self) -> None:
        """Test custom GeoNames username."""
        config = DataSourceConfig(geonames_username="myuser")
        assert config.geonames_username == "myuser"

    def test_missing_geonames_username_raises(self) -> None:
        """Test that missing GeoNames username raises."""
        with pytest.raises(ValidationError):
            DataSourceConfig()


class TestDataManagementConfig:
    """Tests for DataManagementConfig."""

    def test_default_values(self) -> None:
        """Test default values."""
        config = DataManagementConfig()
        assert config.cache_dir == "./cache"
        assert config.update_interval_days == 30
        assert config.batch_size == 1000
        assert config.min_city_population == 15000

    def test_custom_batch_size(self) -> None:
        """Test custom batch size."""
        config = DataManagementConfig(batch_size=500)
        assert config.batch_size == 500

    def test_batch_size_min_boundary(self) -> None:
        """Test batch size minimum boundary."""
        with pytest.raises(ValidationError):
            DataManagementConfig(batch_size=0)

    def test_batch_size_max_boundary(self) -> None:
        """Test batch size maximum boundary."""
        with pytest.raises(ValidationError):
            DataManagementConfig(batch_size=10001)

    def test_update_interval_min_boundary(self) -> None:
        """Test update interval minimum boundary."""
        with pytest.raises(ValidationError):
            DataManagementConfig(update_interval_days=0)

    def test_update_interval_max_boundary(self) -> None:
        """Test update interval maximum boundary."""
        with pytest.raises(ValidationError):
            DataManagementConfig(update_interval_days=366)

    def test_min_city_population_zero_allowed(self) -> None:
        """Test that zero is allowed for min_city_population."""
        config = DataManagementConfig(min_city_population=0)
        assert config.min_city_population == 0


class TestPerformanceConfig:
    """Tests for PerformanceConfig."""

    def test_default_values(self) -> None:
        """Test default values."""
        config = PerformanceConfig()
        assert config.rate_limit_calls_per_minute == 100
        assert config.worker_threads == 4
        assert config.async_enabled is True

    def test_custom_rate_limit(self) -> None:
        """Test custom rate limit."""
        config = PerformanceConfig(rate_limit_calls_per_minute=50)
        assert config.rate_limit_calls_per_minute == 50

    def test_rate_limit_min_boundary(self) -> None:
        """Test rate limit minimum boundary."""
        with pytest.raises(ValidationError):
            PerformanceConfig(rate_limit_calls_per_minute=0)

    def test_rate_limit_max_boundary(self) -> None:
        """Test rate limit maximum boundary."""
        with pytest.raises(ValidationError):
            PerformanceConfig(rate_limit_calls_per_minute=1001)

    def test_worker_threads_boundaries(self) -> None:
        """Test worker threads boundaries."""
        with pytest.raises(ValidationError):
            PerformanceConfig(worker_threads=0)
        with pytest.raises(ValidationError):
            PerformanceConfig(worker_threads=33)

    def test_async_disabled(self) -> None:
        """Test async can be disabled."""
        config = PerformanceConfig(async_enabled=False)
        assert config.async_enabled is False


class TestAppSettings:
    """Tests for AppSettings."""

    def _make_settings(self, **overrides):
        """Helper to build AppSettings with defaults."""
        defaults = {
            "netbox": NetBoxConfig(
                url="https://netbox.example.com",
                token="test-token",
            ),
            "data_sources": DataSourceConfig(geonames_username="testuser"),
            "data_management": DataManagementConfig(),
            "performance": PerformanceConfig(),
        }
        defaults.update(overrides)
        return AppSettings(**defaults)

    def test_default_app_settings(self) -> None:
        """Test default AppSettings values."""
        settings = self._make_settings()
        assert settings.app_name == "netbox-geo-foss"
        assert settings.app_env == "development"
        assert settings.app_debug is False
        assert settings.app_version == "1.0.0"

    def test_production_environment(self) -> None:
        """Test production environment setting."""
        settings = self._make_settings(app_env="production")
        assert settings.app_env == "production"

    def test_staging_environment(self) -> None:
        """Test staging environment setting."""
        settings = self._make_settings(app_env="staging")
        assert settings.app_env == "staging"

    def test_invalid_environment_rejected(self) -> None:
        """Test that invalid environment is rejected."""
        with pytest.raises(ValidationError):
            self._make_settings(app_env="invalid")

    def test_debug_mode(self) -> None:
        """Test debug mode setting."""
        settings = self._make_settings(app_debug=True)
        assert settings.app_debug is True

    def test_nested_netbox_config(self) -> None:
        """Test nested NetBox configuration is accessible."""
        settings = self._make_settings()
        assert settings.netbox.url == "https://netbox.example.com"
        assert settings.netbox.token == "test-token"

    def test_nested_data_sources(self) -> None:
        """Test nested data sources configuration."""
        settings = self._make_settings()
        assert settings.data_sources.geonames_username == "testuser"

    def test_nested_data_management(self) -> None:
        """Test nested data management configuration."""
        settings = self._make_settings()
        assert settings.data_management.batch_size == 1000

    def test_nested_performance(self) -> None:
        """Test nested performance configuration."""
        settings = self._make_settings()
        assert settings.performance.rate_limit_calls_per_minute == 100
