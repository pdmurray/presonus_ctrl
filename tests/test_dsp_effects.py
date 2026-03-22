"""Comprehensive tests for DSP effects (compressor, gate, EQ, limiter)."""

import pytest
from unittest import mock
from presonus.device import PresonusDevice, PresonusUSBError
from presonus.models import (
    PresetType,
    FrequencyBand,
    CompressorSettings,
    GateSettings,
    EqSettings,
    LimiterSettings,
    ChannelSettings,
    FatChannelSettings,
)


class TestCompressor:
    """Tests for compressor DSP effect."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_set_compressor_enabled(self, device_with_mock):
        """Test enabling compressor."""
        device = device_with_mock
        settings = CompressorSettings(enabled=True, threshold=-20, ratio=4)
        result = device.set_compressor(1, settings)
        assert result is True

    def test_set_compressor_disabled(self, device_with_mock):
        """Test disabling compressor."""
        device = device_with_mock
        settings = CompressorSettings(enabled=False)
        result = device.set_compressor(1, settings)
        assert result is True

    def test_set_compressor_all_params(self, device_with_mock):
        """Test compressor with all parameters."""
        device = device_with_mock
        settings = CompressorSettings(
            enabled=True,
            threshold=-40,
            ratio=3,
            attack=10,
            release=50,
            output_gain=5
        )
        result = device.set_compressor(1, settings)
        assert result is True

    def test_set_compressor_invalid_channel(self, device_with_mock):
        """Test compressor on invalid channel."""
        device = device_with_mock
        settings = CompressorSettings(enabled=True)
        # Channel 0 is master, 25+ are invalid
        assert device.set_compressor(25, settings) is False
        assert device.set_compressor(0, settings) is False  # Master doesn't have compressor

    def test_compressor_edge_cases(self, device_with_mock):
        """Test compressor extreme values."""
        device = device_with_mock
        # Min threshold
        settings = CompressorSettings(enabled=True, threshold=-80)
        result = device.set_compressor(1, settings)
        assert result is True
        # High ratio
        settings = CompressorSettings(enabled=True, ratio=20)
        result = device.set_compressor(1, settings)
        assert result is True


class TestGate:
    """Tests for gate DSP effect."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_set_gate_enabled(self, device_with_mock):
        """Test enabling gate."""
        device = device_with_mock
        settings = GateSettings(enabled=True, threshold=-60, ratio=10)
        result = device.set_gate(1, settings)
        assert result is True

    def test_set_gate_disabled(self, device_with_mock):
        """Test disabling gate."""
        device = device_with_mock
        settings = GateSettings(enabled=False)
        result = device.set_gate(1, settings)
        assert result is True

    def test_set_gate_all_params(self, device_with_mock):
        """Test gate with all parameters."""
        device = device_with_mock
        settings = GateSettings(
            enabled=True,
            threshold=-50,
            ratio=4,
            attack=5,
            release=100,
            hold=10
        )
        result = device.set_gate(1, settings)
        assert result is True

    def test_gate_invalid_channel(self, device_with_mock):
        """Test gate on invalid channel."""
        device = device_with_mock
        settings = GateSettings(enabled=True)
        assert device.set_gate(25, settings) is False
        assert device.set_gate(0, settings) is False

    def test_gate_sensitivity(self, device_with_mock):
        """Test gate sensitivity settings."""
        device = device_with_mock
        # High sensitivity (low threshold)
        settings = GateSettings(enabled=True, threshold=-80)
        result = device.set_gate(1, settings)
        assert result is True
        # Low sensitivity (high threshold)
        settings = GateSettings(enabled=True, threshold=-20)
        result = device.set_gate(1, settings)
        assert result is True


