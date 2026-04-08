"""Unit tests for netbox_geo.cli.main module."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from netbox_geo.cli.main import cli


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_settings():
    """Mock get_settings to avoid needing real config."""
    mock = MagicMock()
    mock.app_name = "netbox-geo-foss"
    mock.app_env = "development"
    mock.app_version = "1.0.0"
    mock.netbox = MagicMock()
    mock.netbox.url = "https://netbox.example.com"
    mock.netbox.api_version = "4.4"
    return mock


class TestCliGroup:
    """Tests for the CLI group."""

    def test_cli_help(self, runner) -> None:
        """Test CLI help output."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "geographic data" in result.output.lower()

    def test_cli_version(self, runner) -> None:
        """Test --version flag."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output


class TestImportDataCommand:
    """Tests for the import-data command."""

    def test_import_data_help(self, runner) -> None:
        """Test import-data help output."""
        result = runner.invoke(cli, ["import-data", "--help"])
        assert result.exit_code == 0
        assert "--source" in result.output
        assert "--batch-size" in result.output
        assert "--dry-run" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_import_data_default(self, mock_get_settings, runner, mock_settings) -> None:
        """Test import-data with default options."""
        mock_get_settings.return_value = mock_settings
        result = runner.invoke(cli, ["import-data"])
        assert result.exit_code == 0
        assert "Import completed successfully" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_import_data_with_source(self, mock_get_settings, runner, mock_settings) -> None:
        """Test import-data with specific source."""
        mock_get_settings.return_value = mock_settings
        result = runner.invoke(cli, ["import-data", "--source", "geonames"])
        assert result.exit_code == 0
        assert "geonames" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_import_data_dry_run(self, mock_get_settings, runner, mock_settings) -> None:
        """Test import-data with dry-run flag."""
        mock_get_settings.return_value = mock_settings
        result = runner.invoke(cli, ["import-data", "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_import_data_with_batch_size(self, mock_get_settings, runner, mock_settings) -> None:
        """Test import-data with custom batch size."""
        mock_get_settings.return_value = mock_settings
        result = runner.invoke(cli, ["import-data", "--batch-size", "500"])
        assert result.exit_code == 0

    def test_import_data_invalid_source(self, runner) -> None:
        """Test import-data with invalid source."""
        result = runner.invoke(cli, ["import-data", "--source", "invalid"])
        assert result.exit_code != 0

    @patch("netbox_geo.cli.main.get_settings")
    def test_import_data_settings_error(self, mock_get_settings, runner) -> None:
        """Test import-data when settings raise NetBoxGeoError."""
        from netbox_geo.core.exceptions import NetBoxGeoError

        mock_get_settings.side_effect = NetBoxGeoError("Config missing")
        result = runner.invoke(cli, ["import-data"])
        assert result.exit_code == 1
        assert "Error" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_import_data_unexpected_error(self, mock_get_settings, runner) -> None:
        """Test import-data when unexpected exception occurs."""
        mock_get_settings.side_effect = RuntimeError("Unexpected")
        result = runner.invoke(cli, ["import-data"])
        assert result.exit_code == 1
        assert "Unexpected error" in result.output


class TestSyncCommand:
    """Tests for the sync command."""

    def test_sync_help(self, runner) -> None:
        """Test sync help output."""
        result = runner.invoke(cli, ["sync", "--help"])
        assert result.exit_code == 0
        assert "--endpoint" in result.output
        assert "--force" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_sync_default(self, mock_get_settings, runner, mock_settings) -> None:
        """Test sync with default options."""
        mock_get_settings.return_value = mock_settings
        result = runner.invoke(cli, ["sync"])
        assert result.exit_code == 0
        assert "Synchronization completed" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_sync_with_endpoint(self, mock_get_settings, runner, mock_settings) -> None:
        """Test sync with specific endpoint."""
        mock_get_settings.return_value = mock_settings
        result = runner.invoke(cli, ["sync", "--endpoint", "dcim.sites"])
        assert result.exit_code == 0
        assert "dcim.sites" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_sync_force(self, mock_get_settings, runner, mock_settings) -> None:
        """Test sync with force flag."""
        mock_get_settings.return_value = mock_settings
        result = runner.invoke(cli, ["sync", "--force"])
        assert result.exit_code == 0
        assert "Forcing" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_sync_settings_error(self, mock_get_settings, runner) -> None:
        """Test sync when settings raise NetBoxGeoError."""
        from netbox_geo.core.exceptions import NetBoxGeoError

        mock_get_settings.side_effect = NetBoxGeoError("Config missing")
        result = runner.invoke(cli, ["sync"])
        assert result.exit_code == 1

    @patch("netbox_geo.cli.main.get_settings")
    def test_sync_unexpected_error(self, mock_get_settings, runner) -> None:
        """Test sync when unexpected exception occurs."""
        mock_get_settings.side_effect = RuntimeError("Unexpected")
        result = runner.invoke(cli, ["sync"])
        assert result.exit_code == 1


class TestValidateCommand:
    """Tests for the validate command."""

    def test_validate_help(self, runner) -> None:
        """Test validate help output."""
        result = runner.invoke(cli, ["validate", "--help"])
        assert result.exit_code == 0
        assert "--source" in result.output

    def test_validate_default(self, runner) -> None:
        """Test validate with default options."""
        result = runner.invoke(cli, ["validate"])
        assert result.exit_code == 0
        assert "Validation Results" in result.output
        assert "Passed" in result.output

    def test_validate_local_source(self, runner) -> None:
        """Test validate with local source."""
        result = runner.invoke(cli, ["validate", "--source", "local"])
        assert result.exit_code == 0
        assert "local" in result.output

    def test_validate_netbox_source(self, runner) -> None:
        """Test validate with netbox source."""
        result = runner.invoke(cli, ["validate", "--source", "netbox"])
        assert result.exit_code == 0
        assert "netbox" in result.output

    def test_validate_invalid_source(self, runner) -> None:
        """Test validate with invalid source."""
        result = runner.invoke(cli, ["validate", "--source", "invalid"])
        assert result.exit_code != 0


class TestConfigCommand:
    """Tests for the config command."""

    def test_config_help(self, runner) -> None:
        """Test config help output."""
        result = runner.invoke(cli, ["config", "--help"])
        assert result.exit_code == 0
        assert "--show" in result.output
        assert "--test" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_config_no_flags(self, mock_get_settings, runner, mock_settings) -> None:
        """Test config without flags shows usage hint."""
        mock_get_settings.return_value = mock_settings
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "--show" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_config_show(self, mock_get_settings, runner, mock_settings) -> None:
        """Test config --show displays configuration."""
        mock_get_settings.return_value = mock_settings
        result = runner.invoke(cli, ["config", "--show"])
        assert result.exit_code == 0
        assert "netbox-geo-foss" in result.output
        assert "development" in result.output
        assert "1.0.0" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_config_test(self, mock_get_settings, runner, mock_settings) -> None:
        """Test config --test tests connectivity."""
        mock_get_settings.return_value = mock_settings
        result = runner.invoke(cli, ["config", "--test"])
        assert result.exit_code == 0
        assert "connection successful" in result.output

    @patch("netbox_geo.cli.main.get_settings")
    def test_config_settings_error(self, mock_get_settings, runner) -> None:
        """Test config when settings raise NetBoxGeoError."""
        from netbox_geo.core.exceptions import NetBoxGeoError

        mock_get_settings.side_effect = NetBoxGeoError("Config missing")
        result = runner.invoke(cli, ["config", "--show"])
        assert result.exit_code == 1

    @patch("netbox_geo.cli.main.get_settings")
    def test_config_unexpected_error(self, mock_get_settings, runner) -> None:
        """Test config when unexpected exception occurs."""
        mock_get_settings.side_effect = RuntimeError("Unexpected")
        result = runner.invoke(cli, ["config", "--show"])
        assert result.exit_code == 1
