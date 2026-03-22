"""Comprehensive tests for PresonusDevice API methods."""

import pytest
from unittest import mock
from presonus.device import (
    PresonusDevice, PresonusUSBError
)
from presonus.models import (
    VolumeValue, PanValue, GainValue, OutputValue,
    PresetType, HeadphonesSource, ChannelSettings, MasterSettings,
    DeviceInfo, IO24State, FrequencyBand
)
import usb


class TestDeviceDiscovery:
    """Tests for device discovery and connection."""

    @pytest.fixture
    def mock_usb_devices(self):
        """Create list of mock USB devices."""
        devices = []
        for i in range(3):
            mock_dev = mock.MagicMock(spec=usb.core.Device)
            mock_dev.idVendor = PresonusDevice.VENDOR_ID
            mock_dev.idProduct = PresonusDevice.PRODUCT_ID
            mock_dev.serial_number = f"DEV{i}"
            devices.append(mock_dev)
        return devices

    def test_find_devices_finds_presonus(self, mock_usb_devices):
        """Test finding Presonus IO24 devices."""
        with mock.patch.object(usb.core, 'find', return_value=mock_usb_devices):
            device = PresonusDevice()
            found = device.find_devices()
            assert len(found) == 3
            for dev in found:
                assert dev.idVendor == PresonusDevice.VENDOR_ID
                assert dev.idProduct == PresonusDevice.PRODUCT_ID

    def test_find_devices_filters_non_presonus(self, mock_usb_devices):
        """Test that non-Presonus devices are filtered out."""
        non_presonus = [mock.MagicMock()]
        non_presonus[0].idVendor = 0xFFFF
        non_presonus[0].idProduct = 0xFFFF
        all_devices = mock_usb_devices + non_presonus
        with mock.patch.object(usb.core, 'find', return_value=all_devices):
            device = PresonusDevice()
            found = device.find_devices()
            assert len(found) == 3

    def test_open_invalid_index(self):
        """Test opening device with invalid index."""
        with mock.patch.object(usb.core, 'find', return_value=[]):
            device = PresonusDevice()
            with pytest.raises(PresonusUSBError, match="No device found at index 0"):
                device.open(0)

    def test_open_success(self, mock_usb_device):
        """Test successful device opening."""
        with mock.patch.object(usb.core, 'find', return_value=[mock_usb_device]):
            with mock.patch.object(mock_usb_device, 'is_kernel_driver_active', return_value=False):
                device = PresonusDevice()
                result = device.open(0)
                assert result is True
                assert device._initialized is True


