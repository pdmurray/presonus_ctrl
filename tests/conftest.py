"""Test configuration and shared fixtures for Presonus IO24 tests."""

from unittest import mock
import usb.core
import usb.util

import pytest

from presonus.device import PresonusDevice, PresonusUSBError
from presonus.models import ChannelSettings, FatChannelSettings, PresetType
from click.testing import CliRunner
from cli.main import cli


# Sample USB responses (mock data simulating device behavior)
SAMPLE_DEVICE_RESPONSES = {
    'get_channel_state': bytes([
        0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ]),  # CMD_GET_CHANNEL_STATE + state data
    'set_level': bytes([0x02, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),  # ACK
    'get_fat_channel': bytes([
        0x04, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ]),  # CMD_GET_FAT_CHANNEL
}


@pytest.fixture
def click_runner():
    """Provide a Click test runner for CLI testing."""
    return CliRunner()


@pytest.fixture
def mock_usb_device():
    """Mock USB device for testing without physical hardware."""
    device = mock.MagicMock(spec=usb.core.Device)
    device.idVendor = PresonusDevice.VENDOR_ID
    device.idProduct = PresonusDevice.PRODUCT_ID
    device.serial_number = "MOCK001"
    device.manufacturer = "Mock Manufacturer"
    device.product = "Mock Product"
    return device


@pytest.fixture
def mock_usb_handle():
    """Mock USB handle with endpoint mocking."""
    handle = mock.MagicMock()
    handle.ctrl_transfer = mock.MagicMock(return_value=bytearray(9))
    handle.read = mock.MagicMock(return_value=bytearray(9))
    handle.write = mock.MagicMock(return_value=9)
    return handle


@pytest.fixture
def sample_preset():
    """Provide a sample Preset object."""
    return PresetType.CUSTOM


@pytest.fixture
def sample_fat_channel():
    """Provide a sample FatChannelSettings object."""
    return FatChannelSettings(
        gate_enabled=True,
        compressor_enabled=True,
        eq_enabled=True,
        compressor_threshold=-20,
        compressor_ratio=4.0,
        eq_low_gain=3.0,
        eq_mid_gain=0.0,
        eq_high_gain=-2.0
    )


@pytest.fixture
def mock_device(mock_usb_device, mock_usb_handle):
    """Provide a PresonusDevice with mocked USB operations."""
    with mock.patch.object(PresonusDevice, 'find_devices', return_value=[mock_usb_device]):
        with mock.patch.object(usb.util, 'release_interface'):
            with mock.patch.object(mock_usb_device, 'is_kernel_driver_active', return_value=False):
                with mock.patch.object(mock_usb_device, 'set_configuration'):
                    device = PresonusDevice()
                    device._device = mock_usb_device
                    device.open()
                    yield device
                    device.close()


@pytest.fixture
def mock_presonus_device(mock_usb_device, mock_usb_handle):
    """Provide a PresonusDevice with mocked USB operations (alternative fixture)."""
    with mock.patch.object(usb.core, 'find', return_value=[mock_usb_device]):
        with mock.patch.object(usb.util, 'release_interface'):
            with mock.patch.object(mock_usb_device, 'is_kernel_driver_active', return_value=False):
                with mock.patch.object(mock_usb_device, 'set_configuration'):
                    device = PresonusDevice()
                    device._handle = mock_usb_handle
                    device._initialized = True
                    yield device
                    device.close()


@pytest.fixture
def populated_device(mock_device, mock_usb_handle):
    """Device with mock_usb_handle configured to return sample responses."""
    mock_usb_handle.read.side_effect = [
        SAMPLE_DEVICE_RESPONSES['get_channel_state'],
        SAMPLE_DEVICE_RESPONSES['get_fat_channel'],
    ]
    return mock_device


@pytest.fixture
def temp_test_device_response(mock_usb_handle):
    """Configure mock to return custom response for single test."""
    custom_response = bytearray([0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    mock_usb_handle.read.return_value = custom_response
    mock_usb_handle.ctrl_transfer.return_value = custom_response
    return custom_response


@pytest.fixture
def device_with_exception(mock_device, mock_usb_handle):
    """Device configured to raise USB errors."""
    mock_usb_handle.write.side_effect = Exception("USB write failure")
    return mock_device


@pytest.fixture
def invalid_channel_data():
    """Sample invalid channel data for testing."""
    return {
        'gain': 1.5,
        'mute': "not_a_boolean"
    }


@pytest.fixture
def partial_fat_channel():
    """Sample FatChannelSettings with minimal required fields."""
    return {
        'gate_enabled': True
    }


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "usb: marks tests as USB-related (use mock)"
    )
    config.addinivalue_line(
        "markers", "cli: marks tests as CLI-related"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "capture: marks tests that depend on packet-capture fixtures"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on file location."""
    for item in items:
        if "test_cli" in item.fspath.strpath:
            item.add_marker(pytest.mark.cli)
        if "test_device" in item.fspath.strpath:
            item.add_marker(pytest.mark.usb)
        if "test_protocol" in item.fspath.strpath:
            item.add_marker(pytest.mark.unit)
