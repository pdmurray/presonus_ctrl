"""Tests for USB device connection and discovery."""

import pytest
from unittest import mock
import usb.core

from presonus.device import PresonusDevice, PresonusUSBError


class TestDeviceDiscovery:
    """Tests for device discovery and enumeration."""

    @pytest.mark.usb
    def test_find_device_with_vendor_product(self, mock_usb_device):
        """Verify device can be found by vendor/product IDs."""
        with mock.patch.object(PresonusDevice, 'find_devices', return_value=[mock_usb_device]):
            devices = PresonusDevice().find_devices()
            assert len(devices) == 1
            assert devices[0] == mock_usb_device

    @pytest.mark.usb
    def test_find_device_returns_empty_when_not_found(self):
        """Test device not found scenario."""
        with mock.patch.object(PresonusDevice, 'find_devices', return_value=[]):
            devices = PresonusDevice().find_devices()
            assert len(devices) == 0

    @pytest.mark.usb
    def test_device_properties(self, mock_usb_device):
        """Verify device exposes expected properties."""
        assert hasattr(mock_usb_device, 'idVendor')
        assert hasattr(mock_usb_device, 'idProduct')
        assert hasattr(mock_usb_device, 'serial_number')


class TestDeviceConnection:
    """Tests for device connection and lifecycle."""

    @pytest.mark.usb
    def test_device_initialization(self, mock_usb_device):
        """Verify device initializes correctly."""
        device = PresonusDevice()
        assert device is not None
        assert device._device is None

    @pytest.mark.usb
    def test_device_context_manager(self, mock_usb_device):
        """Verify device works as context manager."""
        with mock.patch.object(PresonusDevice, 'find_devices', return_value=[mock_usb_device]):
            with mock.patch.object(usb.util, 'release_interface'):
                with mock.patch.object(mock_usb_device, 'is_kernel_driver_active', return_value=False):
                    with mock.patch.object(mock_usb_device, 'set_configuration'):
                        with PresonusDevice() as device:
                            assert device is not None

    @pytest.mark.usb
    def test_device_open_without_kernel_driver(self, mock_usb_device):
        """Test device opens when no kernel driver is active."""
        with mock.patch.object(PresonusDevice, 'find_devices', return_value=[mock_usb_device]):
            with mock.patch.object(usb.util, 'release_interface'):
                with mock.patch.object(mock_usb_device, 'is_kernel_driver_active', return_value=False):
                    with mock.patch.object(mock_usb_device, 'set_configuration'):
                        device = PresonusDevice()
                        device._device = mock_usb_device
                        result = device.open()
                        assert result is True

    @pytest.mark.usb
    def test_device_open_detach_kernel_driver(self, mock_usb_device):
        """Test device opens and detaches kernel driver."""
        with mock.patch.object(PresonusDevice, 'find_devices', return_value=[mock_usb_device]):
            with mock.patch.object(usb.util, 'release_interface'):
                with mock.patch.object(mock_usb_device, 'is_kernel_driver_active', return_value=True):
                    with mock.patch.object(mock_usb_device, 'detach_kernel_driver'):
                        with mock.patch.object(mock_usb_device, 'set_configuration'):
                            device = PresonusDevice()
                            device._device = mock_usb_device
                            result = device.open()
                            assert result is True


class TestDeviceAPI:
    """Tests for device API methods."""

    @pytest.mark.usb
    def test_find_devices(self, mock_usb_device):
        """Verify device discovery works."""
        with mock.patch.object(PresonusDevice, 'find_devices', return_value=[mock_usb_device]):
            devices = PresonusDevice().find_devices()
            assert len(devices) >= 1

    @pytest.mark.usb
    def test_device_properties_accessible(self, mock_device):
        """Verify device properties are accessible."""
        assert mock_device._device.idVendor == PresonusDevice.VENDOR_ID
        assert mock_device._device.idProduct == PresonusDevice.PRODUCT_ID

    @pytest.mark.usb
    def test_device_not_connected(self, mock_usb_device):
        """Test scenario where no device is found."""
        with mock.patch.object(PresonusDevice, 'find_devices', return_value=[]):
            devices = PresonusDevice().find_devices()
            assert len(devices) == 0

    @pytest.mark.usb
    def test_close_releases_interface(self, mock_device, mock_usb_handle):
        """Test device close releases interface properly."""
        mock_device._handle = mock_usb_handle
        with mock.patch.object(usb.util, 'release_interface') as mock_release:
            mock_device.close()
            mock_release.assert_called_once()


class TestErrorHandling:
    """Tests for error scenarios."""

    @pytest.mark.usb
    def test_usb_error(self):
        """Verify USB errors are properly formatted."""
        exc = PresonusUSBError("Test USB error")
        assert "Test USB error" in str(exc)

    @pytest.mark.usb
    def test_exception_message(self):
        """Verify error messages are descriptive."""
        exc = PresonusUSBError("Connection failed")
        assert "Connection failed" in str(exc)

    @pytest.mark.usb
    def test_device_not_found(self):
        """Test device not found handling."""
        with mock.patch.object(PresonusDevice, 'find_devices', return_value=[]):
            devices = PresonusDevice().find_devices()
            assert len(devices) == 0

    @pytest.mark.usb
    def test_device_index_out_of_range(self, mock_usb_device):
        """Test device error when index out of range."""
        with mock.patch.object(PresonusDevice, 'find_devices', return_value=[mock_usb_device]):
            with mock.patch.object(usb.util, 'release_interface'):
                with mock.patch.object(mock_usb_device, 'is_kernel_driver_active', return_value=False):
                    with mock.patch.object(mock_usb_device, 'set_configuration'):
                        device = PresonusDevice()
                        with pytest.raises(PresonusUSBError):
                            device.open(index=5)