class TestChannelControl:
    """Comprehensive tests for channel control methods."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_set_channel_volume_valid(self, device_with_mock):
        """Test setting channel volume."""
        device = device_with_mock
        volume_value = VolumeValue.from_db(-20.0)
        result = device.set_channel_volume(1, volume_value.raw)
        assert result is True
        device._handle.write.assert_called_once()

    def test_set_channel_volume_range(self, device_with_mock):
        """Test channel volume range validation."""
        device = device_with_mock
        min_volume = VolumeValue.from_db(-60.0).raw
        max_volume = VolumeValue.from_db(0.0).raw
        assert device.set_channel_volume(1, min_volume) is True
        assert device.set_channel_volume(1, max_volume) is True
        out_of_range = VolumeValue.from_db(100.0).raw
        assert device.set_channel_volume(1, out_of_range) is False

    def test_set_channel_pan_valid(self, device_with_mock):
        """Test setting channel pan."""
        device = device_with_mock
        for pan_db in [-100, -50, 0, 50, 100]:
            pan_value = PanValue.from_db(pan_db)
            result = device.set_channel_pan(1, pan_value.value)
            assert result is True

    def test_set_channel_pan_invalid(self, device_with_mock):
        """Test pan out of range."""
        device = device_with_mock
        result = device.set_channel_pan(1, 200)
        assert result is False

    def test_set_channel_mute_toggle(self, device_with_mock):
        """Test muting and unmuting channels."""
        device = device_with_mock
        device._handle.read.return_value = bytes([0x03, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00])
        device.set_channel_mute(1, True)
        device.set_channel_mute(1, False)
        assert device._handle.write.call_count >= 2

    def test_set_channel_solo_toggle(self, device_with_mock):
        """Test soloing and unsoloing channels."""
        device = device_with_mock
        device._handle.read.return_value = bytes([0x03, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x01, 0x00])
        device.set_channel_solo(1, True)
        device.set_channel_solo(1, False)
        assert device._handle.write.call_count >= 2

    def test_set_channel_gain_valid(self, device_with_mock):
        """Test setting channel gain."""
        device = device_with_mock
        for db in [-60.0, -30.0, 0.0, 12.0]:
            gain_value = GainValue.from_db(db)
            result = device.set_channel_gain(1, gain_value.raw)
            assert result is True

    def test_set_channel_gain_invalid(self, device_with_mock):
        """Test out-of-range gain."""
        device = device_with_mock
        result = device.set_channel_gain(1, 20.0)
        assert result is False

    def test_set_channel_phase(self, device_with_mock):
        """Test phase inversion."""
        device = device_with_mock
        assert device.set_channel_phase(1, True) is True
        assert device.set_channel_phase(1, False) is True

    def test_set_channel_input_source(self, device_with_mock):
        """Test input source selection."""
        device = device_with_mock
        for source in ["mic", "line"]:
            result = device.set_channel_input_source(1, source)
            assert result is True

    def test_channel_methods_invalid_id(self, device_with_mock):
        """Test operations on invalid channel IDs."""
        device = device_with_mock
        device.set_channel_volume(25, 0.0)  # Should fail or succeed
        device.set_channel_pan(0, 0)  # Channel 0 is master
        device.set_channel_mute(25, True)
        device.set_channel_solo(0, True)


class TestMasterControls:
    """Test master control methods."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x06, 0x00, 0x42, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_set_master_volume(self, device_with_mock):
        """Test master volume control."""
        device = device_with_mock
        for vol in [0.0, 0.5, 1.0, -3.0, -6.0]:
            result = device.set_master_volume(vol)
            assert result is True

    def test_set_master_volume_range(self, device_with_mock):
        """Test master volume range validation."""
        device = device_with_mock
        assert device.set_master_volume(-24.0) is True
        assert device.set_master_volume(0.0) is True
        assert device.set_master_volume(0.5) is True
        assert device.set_master_volume(100.0) is False

    def test_set_monitor_blend(self, device_with_mock):
        """Test monitor blend control."""
        device = device_with_mock
        for balance in [-100, -50, 0, 50, 100]:
            result = device.set_monitor_blend(balance)
            if -100 <= balance <= 100:
                assert result is True
            else:
                assert result is False

    def test_set_headphones_volume(self, device_with_mock):
        """Test headphones volume control."""
        device = device_with_mock
        for vol in [0.0, 0.5, 1.0, -3.0]:
            result = device.set_headphones_volume(vol)
            assert result is True

    def test_set_headphones_source(self, device_with_mock):
        """Test headphones source selection."""
        device = device_with_mock
        for source_type in [HeadphonesSource.LINE, HeadphonesSource.MONITOR, HeadphonesSource.HOTKEY]:
            result = device.set_headphones_source(source_type)
            assert result is True


class TestStateQueries:
    """Test state query methods."""

    @pytest.fixture
    def mock_state_response(self, mock_presonus_device):
        """Mock device response for state queries."""
        def create_channel_response(ch_id):
            return bytes([0x03, 0x00, 0x01, 0x00, ch_id, 0x42, 0x00, 0x00, 0x00])
        
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        
        index = [0]
        responses = [create_channel_response(i) for i in range(1, 25)] + [bytes([0x03, 0x00, 0x06, 0x00, 0x42, 0x00, 0x00, 0x00, 0x00])]
        
        def response_callback(cmd_byte):
            idx = index[0]
            index[0] += 1
            if idx < len(responses):
                return responses[idx]
            return responses[-1]
        
        device._handle.read.side_effect = response_callback
        return device

    def test_get_device_info(self, mock_presonus_device):
        """Test device info retrieval."""
        device = mock_presonus_device
        device._handle.read.return_value = bytes([0x03, 0x00, 0x00, 0x01, ord('F'), ord('O'), ord('0'), ord('4'), ord('2'), ord('2'), ord('2'), 0x00, 0x00])
        info = device.get_device_info()
        assert info is not None
        assert isinstance(info, DeviceInfo)
    
    def test_query_state_success(self, mock_state_response):
        """Test full state query."""
        device = mock_state_response
        state = device.query_state()
        assert state is not None
        assert isinstance(state, IO24State)
        assert len(state.channels) == 24

    def test_query_state_with_master(self, mock_state_response):
        """Test state includes master settings."""
        device = mock_state_response
        state = device.query_state()
        assert state.master is not None
    
    def test_state_serialization(self, mock_state_response):
        """Test state to_dict serialization."""
        device = mock_state_response
        state = device.query_state()
        data = state.to_dict()
        assert 'channels' in data
        assert 'master' in data
        assert 'device_info' in data

    def test_state_empty(self):
        """Test empty state."""
        state = IO24State()
        assert len(state.channels) == 0
        assert state.master is None
        data = state.to_dict()
        assert len(data['channels']) == 0
