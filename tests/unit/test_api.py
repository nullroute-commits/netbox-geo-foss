"""Unit tests for src.api.main module."""

import pytest


class TestRootEndpoint:
    """Tests for the root / endpoint."""

    def test_root_returns_200(self, client) -> None:
        """Test root endpoint returns 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_contains_message(self, client) -> None:
        """Test root endpoint contains welcome message."""
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert "Welcome" in data["message"]

    def test_root_contains_version(self, client) -> None:
        """Test root endpoint contains version."""
        response = client.get("/")
        data = response.json()
        assert "version" in data

    def test_root_contains_environment(self, client) -> None:
        """Test root endpoint contains environment."""
        response = client.get("/")
        data = response.json()
        assert "environment" in data


class TestVersionEndpoint:
    """Tests for the /api/v1/version endpoint."""

    def test_version_returns_200(self, client) -> None:
        """Test version endpoint returns 200."""
        response = client.get("/api/v1/version")
        assert response.status_code == 200

    def test_version_contains_required_fields(self, client) -> None:
        """Test version endpoint contains required fields."""
        response = client.get("/api/v1/version")
        data = response.json()
        assert "version" in data
        assert "environment" in data
        assert "api_version" in data
        assert "commit_sha" in data
