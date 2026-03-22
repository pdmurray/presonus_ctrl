"""Comprehensive tests for IO24 models."""

import pytest
from presonus.models import (
    PresetType,
    ChannelSettings,
    FatChannelSettings,
    MasterSettings,
    DeviceInfo,
    IO24State,
)



class TestPresetType:
    """Comprehensive tests for PresetType enum."""

    def test_preset_values_exist(self):
        """Test all preset values are defined."""
        assert PresetType.VOCAL.value == "vocal"
        assert PresetType.GUITAR.value == "guitar"
        assert PresetType.BASS.value == "bass"
        assert PresetType.KEYBOARD.value == "keyboard"
        assert PresetType.DRUMS.value == "drums"
        assert PresetType.CUSTOM.value == "custom"

    def test_preset_names_exist(self):
        """Test all preset names are defined."""
        assert PresetType.VOCAL.name == "VOCAL"
        assert PresetType.GUITAR.name == "GUITAR"
        assert PresetType.BASS.name == "BASS"

    def test_preset_parse_valid(self):
        """Test parsing valid preset names."""
        assert PresetType.parse("vocal") == PresetType.VOCAL
        assert PresetType.parse("guitar") == PresetType.GUITAR
        assert PresetType.parse("bass") == PresetType.BASS
        assert PresetType.parse("keyboard") == PresetType.KEYBOARD
        assert PresetType.parse("drums") == PresetType.DRUMS
        assert PresetType.parse("custom") == PresetType.CUSTOM

    def test_preset_parse_case_sensitive(self):
        """Test that preset parsing is case-sensitive."""
        assert PresetType.parse("vocal") == PresetType.VOCAL
        assert PresetType.parse("VOCAL") is None
        assert PresetType.parse("Guitar") is None

    def test_preset_parse_invalid(self):
        """Test parsing invalid preset names."""
        assert PresetType.parse("invalid") is None
        assert PresetType.parse("") is None
        assert PresetType.parse("nonexistent") is None

    def test_preset_all_values(self):
        """Test iterating over all presets."""
        all_presets = list(PresetType)
        assert len(all_presets) == 6


class TestChannelSettings:
    """Comprehensive tests for ChannelSettings dataclass."""

    def test_channel_valid_creation(self):
        """Test creating valid channel settings."""
        settings = ChannelSettings(channel_id=1)
        assert settings.channel_id == 1
        assert settings.fader == 0.0
        assert settings.gain == 0.0
        assert settings.mute is False
        assert settings.solo is False

    def test_channel_all_fields(self):
        """Test creating channel with all fields."""
        settings = ChannelSettings(
            channel_id=5,
            fader=-12.0,
            gain=20.0,
            mute=True,
            solo=False,
            phase=True,
            input_source="line"
        )
        assert settings.channel_id == 5
        assert settings.fader == -12.0
        assert settings.gain == 20.0
        assert settings.phase is True

    def test_channel_defaults(self):
        """Test default values for gate fields."""
        settings = ChannelSettings(channel_id=10)
        assert settings.gate_enabled is False
        assert settings.gate_threshold == -60.0
        assert settings.gate_attack == 10.0
        assert settings.gate_release == 100.0
        assert settings.phase is False
        assert settings.input_source == "mic"

    def test_channel_to_dict(self):
        """Test conversion to dictionary."""
        settings = ChannelSettings(
            channel_id=3,
            fader=-6.0,
            gain=10.0,
            mute=True
        )
        data = settings.to_dict()
        assert data['channel_id'] == 3
        assert data['gain'] == 10.0
        assert data['mute'] is True
        assert data['gate'] is False

    def test_channel_validation(self):
        """Test channel ID validation."""
        # Channel 0 is valid (master)
        master = ChannelSettings(channel_id=0)
        assert master.channel_id == 0
        
        # Channels 1-24 are valid
        for ch in range(1, 25):
            settings = ChannelSettings(channel_id=ch)
            assert settings.channel_id == ch


class TestFatChannelSettings:
    """Comprehensive tests for FatChannelSettings dataclass."""

    def test_fat_channel_valid_creation(self):
        """Test creating valid fat channel settings."""
        settings = FatChannelSettings(channel_id=1)
        assert settings.channel_id == 1

    def test_fat_channel_compressor_defaults(self):
        """Test compressor defaults."""
        settings = FatChannelSettings(channel_id=1)
        assert settings.compressor["enabled"] is False
        assert settings.compressor["threshold"] == -40.0
        assert settings.compressor["ratio"] == 4.0
        assert settings.compressor["attack"] == 10.0
        assert settings.compressor["release"] == 100.0

    def test_fat_channel_eq_defaults(self):
        """Test EQ defaults."""
        settings = FatChannelSettings(channel_id=1)
        eq = settings.eq
        assert eq["low"] == 0.0
        assert eq["low_mid"] == 0.0
        assert eq["high_mid"] == 0.0
        assert eq["high"] == 0.0

    def test_fat_channel_gate_fields(self):
        """Test gate fields in fat channel."""
        settings = FatChannelSettings(
            channel_id=1,
            gate_enabled=True,
            gate_threshold=-50.0,
            gate_attack=20.0,
            gate_release=200.0
        )
        assert settings.gate_enabled is True
        assert settings.gate_threshold == -50.0
        assert settings.gate_attack == 20.0
        assert settings.gate_release == 200.0

    def test_fat_channel_presets(self):
        """Test preset assignments."""
        for preset in PresetType:
            settings = FatChannelSettings(channel_id=1, preset=preset)
            assert settings.preset == preset

    def test_fat_channel_to_dict(self):
        """Test conversion to dictionary."""
        settings = FatChannelSettings(
            channel_id=4,
            gain=8.0,
            mute=True,
            pan=10,
            preset=PresetType.GUITAR,
            gate_enabled=True
        )
        data = settings.to_dict()
        assert data['channel_id'] == 4
        assert data['gain'] == 8.0
        assert data['mute'] is True
        assert data['pan'] == 10
        assert data['preset'] == "guitar"
        assert data['gate'] is True


