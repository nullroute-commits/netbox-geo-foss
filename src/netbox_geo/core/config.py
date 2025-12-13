"""Configuration management using Pydantic v2."""

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class NetBoxConfig(BaseSettings):
    """NetBox API configuration."""

    url: str = Field(..., description="NetBox instance URL")
    token: str = Field(..., description="NetBox API token")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    timeout: int = Field(30, description="Request timeout in seconds", ge=1, le=300)
    max_retries: int = Field(3, description="Maximum number of retries", ge=0, le=10)
    api_version: str = Field("3.7", description="NetBox API version")

    model_config = SettingsConfigDict(
        env_prefix="NETBOX_",
        case_sensitive=False,
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate NetBox URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("NetBox URL must start with http:// or https://")
        return v.rstrip("/")


class DataSourceConfig(BaseSettings):
    """Geographic data source configuration."""

    geonames_username: str = Field(..., description="GeoNames username")
    geonames_api_url: str = Field(
        "https://api.geonames.org", description="GeoNames API URL"
    )
    naturalearth_data_url: str = Field(
        "https://www.naturalearthdata.com/downloads/",
        description="Natural Earth data URL",
    )
    osm_api_url: str = Field(
        "https://nominatim.openstreetmap.org", description="OpenStreetMap API URL"
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
    )


class DataManagementConfig(BaseSettings):
    """Data management configuration."""

    cache_dir: str = Field("./cache", description="Cache directory path")
    update_interval_days: int = Field(
        30, description="Data update interval in days", ge=1, le=365
    )
    batch_size: int = Field(
        1000, description="Batch size for bulk operations", ge=1, le=10000
    )
    min_city_population: int = Field(
        15000, description="Minimum city population to import", ge=0
    )

    model_config = SettingsConfigDict(
        env_prefix="DATA_",
        case_sensitive=False,
    )


class PerformanceConfig(BaseSettings):
    """Performance and rate limiting configuration."""

    rate_limit_calls_per_minute: int = Field(
        100, description="Maximum API calls per minute", ge=1, le=1000
    )
    worker_threads: int = Field(
        4, description="Number of worker threads", ge=1, le=32
    )
    async_enabled: bool = Field(True, description="Enable async operations")

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
    )


class AppSettings(BaseSettings):
    """Global application settings."""

    app_name: str = Field("netbox-geo-foss", description="Application name")
    app_env: Literal["development", "staging", "production"] = Field(
        "development", description="Application environment"
    )
    app_debug: bool = Field(False, description="Debug mode")
    app_version: str = Field("1.0.0", description="Application version")

    # Nested configurations
    netbox: NetBoxConfig
    data_sources: DataSourceConfig
    data_management: DataManagementConfig
    performance: PerformanceConfig

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def load(cls) -> "AppSettings":
        """Load application settings from environment.

        Returns:
            Configured AppSettings instance.
        """
        return cls(
            netbox=NetBoxConfig(),
            data_sources=DataSourceConfig(),
            data_management=DataManagementConfig(),
            performance=PerformanceConfig(),
        )


# Global settings instance
settings: AppSettings | None = None


def get_settings() -> AppSettings:
    """Get or create global settings instance.

    Returns:
        Global AppSettings instance.
    """
    global settings
    if settings is None:
        settings = AppSettings.load()
    return settings
