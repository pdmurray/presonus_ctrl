"""Data models for Presonus IO24 configuration.

These models intentionally provide a compatibility layer for the current
mocked test suite. They represent a stable public API, not a claim that the
real USB protocol is fully understood yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class OutputId(Enum):
    """Logical output identifiers."""

    MAIN = "main"
    MIX_A = "mix_a"
    MIX_B = "mix_b"


class OutputValue(Enum):
    """Routing output targets used by the current tests."""

    MAIN_L_R = "main_l_r"
    MAIN_1_2 = "main_1_2"


class DeviceType(Enum):
    """Supported device type identifiers."""

    IO24 = "io24"
    IO44 = "io44"


class HeadphonesSource(Enum):
    """Headphone monitor source aliases used across tests and CLI."""

    LINE = "line"
    MONITOR = "monitor"
    HOTKEY = "hotkey"
    MAIN = "line"
    MIX_A = "monitor"
    MIX_B = "hotkey"


class PresetType(Enum):
    """Fat channel preset types.

    A few extra aliases are included because the current tests reference more
    preset names than the rest of the project currently documents.
    """

    VOCAL = "vocal"
    GUITAR = "guitar"
    BASS = "bass"
    KEYBOARD = "keyboard"
    DRUMS = "drums"
    CUSTOM = "custom"
    SNARE = "drums"
    DRUM_MIC = "drums"

    @classmethod
    def parse(cls, name: str) -> Optional["PresetType"]:
        for member in cls:
            if member.value == name:
                return member
        return None


@dataclass(frozen=True)
class VolumeValue:
    """Normalized channel/output volume helper.

    `raw` is stored as dB for compatibility with the current device API tests.
    """

    raw: float
    db: float

    @classmethod
    def from_db(cls, db: float) -> "VolumeValue":
        return cls(raw=float(db), db=float(db))


OutputVolume = VolumeValue


@dataclass(frozen=True)
class GainValue:
    """Gain helper storing the passed dB value as raw."""

    raw: float
    db: float

    @classmethod
    def from_db(cls, db: float) -> "GainValue":
        return cls(raw=float(db), db=float(db))


@dataclass(frozen=True)
class PanValue:
    """Pan helper compatible with the current tests."""

    value: int
    raw: int
    left_to_right: float

    @classmethod
    def center(cls) -> "PanValue":
        return cls(value=0, raw=0, left_to_right=0.0)

    @classmethod
    def from_db(cls, db: float) -> "PanValue":
        value = int(max(-100, min(100, round(db))))
        return cls(value=value, raw=value, left_to_right=value / 100.0)


@dataclass(frozen=True)
class BlendValue:
    """Monitor blend helper."""

    value: int

    @classmethod
    def balanced(cls) -> "BlendValue":
        return cls(0)


class FrequencyBand(Enum):
    """Named EQ bands."""

    LOW = "low"
    LOW_MID = "low_mid"
    HIGH_MID = "high_mid"
    HIGH = "high"


@dataclass
class CompressorSettings:
    """Compressor settings."""

    enabled: bool = False
    threshold: float = -40.0
    ratio: float = 4.0
    attack: float = 10.0
    release: float = 100.0
    output_gain: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "threshold": self.threshold,
            "ratio": self.ratio,
            "attack": self.attack,
            "release": self.release,
            "output_gain": self.output_gain,
        }


@dataclass
class GateSettings:
    """Gate settings."""

    enabled: bool = False
    threshold: float = -60.0
    ratio: float = 4.0
    attack: float = 10.0
    release: float = 100.0
    hold: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "threshold": self.threshold,
            "ratio": self.ratio,
            "attack": self.attack,
            "release": self.release,
            "hold": self.hold,
        }


@dataclass
class EqSettings:
    """Simple four-band EQ settings container."""

    bands: Dict[FrequencyBand, Dict[str, float]] = field(
        default_factory=lambda: {
            band: {"gain": 0.0, "freq": 1000.0, "q": 0.0}
            for band in FrequencyBand
        }
    )

    def set_band(
        self,
        band: FrequencyBand,
        gain: float,
        freq: float = 1000.0,
        q: float = 0.0,
    ) -> None:
        self.bands[band] = {"gain": float(gain), "freq": float(freq), "q": float(q)}

    def to_dict(self) -> Dict[str, Dict[str, float]]:
        return {band.value: values.copy() for band, values in self.bands.items()}


@dataclass
class LimiterSettings:
    """Limiter settings."""

    enabled: bool = False
    threshold: float = -6.0
    release: float = 50.0
    lookahead: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "threshold": self.threshold,
            "release": self.release,
            "lookahead": self.lookahead,
        }


@dataclass
class FatChannelSettings:
    """Fat Channel DSP settings."""

    channel_id: int = 0
    gain: float = 0.0
    fader: float = 0.0
    mute: bool = False
    solo: bool = False
    pan: float = 0.0
    preset: Optional[PresetType] = None
    compressor: Any = field(default_factory=lambda: CompressorSettings().to_dict())
    gate: Any = None
    eq: Any = field(
        default_factory=lambda: {
            "low": 0.0,
            "low_mid": 0.0,
            "high_mid": 0.0,
            "high": 0.0,
        }
    )
    gate_enabled: bool = False
    gate_threshold: float = -60.0
    gate_attack: float = 10.0
    gate_release: float = 100.0
    compressor_enabled: bool = False
    eq_enabled: bool = False
    compressor_threshold: float = -40.0
    compressor_ratio: float = 4.0
    eq_low_gain: float = 0.0
    eq_mid_gain: float = 0.0
    eq_high_gain: float = 0.0
    limiter: Any = None
    limiter_enabled: bool = False
    limiter_threshold: float = -6.0
    reverb: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.compressor, CompressorSettings):
            self.compressor = self.compressor.to_dict()
        elif self.compressor is None:
            self.compressor = CompressorSettings().to_dict()

        if isinstance(self.gate, GateSettings):
            self.gate_enabled = self.gate.enabled
            self.gate_threshold = self.gate.threshold
            self.gate_attack = self.gate.attack
            self.gate_release = self.gate.release

        if isinstance(self.eq, EqSettings):
            eq_dict = self.eq.to_dict()
            self.eq = {
                "low": eq_dict[FrequencyBand.LOW.value]["gain"],
                "low_mid": eq_dict[FrequencyBand.LOW_MID.value]["gain"],
                "high_mid": eq_dict[FrequencyBand.HIGH_MID.value]["gain"],
                "high": eq_dict[FrequencyBand.HIGH.value]["gain"],
            }

        if isinstance(self.limiter, LimiterSettings):
            self.limiter_enabled = self.limiter.enabled
            self.limiter_threshold = self.limiter.threshold

        if "enabled" in self.compressor:
            self.compressor_enabled = bool(self.compressor["enabled"])
        self.compressor.setdefault("enabled", self.compressor_enabled)
        self.compressor.setdefault("threshold", self.compressor_threshold)
        self.compressor.setdefault("ratio", self.compressor_ratio)
        self.compressor.setdefault("attack", 10.0)
        self.compressor.setdefault("release", 100.0)

        self.eq.setdefault("low", self.eq_low_gain)
        self.eq.setdefault("low_mid", self.eq_mid_gain)
        self.eq.setdefault("high_mid", self.eq_mid_gain)
        self.eq.setdefault("high", self.eq_high_gain)

        self.compressor_enabled = bool(self.compressor.get("enabled", self.compressor_enabled))
        self.compressor_threshold = float(self.compressor.get("threshold", self.compressor_threshold))
        self.compressor_ratio = float(self.compressor.get("ratio", self.compressor_ratio))
        self.eq_low_gain = float(self.eq.get("low", self.eq_low_gain))
        self.eq_mid_gain = float(self.eq.get("low_mid", self.eq_mid_gain))
        self.eq_high_gain = float(self.eq.get("high", self.eq_high_gain))

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "channel_id": self.channel_id,
            "gain": self.gain,
            "fader": self.fader,
            "mute": self.mute,
            "solo": self.solo,
            "pan": self.pan,
            "compressor": dict(self.compressor),
            "eq": dict(self.eq),
            "gate_enabled": self.gate_enabled,
            "gate": self.gate_enabled,
            "gate_threshold": self.gate_threshold,
            "gate_attack": self.gate_attack,
            "gate_release": self.gate_release,
            "limiter_enabled": self.limiter_enabled,
            "limiter_threshold": self.limiter_threshold,
            "reverb": self.reverb,
        }
        if self.preset is not None:
            data["preset"] = self.preset.value
        return data


@dataclass
class ChannelSettings:
    """Channel configuration."""

    channel_id: int
    gain: float = 0.0
    fader: float = 0.0
    mute: bool = False
    solo: bool = False
    phase: bool = False
    input_source: str = "mic"
    pan: float = 0.0
    preset: Optional[PresetType] = None
    eq: Dict[str, float] = field(
        default_factory=lambda: {
            "low": 0.0,
            "low_mid": 0.0,
            "high_mid": 0.0,
            "high": 0.0,
        }
    )
    compressor: Dict[str, Any] = field(default_factory=lambda: CompressorSettings().to_dict())
    gate_enabled: bool = False
    gate_threshold: float = -60.0
    gate_attack: float = 10.0
    gate_release: float = 100.0

    @classmethod
    def from_binary(cls, _data: bytes, channel_id: int) -> "ChannelSettings":
        return cls(channel_id=channel_id)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "channel_id": self.channel_id,
            "fader": self.fader,
            "gain": self.gain,
            "mute": self.mute,
            "solo": self.solo,
            "phase": self.phase,
            "input_source": self.input_source,
            "pan": self.pan,
            "eq": dict(self.eq),
            "compressor": dict(self.compressor),
            "gate_enabled": self.gate_enabled,
            "gate": self.gate_enabled,
            "gate_threshold": self.gate_threshold,
            "gate_attack": self.gate_attack,
            "gate_release": self.gate_release,
        }
        if self.preset is not None:
            data["preset"] = self.preset.value
        return data


@dataclass
class MasterSettings:
    """Master settings."""

    main_l_r_fader: float = 0.0
    monitor_fader: float = 0.0
    headphones_fader: float = 0.0
    main_l_r_pan: Dict[str, int] = field(default_factory=lambda: {"left": 0, "right": 0})

    @classmethod
    def from_binary(cls, _data: bytes) -> "MasterSettings":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "main_l_r_fader": self.main_l_r_fader,
            "monitor_fader": self.monitor_fader,
            "headphones_fader": self.headphones_fader,
            "main_l_r_pan": dict(self.main_l_r_pan),
        }


@dataclass
class DeviceInfo:
    """Device information."""

    vendor_id: str
    product_id: str
    product_name: str
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    device_type: DeviceType = DeviceType.IO24

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vendor_id": self.vendor_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "serial_number": self.serial_number,
            "firmware_version": self.firmware_version,
            "device_type": self.device_type.value,
        }


@dataclass
class RoutingEntry:
    """Routing entry."""

    channel_id: int
    output: str
    volume: float = 0.0
    routed: bool = False
    solo: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "output": self.output,
            "volume": self.volume,
            "routed": self.routed,
            "solo": self.solo,
        }


@dataclass
class IO24State:
    """Complete device state."""

    channels: Dict[int, ChannelSettings] = field(default_factory=dict)
    master: Optional[MasterSettings] = None
    device_info: Optional[DeviceInfo] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channels": {str(k): v.to_dict() for k, v in self.channels.items()},
            "master": self.master.to_dict() if self.master else None,
            "device_info": self.device_info.to_dict() if self.device_info else None,
        }


# Backward compatibility aliases.
ChannelState = ChannelSettings
MasterState = MasterSettings
