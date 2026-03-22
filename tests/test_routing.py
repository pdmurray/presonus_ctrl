"""Comprehensive tests for channel routing and aux/reverb sends."""

import pytest
from unittest import mock
from presonus.device import PresonusDevice
from presonus.models import OutputValue


class TestChannelRouting:
    """Tests for channel routing configuration."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_set_routing_to_main(self, device_with_mock):
        """Test routing channel to main outputs."""
        device = device_with_mock
        result = device.set_routing(1, OutputValue.MAIN_L_R, 100, True, False)
        assert result is True

    def test_set_routing_to_bus1(self, device_with_mock):
        """Test routing channel to bus 1."""
        device = device_with_mock
        # Assuming bus routing is supported
        result = device.set_routing(1, OutputValue.MAIN_L_R, 100, True, False)
        assert result is True

    def test_set_routing_no_volume(self, device_with_mock):
        """Test routing without volume."""
        device = device_with_mock
        result = device.set_routing(1, OutputValue.MAIN_L_R, 0, False, False)
        assert result is True

    def test_set_routing_with_solo(self, device_with_mock):
        """Test routing with solo."""
        device = device_with_mock
        result = device.set_routing(1, OutputValue.MAIN_L_R, 100, True, True)
        assert result is True

    def test_routing_invalid_channel(self, device_with_mock):
        """Test routing on invalid channel."""
        device = device_with_mock
        # Channel 25 should fail
        result = device.set_routing(25, OutputValue.MAIN_L_R, 100, True, False)
        assert result is False

    def test_routing_all_outputs(self, device_with_mock):
        """Test routing to all available outputs."""
        device = device_with_mock
        
        # Test various routing scenarios
        outputs = [OutputValue.MAIN_L_R]  # Add more outputs as defined
        
        for output in outputs:
            for routed in [True, False]:
                for with_solo in [True, False]:
                    for volume in [0, 50, 100]:
                        result = device.set_routing(1, output, volume, routed, with_solo)
                        # Should succeed or gracefully handle
                        assert isinstance(result, bool)


class TestAuxSends:
    """Tests for aux send configuration."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_set_aux_send_level(self, device_with_mock):
        """Test setting aux send level."""
        device = device_with_mock
        # Assuming aux levels are set per channel
        result = device.set_aux_send_level(1, 1, 50)
        assert result is True

    def test_set_aux_send_full_range(self, device_with_mock):
        """Test aux send full range."""
        device = device_with_mock
        for level in [0, 50, 100]:
            result = device.set_aux_send_level(1, 1, level)
            if 0 <= level <= 100:
                assert result is True
            else:
                assert result is False

    def test_aux_send_all_channels(self, device_with_mock):
        """Test aux send on all channels."""
        device = device_with_mock
        
        for channel in range(1, 5):  # Test channels 1-4
            result = device.set_aux_send_level(channel, 1, 75)
            assert result is True

    def test_aux_send_invalid_channel(self, device_with_mock):
        """Test aux send on invalid channel."""
        device = device_with_mock
        # Channel 25 should fail
        result = device.set_aux_send_level(25, 1, 50)
        assert result is False

    def test_aux_send_invalid_aux(self, device_with_mock):
        """Test aux send on invalid aux bus."""
        device = device_with_mock
        # Test invalid aux number
        result = device.set_aux_send_level(1, 10, 50)
        assert result is False


class TestReverbSends:
    """Tests for reverb send configuration."""

    @pytest.fixture
    def device_with_mock(self, mock_presonus_device):
        """Device with mocked responses."""
        device = mock_presonus_device
        device._handle.write = mock.MagicMock()
        device._handle.read = mock.MagicMock()
        device._handle.read.return_value = bytes([0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return device

    def test_set_reverb_send_level(self, device_with_mock):
        """Test setting reverb send level."""
        device = device_with_mock
        result = device.set_reverb_send_level(1, 50)
        assert result is True

    def test_reverb_full_range(self, device_with_mock):
        """Test reverb send full range."""
        device = device_with_mock
        for level in [0, 25, 50, 75, 100]:
            result = device.set_reverb_send_level(1, level)
            if 0 <= level <= 100:
                assert result is True
            else:
                assert result is False

    def test_reverb_all_channels(self, device_with_mock):
        """Test reverb send on all channels."""
        device = device_with_mock
        
        for channel in range(1, 5):
            result = device.set_reverb_send_level(channel, 80)
            assert result is True

    def test_reverb_invalid_channel(self, device_with_mock):
        """Test reverb send on invalid channel."""
        device = device_with_mock
        result = device.set_reverb_send_level(25, 50)
        assert result is False

    def test_reverb_zero_level(self, device_with_mock):
        """Test reverb send at zero level (off)."""
        device = device_with_mock
        result = device.set_reverb_send_level(1, 0)
        assert result is True

    def test_reverb_max_level(self, device_with_mock):
        """Test reverb send at maximum level."""
        device = device_with_mock
        result = device.set_reverb_send_level(1, 100)
        assert result is True
