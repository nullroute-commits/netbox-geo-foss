"""Unit tests for src.utils.health module."""


class TestReadinessCheck:
    """Tests for the readiness endpoint."""

    def test_readiness_returns_ready(self, client) -> None:
        """Test readiness endpoint returns ready=True."""
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json() == {"ready": True}


class TestLivenessCheck:
    """Tests for the liveness endpoint."""

    def test_liveness_returns_alive(self, client) -> None:
        """Test liveness endpoint returns alive=True."""
        response = client.get("/live")
        assert response.status_code == 200
        assert response.json() == {"alive": True}
