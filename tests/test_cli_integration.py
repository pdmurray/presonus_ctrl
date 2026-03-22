"""Additional CLI tests for Presonus IO24 control."""

import pytest
from click.testing import CliRunner
from unittest import mock

from cli.main import cli
from presonus.device import PresonusDevice, PresonusUSBError


@pytest.mark.cli
class TestCLIEncapsulation:
    """Tests for CLI encapsulation."""
    
    def test_cli_module_structure(self):
        """Verify CLI module has expected structure."""
        commands = [cmd.name for cmd in cli.commands.values()]
        expected = ['info', 'list', 'set', 'fat', 'get', 'fader', 'preset', 
                   'levels', 'monitor', 'discover']
        for cmd in expected:
            assert cmd in commands, f"Missing command: {cmd}"
    
    def test_cli_help_valid(self, click_runner):
        """Test CLI help output is valid."""
        result = click_runner.invoke(cli)
        assert result.exit_code == 0
        assert "Usage" in result.output


class TestInstalledCLIStructure:
    """Tests for CLI structure and commands."""
    
    def test_list_no_devices_exit_code(self, click_runner):
        """Test list command exits gracefully when no device."""
        with mock.patch.object(PresonusDevice, "find_devices", return_value=[]):
            result = click_runner.invoke(cli, ["list"])
            assert result.exit_code == 0
    
    def test_set_command_exit_code(self, click_runner, mock_usb_device):
        """Test set command with valid arguments."""
        with mock.patch.object(PresonusDevice, "find_devices", return_value=[mock_usb_device]):
            with mock.patch.object(mock_usb_device, "is_kernel_driver_active", return_value=False):
                with mock.patch.object(mock_usb_device, "set_configuration"):
                    with PresonusDevice() as device:
                        result = click_runner.invoke(cli, ["set", "1", "--level", "0.5"])
                        assert result.exit_code == 0
    
    def test_fat_command_exit_code(self, click_runner, mock_usb_device):
        """Test fat command with valid arguments."""
        with mock.patch.object(PresonusDevice, "find_devices", return_value=[mock_usb_device]):
            with mock.patch.object(mock_usb_device, "is_kernel_driver_active", return_value=False):
                with mock.patch.object(mock_usb_device, "set_configuration"):
                    with PresonusDevice() as device:
                        result = click_runner.invoke(cli, ["fat", "1", "--compressor", "on"])
                        assert result.exit_code == 0