class TestMasterSettings:
    """Comprehensive tests for MasterSettings dataclass."""

    def test_master_defaults(self):
        """Test master settings defaults."""
        settings = MasterSettings()
        assert settings.main_l_r_fader == 0.0
        assert settings.monitor_fader == 0.0
        assert settings.headphones_fader == 0.0
        assert settings.main_l_r_pan == {"left": 0, "right": 0}

    def test_master_custom_values(self):
        """Test master with custom values."""
        settings = MasterSettings(
            main_l_r_fader=-6.0,
            monitor_fader=-12.0,
            headphones_fader=-3.0
        )
        assert settings.main_l_r_fader == -6.0
        assert settings.monitor_fader == -12.0
        assert settings.headphones_fader == -3.0

    def test_master_to_dict(self):
        """Test conversion to dictionary."""
        settings = MasterSettings(
            main_l_r_fader=-3.0,
            monitor_fader=-6.0,
            headphones_fader=-9.0
        )
        data = settings.to_dict()
        assert data['main_l_r_fader'] == -3.0
        assert data['monitor_fader'] == -6.0
        assert data['headphones_fader'] == -9.0


class TestDeviceInfo:
    """Comprehensive tests for DeviceInfo dataclass."""

    def test_device_info_creation(self):
        """Test creating device info."""
        info = DeviceInfo(
            vendor_id="194f",
            product_id="0422",
            product_name="Revelator IO 24",
            serial_number="ABCD1234"
        )
        assert info.vendor_id == "194f"
        assert info.product_id == "0422"
        assert info.product_name == "Revelator IO 24"
        assert info.serial_number == "ABCD1234"

    def test_device_info_with_none_serial(self):
        """Test device info without serial."""
        info = DeviceInfo(
            vendor_id="194f",
            product_id="0422",
            product_name="Revelator IO 24"
        )
        assert info.serial_number is None

    def test_device_info_all_optional(self):
        """Test device info with all optional fields."""
        info = DeviceInfo(
            vendor_id="194f",
            product_id="0422",
            product_name="Revelator IO 24",
            serial_number="XYZ789",
            firmware_version="1.2.3"
        )
        assert info.firmware_version == "1.2.3"

    def test_device_info_defaults(self):
        """Test device info defaults."""
        info = DeviceInfo(
            vendor_id="194f",
            product_id="0422",
            product_name="Revelator IO 24"
        )
        assert info.serial_number is None
        assert info.firmware_version is None


class TestIO24State:
    """Comprehensive tests for IO24State dataclass."""

    def test_io24_state_empty(self):
        """Test empty state creation."""
        state = IO24State()
        assert len(state.channels) == 0
        assert state.master is None

    def test_io24_state_with_channels(self):
        """Test state with multiple channels."""
        state = IO24State(
            channels={
                1: ChannelSettings(channel_id=1, gain=10.0),
                2: ChannelSettings(channel_id=2, fader=-6.0),
                3: ChannelSettings(channel_id=3, mute=True),
            },
            master=MasterSettings(main_l_r_fader=-3.0)
        )
        assert len(state.channels) == 3
        assert state.master.main_l_r_fader == -3.0

    def test_io24_state_all_channels(self):
        """Test state with all 24 channels."""
        channels = {
            i: ChannelSettings(channel_id=i, gain=i * 0.5)
            for i in range(1, 25)
        }
        state = IO24State(channels=channels)
        assert len(state.channels) == 24

    def test_io24_state_channel_access(self):
        """Test channel access methods."""
        state = IO24State(
            channels={
                1: ChannelSettings(channel_id=1),
                5: ChannelSettings(channel_id=5),
                10: ChannelSettings(channel_id=10),
            }
        )
        # Channels are stored in a dict keyed by channel_id
        assert state.channels[1].channel_id == 1
        assert 5 in state.channels
        assert 10 in state.channels
        
        # Non-existent channel
        assert 99 not in state.channels

    def test_io24_state_to_dict(self):
        """Test state serialization."""
        state = IO24State(
            channels={
                1: ChannelSettings(channel_id=1, gain=10.0),
                2: ChannelSettings(channel_id=2, fader=-6.0),
            },
            master=MasterSettings(main_l_r_fader=-3.0)
        )
        data = state.to_dict()
        assert 'channels' in data
        assert 'master' in data
        assert 'device_info' in data
        assert len(data['channels']) == 2
        assert data['master']['main_l_r_fader'] == -3.0

    def test_io24_state_empty_to_dict(self):
        """Test empty state serialization."""
        state = IO24State()
        data = state.to_dict()
        assert len(data['channels']) == 0
        assert data['master'] is None
        assert data['device_info'] is None
