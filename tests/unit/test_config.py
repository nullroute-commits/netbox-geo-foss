"""Unit tests for configuration module."""

import pytest
from pydantic import ValidationError

from src.core.config import Settings


class TestSettings:
    """Test Settings configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings(
            secret_key="test-key",
            database_url="postgresql://user:pass@localhost/db",
            redis_url="redis://localhost:6379/0",
        )

        assert settings.app_name == "Enterprise App"
        assert settings.environment == "development"
        assert settings.debug is False
        assert settings.api_port == 8000

    def test_environment_validation(self):
        """Test environment validation."""
        # Valid environments
        for env in ["development", "testing", "staging", "production"]:
            settings = Settings(
                environment=env,
                secret_key="test-key",
                database_url="postgresql://user:pass@localhost/db",
                redis_url="redis://localhost:6379/0",
            )
            assert settings.environment == env

        # Invalid environment
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment="invalid",
                secret_key="test-key",
                database_url="postgresql://user:pass@localhost/db",
                redis_url="redis://localhost:6379/0",
            )
        assert "Environment must be one of" in str(exc_info.value)

    def test_allowed_origins_parsing(self):
        """Test allowed origins parsing from string."""
        # String input
        settings = Settings(
            secret_key="test-key",
            database_url="postgresql://user:pass@localhost/db",
            redis_url="redis://localhost:6379/0",
            allowed_origins="http://localhost:3000,http://localhost:8080",
        )
        assert settings.allowed_origins == ["http://localhost:3000", "http://localhost:8080"]

        # List input
        settings = Settings(
            secret_key="test-key",
            database_url="postgresql://user:pass@localhost/db",
            redis_url="redis://localhost:6379/0",
            allowed_origins=["http://example.com"],
        )
        assert settings.allowed_origins == ["http://example.com"]

    def test_environment_properties(self):
        """Test environment property methods."""
        # Production
        settings = Settings(
            environment="production",
            secret_key="test-key",
            database_url="postgresql://user:pass@localhost/db",
            redis_url="redis://localhost:6379/0",
        )
        assert settings.is_production is True
        assert settings.is_development is False
        assert settings.is_testing is False

        # Development
        settings.environment = "development"
        assert settings.is_production is False
        assert settings.is_development is True
        assert settings.is_testing is False

        # Testing
        settings.environment = "testing"
        assert settings.is_production is False
        assert settings.is_development is False
        assert settings.is_testing is True

    def test_required_fields(self, monkeypatch):
        """Test required fields validation."""
        # Clear environment variables that might interfere
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)
        
        # Missing secret_key
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                database_url="postgresql://user:pass@localhost/db",
                redis_url="redis://localhost:6379/0",
            )
        assert "secret_key" in str(exc_info.value)

        # Missing database_url
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                secret_key="test-key",
                redis_url="redis://localhost:6379/0",
            )
        assert "database_url" in str(exc_info.value)
