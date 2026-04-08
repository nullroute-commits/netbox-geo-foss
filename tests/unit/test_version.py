"""Unit tests for src.utils.version module."""

import os
from unittest.mock import patch

from src.utils.version import get_version_info


class TestGetVersionInfo:
    """Tests for get_version_info function."""

    def test_returns_dict(self) -> None:
        """Test that get_version_info returns a dictionary."""
        info = get_version_info()
        assert isinstance(info, dict)

    def test_contains_required_keys(self) -> None:
        """Test that result contains all required keys."""
        info = get_version_info()
        expected_keys = {
            "version",
            "environment",
            "commit_sha",
            "build_date",
            "build_number",
            "api_version",
        }
        assert expected_keys == set(info.keys())

    def test_api_version(self) -> None:
        """Test that API version is v1."""
        info = get_version_info()
        assert info["api_version"] == "v1"

    def test_default_commit_sha(self) -> None:
        """Test default commit SHA when env var not set."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("COMMIT_SHA", None)
            info = get_version_info()
            assert info["commit_sha"] == "unknown"

    def test_custom_commit_sha(self) -> None:
        """Test commit SHA from environment variable."""
        with patch.dict(os.environ, {"COMMIT_SHA": "abc123def"}):
            info = get_version_info()
            assert info["commit_sha"] == "abc123def"

    def test_default_build_number(self) -> None:
        """Test default build number when env var not set."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BUILD_NUMBER", None)
            info = get_version_info()
            assert info["build_number"] == "local"

    def test_custom_build_number(self) -> None:
        """Test build number from environment variable."""
        with patch.dict(os.environ, {"BUILD_NUMBER": "42"}):
            info = get_version_info()
            assert info["build_number"] == "42"

    def test_custom_build_date(self) -> None:
        """Test build date from environment variable."""
        with patch.dict(os.environ, {"BUILD_DATE": "2025-01-01T00:00:00"}):
            info = get_version_info()
            assert info["build_date"] == "2025-01-01T00:00:00"

    def test_build_date_default_is_iso_format(self) -> None:
        """Test that default build date is in ISO format."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BUILD_DATE", None)
            info = get_version_info()
            # ISO format should contain 'T' separator
            assert "T" in info["build_date"] or "-" in info["build_date"]
