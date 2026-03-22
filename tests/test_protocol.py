"""Tests for Presonus IO24 protocol."""

import pytest
from presonus.models import (
    FatChannelSettings,
    ChannelSettings,
    MasterSettings,
    DeviceInfo,
    IO24State,
    PresetType,
)
from presonus.protocol import (
    CommandType,
    ProtocolDiscovery,
    calculate_crc,
)


class TestChannelSettings:
    """Tests for channel settings data classes."""

    def test_fat_channel_defaults(self):
        settings = FatChannelSettings(channel_id=1)
        assert settings.channel_id == 1
        assert settings.gain == 0.0
        assert settings.mute is False
        assert settings.solo is False
        assert settings.preset is None

    def test_channel_extended(self):
        settings = ChannelSettings(channel_id=2, fader=-12.0, gain=20.0)
        assert settings.fader == -12.0
        assert settings.gain == 20.0
        assert settings.input_source == "mic"

    def test_preset_type(self):
        assert PresetType.VOCAL.value == "vocal"
        assert PresetType.GUITAR.value == "guitar"
        assert PresetType.CUSTOM.value == "custom"


class TestDeviceInfo:
    """Tests for device information."""

    def test_device_info_creation(self):
        info = DeviceInfo(
            vendor_id="194f",
            product_id="0422",
            product_name="Revelator IO 24",
            serial_number="ABCD1234",
        )
        assert info.vendor_id == "194f"
        assert info.product_id == "0422"
        assert info.product_name == "Revelator IO 24"
        assert info.serial_number == "ABCD1234"


class TestProtocolDiscovery:
    """Tests for protocol discovery helper."""

    def test_analyze_response_minimal(self):
        response = ProtocolDiscovery.analyze_response(bytes([0x01, 0x02, 0x03]))
        assert response["raw"] == "010203"
        assert response["length"] == 3
        assert response["header"] == "0102"

    def test_analyze_response_short(self):
        response = ProtocolDiscovery.analyze_response(bytes([0x01]))
        assert response["raw"] == "01"
        assert response["length"] == 1
        assert response["header"] is None

    def test_analyze_response_empty(self):
        response = ProtocolDiscovery.analyze_response(bytes([]))
        assert response["raw"] == ""
        assert response["length"] == 0


class TestCRC:
    """Tests for CRC calculation (placeholder)."""

    def test_crc_calculates(self):
        # This is a placeholder - actual CRC algorithm TBD
        result = calculate_crc(b"test data")
        assert isinstance(result, bytes)
        assert len(result) == 2


class TestCommand:
    """Tests for command encoding."""

    def test_command_encode_template(self):
        # Placeholder - actual encoding TBD
        cmd = CommandType.SET_FADER
        assert isinstance(cmd, int)
        assert cmd == 0x01