class TestEQ:
    """Tests for 4-band EQ DSP effect."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_set_eq_band1(self, device_with_mock):
        """Test EQ band 1 (Low)"""
        device = device_with_mock
        eq = EqSettings()
        eq.set_band(FrequencyBand.LOW, gain=5, freq=100, q=1.0)
        result = device.set_eq(1, eq)
        assert result is True

    def test_set_eq_band2(self, device_with_mock):
        """Test EQ band 2 (Low-Mid)"""
        device = device_with_mock
        eq = EqSettings()
        eq.set_band(FrequencyBand.LOW_MID, gain=-3, freq=300, q=0.5)
        result = device.set_eq(1, eq)
        assert result is True

    def test_set_eq_band3(self, device_with_mock):
        """Test EQ band 3 (High-Mid)"""
        device = device_with_mock
        eq = EqSettings()
        eq.set_band(FrequencyBand.HIGH_MID, gain=2, freq=3000, q=1.0)
        result = device.set_eq(1, eq)
        assert result is True

    def test_set_eq_band4(self, device_with_mock):
        """Test EQ band 4 (High)"""
        device = device_with_mock
        eq = EqSettings()
        eq.set_band(FrequencyBand.HIGH, gain=-2, freq=8000, q=0.7)
        result = device.set_eq(1, eq)
        assert result is True

    def test_set_eq_all_bands(self, device_with_mock):
        """Test EQ with all 4 bands."""
        device = device_with_mock
        eq = EqSettings()
        eq.set_band(FrequencyBand.LOW, gain=3, freq=100, q=1.0)
        eq.set_band(FrequencyBand.LOW_MID, gain=-1, freq=400, q=0.8)
        eq.set_band(FrequencyBand.HIGH_MID, gain=1, freq=2000, q=1.2)
        eq.set_band(FrequencyBand.HIGH, gain=2, freq=6000, q=0.9)
        result = device.set_eq(1, eq)
        assert result is True

    def test_eq_invalid_channel(self, device_with_mock):
        """Test EQ on invalid channel."""
        device = device_with_mock
        eq = EqSettings()
        eq.set_band(FrequencyBand.LOW, gain=0)
        assert device.set_eq(25, eq) is False
        assert device.set_eq(0, eq) is False

    def test_eq_flat_response(self, device_with_mock):
        """Test EQ with flat response (all gains at 0)."""
        device = device_with_mock
        eq = EqSettings()
        for band in FrequencyBand:
            eq.set_band(band, gain=0, freq=1000, q=0.0)
        result = device.set_eq(1, eq)
        assert result is True


class TestLimiter:
    """Tests for limiter DSP effect."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_set_limiter_enabled(self, device_with_mock):
        """Test enabling limiter."""
        device = device_with_mock
        settings = LimiterSettings(enabled=True, threshold=-3, release=50)
        result = device.set_limiter(1, settings)
        assert result is True

    def test_set_limiter_disabled(self, device_with_mock):
        """Test disabling limiter."""
        device = device_with_mock
        settings = LimiterSettings(enabled=False)
        result = device.set_limiter(1, settings)
        assert result is True

    def test_set_limiter_params(self, device_with_mock):
        """Test limiter parameters."""
        device = device_with_mock
        settings = LimiterSettings(
            enabled=True,
            threshold=-6,
            release=30,
            lookahead=5
        )
        result = device.set_limiter(1, settings)
        assert result is True

    def test_limiter_invalid_channel(self, device_with_mock):
        """Test limiter on invalid channel."""
        device = device_with_mock
        settings = LimiterSettings(enabled=True)
        assert device.set_limiter(25, settings) is False
        assert device.set_limiter(0, settings) is False


class TestPresetApplication:
    """Tests for preset loading on channels."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return device

    @pytest.mark.parametrize("preset", PresetType)
    def test_set_channel_preset(self, device_with_mock, preset):
        """Test loading various presets."""
        device = device_with_mock
        result = device.set_channel_preset(1, preset)
        assert result is True

    def test_set_channel_preset_invalid(self, device_with_mock):
        """Test preset on invalid channel."""
        device = device_with_mock
        result = device.set_channel_preset(25, PresetType.SNARE)
        assert result is False
        result = device.set_channel_preset(0, PresetType.GUITAR)
        assert result is False

    def test_set_channel_preset_master(self, device_with_mock):
        """Test preset on master (should fail)."""
        device = device_with_mock
        result = device.set_channel_preset(0, PresetType.SNARE)
        assert result is False


class TestCompleteFatChannel:
    """Test complete fat channel configuration."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_full_fat_channel_config(self, device_with_mock):
        """Test full fat channel configuration."""
        device = device_with_mock
        
        # Configure all effects
        compressor = CompressorSettings(enabled=True, threshold=-20, ratio=4)
        gate = GateSettings(enabled=True, threshold=-50, ratio=4)
        eq = EqSettings()
        eq.set_band(FrequencyBand.LOW, gain=-2, freq=100, q=1.0)
        eq.set_band(FrequencyBand.LOW_MID, gain=1, freq=400, q=0.8)
        eq.set_band(FrequencyBand.HIGH_MID, gain=2, freq=2500, q=1.2)
        eq.set_band(FrequencyBand.HIGH, gain=-1, freq=8000, q=0.9)
        limiter = LimiterSettings(enabled=False)
        
        device.set_compressor(1, compressor)
        device.set_gate(1, gate)
        device.set_eq(1, eq)
        device.set_limiter(1, limiter)
        
        assert device._handle.write.call_count == 4

    def test_fat_channel_preset_then_custom(self, device_with_mock):
        """Test preset followed by custom settings."""
        device = device_with_mock
        
        # Load preset
        device.set_channel_preset(1, PresetType.VOCAL)
        
        # Override with custom settings
        eq = EqSettings()
        eq.set_band(FrequencyBand.LOW, gain=3, freq=100, q=1.0)
        device.set_eq(1, eq)
        
        assert device._handle.write.call_count == 2

    def test_fat_channel_clear_preset(self, device_with_mock):
        """Test clearing preset and setting defaults."""
        device = device_with_mock
        
        # Load preset
        device.set_channel_preset(1, PresetType.GUITAR)
        
        # Clear by applying defaults
        eq = EqSettings()
        for band in FrequencyBand:
            eq.set_band(band, gain=0, freq=1000, q=0.0)
        settings = FatChannelSettings(
            compressor=CompressorSettings(enabled=False),
            gate=GateSettings(enabled=False),
            eq=eq,
            limiter=LimiterSettings(enabled=False)
        )
        device.set_gate(1, GateSettings(enabled=False))
        
        assert device._handle.write.call_count >= 1
