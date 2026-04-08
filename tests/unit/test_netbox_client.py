"""Unit tests for netbox_geo.netbox.client module."""

from unittest.mock import MagicMock, patch

import pytest

from netbox_geo.core.config import NetBoxConfig
from netbox_geo.core.exceptions import NetBoxAPIError
from netbox_geo.netbox.client import NetBoxClient


@pytest.fixture
def netbox_config() -> NetBoxConfig:
    """Create a NetBoxConfig for testing."""
    return NetBoxConfig(
        url="https://netbox.example.com",
        token="test-token",
        verify_ssl=True,
        timeout=30,
        max_retries=2,
    )


@pytest.fixture
def mock_pynetbox_api():
    """Mock pynetbox.api to avoid real API calls."""
    with patch("netbox_geo.netbox.client.pynetbox.api") as mock_api:
        mock_instance = MagicMock()
        mock_api.return_value = mock_instance
        yield mock_api, mock_instance


@pytest.fixture
def client(netbox_config, mock_pynetbox_api):
    """Create a NetBoxClient with mocked pynetbox."""
    _, mock_instance = mock_pynetbox_api
    return NetBoxClient(config=netbox_config, rate_limit_calls_per_minute=1000)


class TestNetBoxClientInit:
    """Tests for NetBoxClient initialization."""

    def test_init_creates_client(self, netbox_config, mock_pynetbox_api) -> None:
        """Test that __init__ creates a pynetbox client."""
        mock_api, _ = mock_pynetbox_api
        NetBoxClient(config=netbox_config)
        mock_api.assert_called_once_with(
            url=netbox_config.url,
            token=netbox_config.token,
        )

    def test_init_sets_rate_limiter(self, netbox_config, mock_pynetbox_api) -> None:
        """Test that __init__ configures rate limiter."""
        client = NetBoxClient(config=netbox_config, rate_limit_calls_per_minute=50)
        assert client.rate_limiter.calls_per_minute == 50

    def test_init_default_rate_limit(self, netbox_config, mock_pynetbox_api) -> None:
        """Test default rate limit value."""
        client = NetBoxClient(config=netbox_config)
        assert client.rate_limiter.calls_per_minute == 100

    def test_init_stores_config(self, netbox_config, mock_pynetbox_api) -> None:
        """Test that config is stored."""
        client = NetBoxClient(config=netbox_config)
        assert client.config is netbox_config

    def test_init_ssl_disabled(self, mock_pynetbox_api) -> None:
        """Test client creation with SSL verification disabled."""
        config = NetBoxConfig(
            url="https://netbox.example.com",
            token="test-token",
            verify_ssl=False,
        )
        NetBoxClient(config=config)
        _, mock_instance = mock_pynetbox_api
        # When SSL is disabled, http_session.verify should be set to False
        assert mock_instance.http_session.verify is False

    def test_init_failure_raises_netbox_api_error(self) -> None:
        """Test that client creation failure raises NetBoxAPIError."""
        config = NetBoxConfig(
            url="https://netbox.example.com",
            token="test-token",
        )
        with (
            patch(
                "netbox_geo.netbox.client.pynetbox.api",
                side_effect=Exception("Connection failed"),
            ),
            pytest.raises(NetBoxAPIError, match="Failed to create NetBox client"),
        ):
            NetBoxClient(config=config)


class TestNetBoxClientProperty:
    """Tests for NetBoxClient.client property."""

    def test_client_property_returns_pynetbox_instance(self, client, mock_pynetbox_api) -> None:
        """Test that client property returns the pynetbox API instance."""
        _, mock_instance = mock_pynetbox_api
        assert client.client is mock_instance


class TestNetBoxClientGet:
    """Tests for NetBoxClient.get method."""

    def test_get_calls_endpoint(self, client, mock_pynetbox_api) -> None:
        """Test that get calls the correct endpoint."""
        _, mock_instance = mock_pynetbox_api
        mock_endpoint = MagicMock()
        mock_endpoint.all.return_value = [{"id": 1, "name": "test"}]
        mock_instance.dcim = mock_endpoint

        result = client.get("dcim")
        assert result is not None
        mock_endpoint.all.assert_called()

    def test_get_invalid_endpoint_raises(self, client, mock_pynetbox_api) -> None:
        """Test that invalid endpoint raises NetBoxAPIError."""
        _, mock_instance = mock_pynetbox_api
        # Make getattr raise AttributeError for unknown endpoint
        mock_instance.configure_mock(**{"nonexistent": None})
        del mock_instance.nonexistent

        with pytest.raises(NetBoxAPIError, match="Invalid endpoint"):
            client.get("nonexistent")


class TestNetBoxClientCreate:
    """Tests for NetBoxClient.create method."""

    def test_create_calls_endpoint(self, client, mock_pynetbox_api) -> None:
        """Test that create calls the correct endpoint."""
        _, mock_instance = mock_pynetbox_api
        mock_endpoint = MagicMock()
        mock_endpoint.create.return_value = {"id": 1, "name": "new-site"}
        mock_instance.dcim = mock_endpoint

        data = {"name": "new-site"}
        result = client.create("dcim", data)
        assert result is not None
        mock_endpoint.create.assert_called()

    def test_create_invalid_endpoint_raises(self, client, mock_pynetbox_api) -> None:
        """Test that invalid endpoint raises NetBoxAPIError."""
        _, mock_instance = mock_pynetbox_api
        del mock_instance.nonexistent

        with pytest.raises(NetBoxAPIError, match="Invalid endpoint"):
            client.create("nonexistent", {"name": "test"})


