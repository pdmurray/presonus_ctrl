"""Tests for the partial protocol backend."""

from unittest import mock

import pytest

from presonus.device import PresonusDevice
from presonus.models import HeadphonesSource, PresetType


@pytest.mark.unit
class TestProtocolBackend:
    def test_protocol_mode_reports_backend(self):
        device = PresonusDevice(mode="protocol")
        assert device.mode == "protocol"

    def test_protocol_backend_supported_setters_write(self, mock_presonus_device):
        device = PresonusDevice(mode="protocol")
        device._handle = mock.MagicMock()
        device._initialized = True

        assert device.set_channel_mute(1, True) is True
        assert device.set_channel_solo(1, False) is True
        assert device.set_channel_phase(1, True) is True
        assert device.set_channel_preset(1, PresetType.VOCAL) is True
        assert device.set_headphones_source(HeadphonesSource.MONITOR) is True
        assert device._handle.write.call_count == 5

    def test_protocol_backend_invalid_channel_returns_false(self):
        device = PresonusDevice(mode="protocol")
        device._handle = mock.MagicMock()
        device._initialized = True

        assert device.set_channel_mute(0, True) is False
        assert device.set_channel_solo(25, True) is False

    def test_protocol_backend_unsupported_method_raises(self):
        device = PresonusDevice(mode="protocol")
        device._handle = mock.MagicMock()
        device._initialized = True

        with pytest.raises(NotImplementedError):
            device.set_channel_volume(1, -10.0)

        with pytest.raises(NotImplementedError):
            device.query_state()
