"""Unit tests for the active netbox_geo configuration module."""

import pytest
from pydantic import ValidationError

import netbox_geo.core.config as config_module
from netbox_geo.core.config import AppSettings, NetBoxConfig, get_settings


def test_netbox_config_normalizes_url() -> None:
    """Verify that NetBoxConfig strips a trailing slash from the URL."""
    config = NetBoxConfig(url="https://netbox.example.com/", token="test-token")

    assert config.url == "https://netbox.example.com"
    assert config.verify_ssl is True
    assert config.timeout == 30


def test_netbox_config_requires_http_scheme() -> None:
    """Verify that NetBoxConfig rejects URLs without an HTTP scheme."""
    with pytest.raises(ValidationError, match="NetBox URL must start with http:// or https://"):
        NetBoxConfig(url="netbox.example.com", token="test-token")


def test_app_settings_loads_nested_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """AppSettings.load should build nested settings objects from environment variables."""
    monkeypatch.setenv("NETBOX_URL", "https://netbox.example.com/api/")
    monkeypatch.setenv("NETBOX_TOKEN", "super-secret")
    monkeypatch.setenv("GEONAMES_USERNAME", "geotest")
    monkeypatch.setenv("DATA_BATCH_SIZE", "250")

    settings = AppSettings.load()

    assert settings.app_name == "netbox-geo-foss"
    assert settings.app_env == "development"
    assert settings.netbox.url == "https://netbox.example.com/api"
    assert settings.netbox.token == "super-secret"
    assert settings.data_sources.geonames_username == "geotest"
    assert settings.data_management.batch_size == 250
    assert settings.performance.rate_limit_calls_per_minute == 100


def test_app_settings_validate_required_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """AppSettings.load should fail when required nested settings are missing."""
    monkeypatch.delenv("NETBOX_URL", raising=False)
    monkeypatch.delenv("NETBOX_TOKEN", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        AppSettings.load()

    error_text = str(exc_info.value)
    assert "url" in error_text
    assert "token" in error_text


def test_data_source_config_requires_geonames_username(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that DataSourceConfig enforces its required GeoNames username."""
    monkeypatch.setenv("NETBOX_URL", "https://netbox.example.com")
    monkeypatch.setenv("NETBOX_TOKEN", "super-secret")
    monkeypatch.delenv("GEONAMES_USERNAME", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        AppSettings.load()

    assert "geonames_username" in str(exc_info.value)


def test_get_settings_returns_cached_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_settings should reuse the module-level settings instance once loaded."""
    monkeypatch.setenv("NETBOX_URL", "https://netbox.example.com")
    monkeypatch.setenv("NETBOX_TOKEN", "super-secret")
    monkeypatch.setenv("GEONAMES_USERNAME", "geotest")
    monkeypatch.setattr(config_module, "settings", None)

    first = get_settings()
    second = get_settings()

    assert first is second
    assert second.netbox.url == "https://netbox.example.com"