class TestNetBoxClientBulkCreate:
    """Tests for NetBoxClient.bulk_create method."""

    def test_bulk_create_calls_endpoint(self, client, mock_pynetbox_api) -> None:
        """Test that bulk_create calls the correct endpoint."""
        _, mock_instance = mock_pynetbox_api
        mock_endpoint = MagicMock()
        mock_endpoint.create.return_value = [{"id": 1}, {"id": 2}]
        mock_instance.dcim = mock_endpoint

        data = [{"name": "site1"}, {"name": "site2"}]
        result = client.bulk_create("dcim", data)
        assert result is not None
        mock_endpoint.create.assert_called()

    def test_bulk_create_invalid_endpoint_raises(self, client, mock_pynetbox_api) -> None:
        """Test that invalid endpoint raises NetBoxAPIError."""
        _, mock_instance = mock_pynetbox_api
        del mock_instance.nonexistent

        with pytest.raises(NetBoxAPIError, match="Invalid endpoint"):
            client.bulk_create("nonexistent", [{"name": "test"}])


class TestNetBoxClientUpdate:
    """Tests for NetBoxClient.update method."""

    def test_update_calls_endpoint(self, client, mock_pynetbox_api) -> None:
        """Test that update retrieves and saves object."""
        _, mock_instance = mock_pynetbox_api
        mock_endpoint = MagicMock()
        mock_obj = MagicMock()
        mock_obj.save.return_value = True
        mock_endpoint.get.return_value = mock_obj
        mock_instance.dcim = mock_endpoint

        result = client.update("dcim", 1, {"name": "updated"})
        assert result is not None
        mock_endpoint.get.assert_called()
        assert mock_obj.name == "updated"

    def test_update_invalid_endpoint_raises(self, client, mock_pynetbox_api) -> None:
        """Test that invalid endpoint raises NetBoxAPIError."""
        _, mock_instance = mock_pynetbox_api
        del mock_instance.nonexistent

        with pytest.raises(NetBoxAPIError, match="Invalid endpoint"):
            client.update("nonexistent", 1, {"name": "test"})


class TestNetBoxClientDelete:
    """Tests for NetBoxClient.delete method."""

    def test_delete_calls_endpoint(self, client, mock_pynetbox_api) -> None:
        """Test that delete retrieves and deletes object."""
        _, mock_instance = mock_pynetbox_api
        mock_endpoint = MagicMock()
        mock_obj = MagicMock()
        mock_obj.delete.return_value = True
        mock_endpoint.get.return_value = mock_obj
        mock_instance.dcim = mock_endpoint

        result = client.delete("dcim", 1)
        assert result is not None
        mock_endpoint.get.assert_called()
        mock_obj.delete.assert_called()

    def test_delete_invalid_endpoint_raises(self, client, mock_pynetbox_api) -> None:
        """Test that invalid endpoint raises NetBoxAPIError."""
        _, mock_instance = mock_pynetbox_api
        del mock_instance.nonexistent

        with pytest.raises(NetBoxAPIError, match="Invalid endpoint"):
            client.delete("nonexistent", 1)


class TestRetryWithBackoff:
    """Tests for NetBoxClient._retry_with_backoff."""

    def test_successful_call_no_retry(self, client) -> None:
        """Test that successful call returns without retrying."""
        func = MagicMock(return_value="success")
        result = client._retry_with_backoff(func)
        assert result == "success"
        func.assert_called_once()

    def test_retry_on_request_exception(self, client) -> None:
        """Test that RequestException triggers retry."""
        from requests.exceptions import RequestException

        func = MagicMock(side_effect=[RequestException("fail"), "success"])
        with patch("netbox_geo.netbox.client.time.sleep"):
            result = client._retry_with_backoff(func)
        assert result == "success"
        assert func.call_count == 2

    def test_max_retries_exhausted(self, client) -> None:
        """Test that exhausting retries raises NetBoxAPIError."""
        from requests.exceptions import RequestException

        func = MagicMock(side_effect=RequestException("always fails"))
        with (
            patch("netbox_geo.netbox.client.time.sleep"),
            pytest.raises(NetBoxAPIError, match="Failed after"),
        ):
            client._retry_with_backoff(func, max_retries=1)
        assert func.call_count == 2  # initial + 1 retry

    def test_unexpected_exception_raises_immediately(self, client) -> None:
        """Test that unexpected exceptions raise NetBoxAPIError immediately."""
        func = MagicMock(side_effect=ValueError("unexpected"))
        with pytest.raises(NetBoxAPIError, match="Unexpected error"):
            client._retry_with_backoff(func)
        func.assert_called_once()

    def test_custom_max_retries(self, client) -> None:
        """Test custom max_retries parameter."""
        from requests.exceptions import RequestException

        func = MagicMock(side_effect=RequestException("fail"))
        with patch("netbox_geo.netbox.client.time.sleep"), pytest.raises(NetBoxAPIError):
            client._retry_with_backoff(func, max_retries=0)
        func.assert_called_once()  # no retries, only initial call

    def test_retry_with_pynetbox_request_error(self, client) -> None:
        """Test retry on pynetbox RequestError."""
        import pynetbox.core.query

        # Create a mock request object that pynetbox.core.query.RequestError expects
        mock_req = MagicMock()
        mock_req.status_code = 500
        mock_req.error = "API error"
        mock_req.url = "https://netbox.example.com/api/"
        mock_req.json.return_value = {"detail": "error"}

        func = MagicMock(
            side_effect=[
                pynetbox.core.query.RequestError(mock_req),
                "success",
            ]
        )
        with patch("netbox_geo.netbox.client.time.sleep"):
            result = client._retry_with_backoff(func)
        assert result == "success"
        assert func.call_count == 2
