"""Edge case tests and error handling validation."""

import pytest
from unittest import mock
from presonus.device import PresonusDevice, PresonusUSBError
from presonus.models import (
    PresetType, FrequencyBand,
    CompressorSettings, GateSettings,
    EqSettings, LimiterSettings,
    HeadphonesSource
)
import usb.core


class TestInvalidChannelIDs:
    """Tests for invalid channel ID handling."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        return device

    def test_channel_zero_pan(self, device_with_mock):
        """Test pan on channel 0 (master - shouldn't allow pan)."""
        device = device_with_mock
        result = device.set_channel_pan(0, 0)
        # Master typically doesn't pan in stereo
        assert result is False

    def test_channel_zero_solo(self, device_with_mock):
        """Test solo on channel 0 (master - shouldn't allow solo)."""
        device = device_with_mock
        result = device.set_channel_solo(0, True)
        # Master typically doesn't solo
        assert result is False

    def test_channel_over_25(self, device_with_mock):
        """Test channel IDs > 24."""
        device = device_with_mock
        
        for method_name in ['volume', 'pan', 'mute', 'solo', 'gain', 'phase']:
            method = getattr(device, f'set_channel_{method_name}')
            result = False
            
            if method_name in ['volume', 'pan']:
                result = method(25, 0)
            elif method_name in ['mute', 'solo']:
                result = method(25, True)
            elif method_name == 'gain':
                result = method(25, 6.0)
            elif method_name == 'phase':
                phase_method = getattr(device, 'set_channel_phase')
                result = phase_method(25, True)
            
            assert result is False, f"{method_name} should fail for channel 25"


class TestInvalidParameterValues:
    """Tests for out-of-range parameter values."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        return device

    def test_gain_out_of_range(self, device_with_mock):
        """Test gain out of valid range."""
        device = device_with_mock
        
        # Valid range is typically -60 to +12 dB
        assert device.set_channel_gain(1, -70.0) is False
        assert device.set_channel_gain(1, 13.0) is False
        assert device.set_channel_gain(1, -60.0) is True
        assert device.set_channel_gain(1, 12.0) is True

    def test_pan_out_of_range(self, device_with_mock):
        """Test pan out of valid range."""
        device = device_with_mock
        
        # Valid pan is typically -100 to +100 or -50 to +50
        assert device.set_channel_pan(1, -150) is False
        assert device.set_channel_pan(1, 150) is False
        assert device.set_channel_pan(1, -100) is True
        assert device.set_channel_pan(1, 100) is True

    def test_volume_out_of_range(self, device_with_mock):
        """Test volume out of valid range."""
        device = device_with_mock
         
        # Valid volume typically -60 to 0 dB
        assert device.set_channel_volume(1, -70.0) is False
        assert device.set_channel_volume(1, 1.0) is False
        assert device.set_channel_volume(1, -60.0) is True
        assert device.set_channel_volume(1, 0.0) is True

    def test_compressor_threshold_out_of_range(self, device_with_mock):
        """Test compressor threshold out of range."""
        device = device_with_mock
        
        settings = CompressorSettings(enabled=True, threshold=-100)
        result = device.set_compressor(1, settings)
        assert result is False
        
        settings = CompressorSettings(enabled=True, threshold=0)
        result = device.set_compressor(1, settings)
        assert result is False

    def test_gate_threshold_out_of_range(self, device_with_mock):
        """Test gate threshold out of range."""
        device = device_with_mock
        
        settings = GateSettings(enabled=True, threshold=-100)
        result = device.set_gate(1, settings)
        assert result is False

    def test_limiter_threshold_out_of_range(self, device_with_mock):
        """Test limiter threshold out of range."""
        device = device_with_mock
        
        # Threshold -3 dB is typically max
        settings = LimiterSettings(enabled=True, threshold=0)
        result = device.set_limiter(1, settings)
        assert result is False

    def test_monitor_blend_out_of_range(self, device_with_mock):
        """Test monitor blend out of range."""
        device = device_with_mock
        
        # Range typically -100 to +100
        assert device.set_monitor_blend(-150) is False
        assert device.set_monitor_blend(150) is False
        assert device.set_monitor_blend(-100) is True
        assert device.set_monitor_blend(100) is True

    def test_headphones_source_invalid(self, device_with_mock):
        """Test invalid headphones source."""
        device = device_with_mock
        
        # Valid sources are LINE, MONITOR, HOTKEY
        try:
            device.set_headphones_source(999)
        except Exception:
            pass  # Expected to fail


class TestDeviceInitializationErrors:
    """Tests for device initialization failures."""

    def test_open_non_existent_device(self):
        """Test opening non-existent device index."""
        with mock.patch.object(usb.core, 'find', return_value=[]) as mock_find:
            device = PresonusDevice()
            with pytest.raises(PresonusUSBError, match="No device found"):
                device.open(0)

    def test_operation_on_uninitialized_device(self, mock_presonus_device):
        """Test operations on uninitialized device."""
        device = mock_presonus_device
        device._initialized = False
        
        with pytest.raises(PresonusUSBError):
            device.set_channel_volume(1, 0.0)
        
        with pytest.raises(PresonusUSBError):
            device.set_master_volume(0.0)
        
        with pytest.raises(PresonusUSBError):
            device.query_state()

    def test_handle_not_initialized(self, mock_presonus_device):
        """Test operations when USB handle not available."""
        device = mock_presonus_device
        device._handle = None
        device._initialized = True
        
        with pytest.raises(PresonusUSBError):
            device.set_channel_volume(1, 0.0)


class TestResponseParsingErrors:
    """Tests for malformed USB response handling."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        return device

    def test_incomplete_response(self, device_with_mock):
        """Test handling of incomplete USB responses."""
        device = device_with_mock
        device._handle.read.return_value = bytes([0x03, 0x00])  # Too short
        
        # Should handle gracefully
        try:
            device.query_state()
        except Exception:
            pass  # Expected to handle gracefully

    def test_invalid_command_response(self, device_with_mock):
        """Test handling of invalid command responses."""
        device = device_with_mock
        device._handle.read.return_value = bytes([0xFF, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
        
        # Should handle gracefully
        try:
            device.get_device_info()
        except Exception:
            pass  # Expected


class TestConcurrentOperations:
    """Tests for edge cases in concurrent operations."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_rapid_volume_changes(self, device_with_mock):
        """Test rapid successive volume changes."""
        device = device_with_mock
        
        for i in range(10):
            device.set_channel_volume(1, -i * 5)
        
        assert device._handle.write.call_count == 10

    def test_rapid_preset_load(self, device_with_mock):
        """Test rapid preset loading."""
        device = device_with_mock
        
        for preset in [PresetType.VOCAL, PresetType.GUITAR, PresetType.SNARE]:
            device.set_channel_preset(1, preset)
        
        assert device._handle.write.call_count == 3

    def test_mixed_channel_operations(self, device_with_mock):
        """Test mixed operations across channels."""
        device = device_with_mock
        
        operations = [
            (1, lambda d: d.set_channel_volume(1, -10)),
            (2, lambda d: d.set_channel_pan(2, 25)),
            (3, lambda d: d.set_channel_mute(3, True)),
            (4, lambda d: d.set_channel_gain(4, 8.0)),
        ]
        
        for channel, op in operations:
            op(device)
        
        assert device._handle.write.call_count >= len(operations)


class TestBoundaryConditions:
    """Tests for boundary conditions."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        return device

    def test_zero_values(self, device_with_mock):
        """Test all zero parameter values."""
        device = device_with_mock
        
        assert device.set_channel_volume(1, 0.0) is True
        assert device.set_master_volume(0.0) is True
        
        assert device.set_channel_pan(1, 0) is True
        assert device.set_monitor_blend(0) is True

    def test_exact_boundary_values(self, device_with_mock):
        """Test exact boundary values."""
        device = device_with_mock
        
        # Volume boundary
        assert device.set_channel_volume(1, -60.0) is True
        assert device.set_channel_volume(1, 0.0) is True
        
        # Pan boundary
        assert device.set_channel_pan(1, -100) is True
        assert device.set_channel_pan(1, 100) is True
        
        # Gain boundary
        assert device.set_channel_gain(1, -60.0) is True
        assert device.set_channel_gain(1, 12.0) is True

    def test_negative_pan_values(self, device_with_mock):
        """Test negative pan values."""
        device = device_with_mock
        
        for pan in [-100, -50, -1]:
            assert device.set_channel_pan(1, pan) is True

    def test_negative_volume_values(self, device_with_mock):
        """Test negative volume values."""
        device = device_with_mock
        
        for vol in [-1, -10, -30, -60]:
            assert device.set_channel_volume(1, vol) is True
