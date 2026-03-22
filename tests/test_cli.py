"""Tests for CLI commands and interface."""

import pytest
from click.testing import CliRunner
from unittest import mock

from cli.main import cli
from presonus.device import PresonusDevice, PresonusUSBError


@pytest.mark.cli
class TestCLICommands:
    def test_cli_help(self, click_runner):
        result = click_runner.invoke(cli)
        assert result.exit_code == 0
        assert "Usage" in result.output

    def test_cli_info_command_exists(self, click_runner):
        result = click_runner.invoke(cli, ["info"])
        assert "unrecognized" not in result.output.lower()

    def test_cli_list_command_exists(self, click_runner):
        result = click_runner.invoke(cli, ["list"])
        assert "unrecognized" not in result.output.lower()


@pytest.mark.cli
class TestInfoCommand:
    def test_info_device_not_connected(self, click_runner, mock_usb_device):
        with mock.patch.object(PresonusDevice, "find_devices", return_value=[]):
            result = click_runner.invoke(cli, ["info"])
            assert result.exit_code != 0

    def test_info_command(self, click_runner, mock_usb_device, mock_usb_handle):
        with mock.patch.object(PresonusDevice, "find_devices", return_value=[mock_usb_device]):
            with mock.patch.object(mock_usb_device, "is_kernel_driver_active", return_value=False):
                with mock.patch.object(mock_usb_device, "set_configuration"):
                    device = PresonusDevice()
                    device._device = mock_usb_device
                    with mock.patch.object(PresonusDevice, "open", return_value=True):
                        with mock.patch.object(PresonusDevice, "close"):
                            result = click_runner.invoke(cli, ["info"])
                            assert result.exit_code == 0


@pytest.mark.cli
class TestListCommand:
    def test_list_devices(self, click_runner, mock_usb_device):
        with mock.patch.object(PresonusDevice, "find_devices", return_value=[mock_usb_device]):
            result = click_runner.invoke(cli, ["list"])
            assert result.exit_code == 0

    def test_list_no_devices(self, click_runner):
        with mock.patch.object(PresonusDevice, "find_devices", return_value=[]):
            result = click_runner.invoke(cli, ["list"])
            assert result.exit_code == 0


@pytest.mark.cli
class TestSetCommand:
    def test_set_level_success(self, click_runner, mock_device):
        result = click_runner.invoke(cli, ["set", "1", "--level", "0.75"])
        assert result.exit_code == 0
        assert "Setting channel 1 parameters" in result.output

    def test_set_invalid_channel(self, click_runner):
        result = click_runner.invoke(cli, ["set", "--channel", "99", "--level", "0.5"])
        assert result.exit_code != 0

    def test_set_invalid_level(self, click_runner):
        result = click_runner.invoke(cli, ["set", "--channel", "1", "--level", "1.5"])
        assert result.exit_code != 0


@pytest.mark.cli
class TestFatCommand:
    def test_fat_enable_compressor(self, click_runner, mock_device):
        result = click_runner.invoke(cli, ["fat", "1", "--compressor", "on"])
        assert result.exit_code == 0
        assert "Adjusting fat channel settings" in result.output


@pytest.mark.cli
class TestCLIErrorHandling:
    def test_cli_unrecognized_option(self, click_runner):
        result = click_runner.invoke(cli, ["--unknown-option"])
        assert result.exit_code != 0

    def test_cli_missing_required_args(self, click_runner):
        result = click_runner.invoke(cli, ["set"])
        assert result.exit_code != 0
        assert "missing" in result.output.lower() or "error" in result.output.lower()

    def test_cli_permission_error(self, click_runner, mock_device, mock_usb_handle):
        mock_usb_handle.write.side_effect = Exception("USBError: Access denied")
        result = click_runner.invoke(cli, ["set", "--channel", "1", "--level", "0.5"])
        assert result.exit_code != 0
