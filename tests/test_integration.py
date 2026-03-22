"""Integration tests for complete workflows and end-to-end scenarios."""

import pytest
from unittest import mock
from presonus.device import PresonusDevice
from presonus.models import (
    PresetType, FrequencyBand,
    CompressorSettings, GateSettings,
    EqSettings, LimiterSettings
)


class TestChannelCompleteSetup:
    """Test complete channel setup workflow."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_channel_gain_to_mute_workflow(self, device_with_mock):
        """Test setting gain, then applying preset, then muting."""
        device = device_with_mock
        
        # Step 1: Set gain
        device.set_channel_gain(1, 6.0)
        # Step 2: Apply vocal preset
        device.set_channel_preset(1, PresetType.VOCAL)
        # Step 3: Set volume
        device.set_channel_volume(1, -10.0)
        # Step 4: Set pan
        device.set_channel_pan(1, -50)
        # Step 5: Mute
        device.set_channel_mute(1, True)
        
        assert device._handle.write.call_count >= 5

    def test_fat_channel_workflow(self, device_with_mock):
        """Test complete fat channel configuration workflow."""
        device = device_with_mock
        
        # Load preset first
        device.set_channel_preset(1, PresetType.SNARE)
        
        # Load compressor
        compressor = CompressorSettings(enabled=True, threshold=-20, ratio=4)
        device.set_compressor(1, compressor)
        
        # Configure EQ
        eq = EqSettings()
        eq.set_band(FrequencyBand.LOW, gain=-2, freq=100, q=1.5)
        eq.set_band(FrequencyBand.LOW_MID, gain=1, freq=400, q=0.8)
        eq.set_band(FrequencyBand.HIGH_MID, gain=2, freq=2500, q=1.2)
        eq.set_band(FrequencyBand.HIGH, gain=-1, freq=8000, q=0.7)
        device.set_eq(1, eq)
        
        # Set gate
        gate = GateSettings(enabled=True, threshold=-50, ratio=10)
        device.set_gate(1, gate)
        
        # Set limiter
        limiter = LimiterSettings(enabled=False)
        device.set_limiter(1, limiter)
        
        assert device._handle.write.call_count >= 5

    def test_channel_query_validation(self, device_with_mock):
        """Test querying state after changes."""
        device = device_with_mock
        device._handle.read.side_effect = [
            bytes([0x03, 0x00, 0x01, 0x00, 0x01, 0x42, 0x00, 0x00, 0x00]),  # Ch 1
            bytes([0x03, 0x00, 0x01, 0x00, 0x02, 0x42, 0x00, 0x00, 0x00]),  # Ch 2
        ]
        
        device.set_channel_volume(1, -10.0)
        state = device.query_state()
        
        # Verify state reflects changes
        assert 1 in state.channels
        assert 2 in state.channels


class TestMasterCompleteSetup:
    """Test complete master configuration workflow."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x06, 0x00, 0x42, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_master_vol_to_blend_workflow(self, device_with_mock):
        """Test setting master volume then adjust monitor blend."""
        device = device_with_mock
        
        # Set master volume
        device.set_master_volume(-6.0)
        # Adjust monitor blend
        device.set_monitor_blend(-30)
        # Check headphones
        device.set_headphones_volume(-3.0)
        
        assert device._handle.write.call_count >= 3

    def test_headphones_workflow(self, device_with_mock):
        """Test setting mix source then volume."""
        device = device_with_mock
        
        device.set_headphones_source(0, "monitor")
        device.set_headphones_volume(-3.0)
        
        assert device._handle.write.call_count >= 2


class TestBusManagement:
    """Test bus and aux configuration workflows."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_bus_routing_workflow(self, device_with_mock):
        """Test routing to bus and setting send levels."""
        device = device_with_mock
        
        # Route channel to bus
        device.set_routing(1, 0x00, 100, True, False)
        # Set aux send level
        device.set_aux_send_level(1, 1, 75)
        
        assert device._handle.write.call_count >= 2

    def test_reverb_workflow(self, device_with_mock):
        """Test setting reverb send level."""
        device = device_with_mock
        
        device.set_reverb_send_level(1, 80)
        device.set_reverb_send_level(2, 60)
        
        assert device._handle.write.call_count >= 2


class TestEdgeCaseWorkflows:
    """Test edge case complete workflows."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_preset_clearing_workflow(self, device_with_mock):
        """Test preset applied then cleared."""
        device = device_with_mock
        
        # Apply preset
        device.set_channel_preset(1, PresetType.VOCAL)
        # Clear by reapplying with defaults
        device.set_channel_preset(1, PresetType.DRUM_MIC)
        
        assert device._handle.write.call_count >= 2

    def test_eq_tuning_workflow(self, device_with_mock):
        """Test fine-tuning EQ adjustments."""
        device = device_with_mock
        
        # Start with flat EQ
        eq = EqSettings()
        for band in FrequencyBand:
            eq.set_band(band, gain=0, freq=1000, q=0.0)
        device.set_eq(1, eq)
        
        # Adjust one band
        eq.set_band(FrequencyBand.LOW, gain=3, freq=100, q=1.0)
        device.set_eq(1, eq)
        
        # Adjust multiple bands
        eq.set_band(FrequencyBand.LOW_MID, gain=-1, freq=300, q=0.8)
        eq.set_band(FrequencyBand.HIGH_MID, gain=2, freq=2000, q=1.2)
        device.set_eq(1, eq)
        
        assert device._handle.write.call_count >= 3

    def test_multi_channel_setup(self, device_with_mock):
        """Test setting up multiple channels identically."""
        device = device_with_mock
        
        channels = [1, 2, 3, 4]
        
        for ch_id in channels:
            device.set_channel_gain(ch_id, 6.0)
            device.set_channel_volume(ch_id, -15.0)
            device.set_channel_pan(ch_id, 0)
            device.set_channel_mute(ch_id, False)
        
        assert device._handle.write.call_count >= len(channels) * 4
