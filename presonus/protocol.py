"""USB protocol command definitions for Presonus IO24.

This module contains the protocol command structure definitions.
The actual USB communication needs to be reverse-engineered from
the device behavior.
"""

import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional


class ProtocolCommand(IntEnum):
    """Presonus USB protocol command codes."""
    # Device info and state
    CMD_GET_DEVICE_INFO = 0x01
    CMD_QUERY_DEVICE_STATE = 0x02
    CMD_SYNC_STATE = 0x03
    
    # Channel control
    CMD_GET_CHANNEL_STATE = 0x10
    CMD_SET_CHANNEL_STATE = 0x11
    CMD_GET_FAT_CHANNEL = 0x12
    CMD_SET_FAT_CHANNEL = 0x13
    
    # Volume and level control
    CMD_SET_VOLUME = 0x20
    CMD_GET_VOLUME = 0x21
    CMD_SET_GAIN = 0x22
    CMD_SET_PHANTOM_POWER = 0x23
    CMD_SET_PAN = 0x24
    CMD_SET_MUTE = 0x25
    CMD_SET_SOLO = 0x26
    
    # Preset management
    CMD_QUERY_PRESETS = 0x30
    CMD_SET_PRESET = 0x31
    CMD_LOAD_PRESET = 0x32
    
    # DSP effects
    CMD_SET_COMPRESSOR = 0x40
    CMD_SET_GATE = 0x41
    CMD_SET_EQ = 0x42
    CMD_SET_LIMITER = 0x43
    CMD_DSP_ENABLE = 0x44
    
    # Routing control
    CMD_QUERY_ROUTING = 0x50
    CMD_SET_ROUTING_VOLUME = 0x51
    CMD_SET_ROUTING = 0x52
    CMD_TOGGLE_ROUTING = 0x53
    CMD_SET_ROUTING_SOLO = 0x54
    CMD_GET_ROUTING_SLOTS = 0x55
    
    # Master controls
    CMD_SET_MASTER_VOLUME = 0x60
    CMD_SET_HEADPHONES_SOURCE = 0x61
    CMD_SET_HEADPHONES_VOLUME = 0x62
    CMD_SET_MONITOR_BLEND = 0x63
    CMD_SET_AUX_MIRROR = 0x64
    
    # Auxiliary sends
    CMD_SET_AUX_SEND = 0x70
    
    # Reverb
    CMD_SET_REVERB_SEND = 0x80
    
    # System
    CMD_PING = 0xFE
    CMD_PONG = 0xFF


@dataclass
class ProtocolHeader:
    """Protocol message header structure."""
    version: int = 1  # Protocol version
    command: int = 0  # Command code
    channel_id: int = 0  # Channel number (0 = master/global)
    data_length: int = 0  # Length of payload
    
    def encode(self) -> bytes:
        """Encode header to bytes."""
        return struct.pack('>BBBB', 
            0x02,  # Magic byte
            self.version,
            self.command,
            self.channel_id
        )
    
    @classmethod
    def decode(cls, data: bytes) -> 'ProtocolHeader':
        """Decode header from bytes."""
        if len(data) < 4:
            return cls()
        return cls(
            version=data[1],
            command=data[2],
            channel_id=data[3],
        )
    
    @classmethod
    def create(cls, command: int, channel_id: int = 0) -> 'ProtocolHeader':
        """Create header for a command."""
        return cls(
            version=1,
            command=command,
            channel_id=channel_id,
            data_length=0,
        )


@dataclass
class ChannelMessage:
    """Channel-specific message structure."""
    channel_id: int
    command: int
    payload: bytes = b""
    
    def encode(self) -> bytes:
        """Encode complete message with header."""
        header = ProtocolHeader.create(self.command, self.channel_id)
        header.data_length = len(self.payload)
        return header.encode() + self.payload
    
    @classmethod
    def decode(cls, data: bytes) -> Optional['ChannelMessage']:
        """Decode message from bytes."""
        if len(data) < 4:
            return None
        header = ProtocolHeader.decode(data)
        expected_len = 4 + header.data_length
        if len(data) < expected_len:
            return None
        return cls(
            channel_id=header.channel_id,
            command=header.command,
            payload=data[4:expected_len],
        )
    
    @classmethod
    def from_command(cls, channel_id: int, command: int, 
                     data: Optional[bytes] = None) -> 'ChannelMessage':
        """Create message from command code."""
        return cls(
            channel_id=channel_id,
            command=command,
            payload=data or b"",
        )


class VolumeMessage:
    """Volume/level value encoding/decoding."""
    
    @staticmethod
    def encode_db_to_raw(db: float) -> int:
        """Convert dB to raw value (0-1023)."""
        if db <= -96:
            return 0
        elif db >= 0:
            return 1023
        return int(1023 * (10 ** (db / 20)))
    
    @staticmethod
    def encode_raw_to_db(raw: int) -> float:
        """Convert raw value to dB."""
        import math
        if raw <= 0:
            return -96.0
        elif raw >= 1023:
            return 0.0
        return 20 * math.log10(raw / 1023)
    
    @staticmethod
    def encode_volume_value(value: float) -> bytes:
        """Encode volume value as 2-byte little-endian."""
        raw = int(value * 1023)
        return struct.pack('<H', raw)
    
    @staticmethod
    def decode_volume_value(data: bytes) -> float:
        """Decode volume value from 2-byte little-endian."""
        if len(data) < 2:
            return 0.5
        raw = struct.unpack('<H', data[:2])[0]
        return raw / 1023.0


class GainMessage:
    """Gain value encoding/decoding."""
    
    MIN_DB = -18.0
    MAX_DB = 66.0
    RANGE_DB = MAX_DB - MIN_DB
    
    @staticmethod
    def encode_db_to_raw(db: float) -> int:
        """Convert dB to raw value (0-127)."""
        raw = int((db - GainMessage.MIN_DB) / GainMessage.RANGE_DB * 127)
        return max(0, min(127, raw))
    
    @staticmethod
    def encode_raw_to_db(raw: int) -> float:
        """Convert raw value to dB."""
        return GainMessage.MIN_DB + (raw / 127.0) * GainMessage.RANGE_DB
    
    @staticmethod
    def encode_gain_value(db: float) -> bytes:
        """Encode gain in dB as 1 byte."""
        raw = GainMessage.encode_db_to_raw(db)
        return struct.pack('B', raw)
    
    @staticmethod
    def decode_gain_value(data: bytes) -> float:
        """Decode gain from 1 byte."""
        if len(data) < 1:
            return GainMessage.MIN_DB
        raw = struct.unpack('B', data[:1])[0]
        return GainMessage.encode_raw_to_db(raw)


class PanMessage:
    """Pan position encoding/decoding."""
    
    @staticmethod
    def encode_left_right_to_raw(lr: float) -> int:
        """Convert left-to-right (-1 to 1) to raw (0-127)."""
        return int(((lr + 1.0) / 2.0) * 127)
    
    @staticmethod
    def encode_raw_to_left_right(raw: int) -> float:
        """Convert raw (0-127) to left-to-right (-1 to 1)."""
        return (raw / 127.0) * 2.0 - 1.0
    
    @staticmethod
    def encode_pan_value(value: float) -> bytes:
        """Encode pan value (-1 to 1) as 1 byte."""
        raw = PanMessage.encode_left_right_to_raw(value)
        return struct.pack('B', raw)
    
    @staticmethod
    def decode_pan_value(data: bytes) -> float:
        """Decode pan from 1 byte."""
        if len(data) < 1:
            return 0.0
        raw = struct.unpack('B', data[:1])[0]
        return PanMessage.encode_raw_to_left_right(raw)


@dataclass
class CompressorMessage:
    """Compressor settings encoding."""
    enabled: bool = True
    threshold: int = 0  # 0-127 (-40 to 0 dB)
    ratio: int = 0  # 0-127 (1:1 to 20:1)
    attack: int = 0  # 0-127 (1-100 ms)
    release: int = 0  # 0-127 (10-500 ms)
    makeup: int = 0  # -6 to 6 dB
    
    @classmethod
    def from_settings(cls, threshold: float, ratio: float, 
                      attack: float, release: float, makeup: float) -> 'CompressorMessage':
        """Create from compressor settings."""
        return cls(
            threshold=cls._db_to_raw(threshold, -40, 0),
            ratio=cls._ratio_to_raw(ratio, 1, 20),
            attack=cls._ms_to_raw(attack, 1, 100),
            release=cls._ms_to_raw(release, 10, 500),
            makeup=cls._db_to_raw(makeup, -6, 6),
        )
    
    @staticmethod
    def _db_to_raw(db: float, min_db: float, max_db: float) -> int:
        return max(0, min(127, int((db - min_db) / (max_db - min_db) * 127)))
    
    @staticmethod
    def _ratio_to_raw(ratio: float, min_r: float, max_r: float) -> int:
        return max(0, min(127, int((ratio - min_r) / (max_r - min_r) * 127)))
    
    @staticmethod
    def _ms_to_raw(ms: float, min_ms: float, max_ms: float) -> int:
        return max(0, min(127, int((ms - min_ms) / (max_ms - min_ms) * 127)))
    
    def encode(self) -> bytes:
        return bytes([
            int(self.enabled),
            self.threshold, self.ratio,
            self.attack, self.release,
            self.makeup,
        ])


@dataclass
class GateMessage:
    """Gate settings encoding."""
    enabled: bool = True
    threshold: int = 0  # 0-127
    attack: int = 0  # 0-127
    release: int = 0  # 0-127
    hysteresis: int = 0  # 0-127
    
    def encode(self) -> bytes:
        return bytes([
            int(self.enabled),
            self.threshold, self.attack, self.release, self.hysteresis,
        ])


@dataclass
class EqMessage:
    """EQ settings encoding (4 bands)."""
    bands: List[dict] = field(default_factory=lambda: [
        {"enabled": True, "freq": 64, "q": 64, "gain": 64},
        {"enabled": True, "freq": 64, "q": 64, "gain": 64},
        {"enabled": True, "freq": 64, "q": 64, "gain": 64},
        {"enabled": True, "freq": 64, "q": 64, "gain": 64},
    ])
    
    def encode(self) -> bytes:
        result = []
        for band in self.bands:
            result.extend([
                int(band["enabled"]),
                band["freq"], band["q"], band["gain"]
            ])
        return bytes(result)


@dataclass
class LimiterMessage:
    """Limiter settings encoding."""
    enabled: bool = True
    threshold: int = 0  # -127 to 127 (approx -20 to +5 dB)
    release: int = 0  # 0-127
    
    def encode(self) -> bytes:
        return bytes([
            int(self.enabled),
            self.threshold, self.release,
        ])


@dataclass
class RoutingEntry:
    """Routing slot entry."""
    channel_id: int
    output: int
    volume: int
    routed: bool
    solo: bool
    
    @classmethod
    def decode(cls, data: bytes) -> Optional['RoutingEntry']:
        if len(data) < 4:
            return None
        return cls(
            channel_id=data[0],
            output=data[1],
            volume=struct.unpack('<H', data[2:4])[0],
            routed=bool(data[4]) if len(data) > 4 else False,
            solo=bool(data[5]) if len(data) > 5 else False,
        )


def create_preset_message(preset_type: str, preset_name: str) -> bytes:
    """Create preset selection message."""
    preset_map = {
        "vocal": 0x01,
        "guitar": 0x02,
        "bass": 0x03,
        "keyboard": 0x04,
        "drums": 0x05,
        "custom": 0xFF,
    }
    code = preset_map.get(preset_type.lower(), 0xFF)
    name_bytes = preset_name.encode('utf-8')[:16].ljust(16, b'\x00')
    return bytes([code]) + name_bytes


def create_channel_command(channel_id: int, command: int, payload: bytes = b"") -> bytes:
    """Create a complete channel command message."""
    header = bytes([0x02, 0x01, command, channel_id & 0xFF])
    header += struct.pack('<H', len(payload))
    return header + payload


def create_query_response(command: int, payload: bytes) -> bytes:
    """Create a query response message."""
    return bytes([0x82, 0x01, command, 0x00]) + payload



def calculate_crc(data: bytes) -> bytes:
    """Calculate 16-bit CRC and return as 2 bytes."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return bytes([(crc >> 8) & 0xFF, crc & 0xFF])

class CRC8:
    """8-bit CRC calculation for protocol validation."""
    
    @staticmethod
    def calculate(data: bytes) -> int:
        """Calculate CRC-8 of data."""
        crc = 0x00
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x07) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc
    
    @staticmethod
    def verify(data: bytes) -> bool:
        """Verify CRC-8 of data (excluding CRC byte)."""
        if len(data) < 1:
            return False
        calculated = CRC8.calculate(data[:-1])
        return calculated == data[-1]



class CommandType(IntEnum):
    """Command type codes."""
    GET_CHANNEL_STATE = 0x00
    SET_CHANNEL_LEVEL = 0x01
    SET_FADER = 0x01
    GET_DEVICE_INFO = 0x02
    QUERY_DEVICE_STATE = 0x03
    SYNC_STATE = 0x04
    
    # Channel state and fat channel
    SET_CHANNEL_STATE = 0x11
    GET_FAT_CHANNEL = 0x12
    SET_FAT_CHANNEL = 0x13
    
    # Volume, gain, pan, mute, solo
    SET_VOLUME = 0x20
    GET_VOLUME = 0x21
    SET_GAIN = 0x22
    SET_PHANTOM_POWER = 0x23
    SET_PAN = 0x24
    SET_MUTE = 0x25
    SET_SOLO = 0x26
    
    # Presets
    QUERY_PRESETS = 0x30
    SET_PRESET = 0x31
    LOAD_PRESET = 0x32
    
    # DSP - compressor, gate, EQ, limiter
    SET_COMPRESSOR = 0x40
    SET_GATE = 0x41
    SET_EQ = 0x42
    SET_LIMITER = 0x43
    DSP_ENABLE = 0x44
    
    # Routing
    QUERY_ROUTING = 0x50
    SET_ROUTING_VOLUME = 0x51
    SET_ROUTING = 0x52
    TOGGLE_ROUTING = 0x53
    SET_ROUTING_SOLO = 0x54
    GET_ROUTING_SLOTS = 0x55
    
    # Master output
    SET_MASTER_VOLUME = 0x60
    SET_HEADPHONES_SOURCE = 0x61
    SET_MONITOR_SOURCE = 0x62
    SET_MONITOR_MIX = 0x63
    SET_MASTER_MONITOR_MIX = 0x64
    QUERY_MASTER_STATE = 0x65

def serialize_bool(value: bool) -> bytes:
    """Serialize boolean as single byte."""
    return bytes([1 if value else 0])


def deserialize_bool(data: bytes) -> bool:
    """Deserialize boolean from single byte."""
    return bool(data[0]) if data else False


def serialize_int8(value: int) -> bytes:
    """Serialize signed int8 as single byte."""
    return struct.pack('b', value)


def deserialize_int8(data: bytes) -> int:
    """Deserialize signed int8 from single byte."""
    return struct.unpack('b', data[:1])[0]


def serialize_int16(value: int) -> bytes:
    """Serialize signed int16 as 2 bytes little-endian."""
    return struct.pack('<h', value)


def deserialize_int16(data: bytes) -> int:
    """Deserialize signed int16 from 2 bytes."""
    return struct.unpack('<h', data[:2])[0]


class MessageBuilder:
    """Helper class for building protocol messages."""
    
    def __init__(self):
        self._data = bytearray()
    
    def add_header(self, command: int, channel_id: int = 0) -> 'MessageBuilder':
        """Add protocol header."""
        self._data.extend(bytes([0x02, 0x01, command, channel_id & 0xFF]))
        return self
    
    def add_length(self, length: int) -> 'MessageBuilder':
        """Add length field."""
        self._data.extend(struct.pack('<H', length))
        return self
    
    def add_bytes(self, data: bytes) -> 'MessageBuilder':
        """Add raw bytes."""
        self._data.extend(data)
        return self
    
    def add_bool(self, value: bool) -> 'MessageBuilder':
        """Add boolean value."""
        self._data.append(1 if value else 0)
        return self
    
    def add_int8(self, value: int) -> 'MessageBuilder':
        """Add signed int8 value."""
        self._data.extend(struct.pack('b', value))
        return self
    
    def add_int16(self, value: int) -> 'MessageBuilder':
        """Add signed int16 value."""
        self._data.extend(struct.pack('<h', value))
        return self
    
    def add_float32(self, value: float) -> 'MessageBuilder':
        """Add float32 value."""
        self._data.extend(struct.pack('<f', value))
        return self
    
    def add_volume_db(self, db: float) -> 'MessageBuilder':
        """Add volume value in dB."""
        raw = VolumeMessage.encode_db_to_raw(db)
        self._data.extend(struct.pack('<H', raw))
        return self
    
    def add_gain_db(self, db: float) -> 'MessageBuilder':
        """Add gain value in dB."""
        raw = GainMessage.encode_db_to_raw(db)
        self._data.extend(struct.pack('B', raw))
        return self
    
    def add_pan_lr(self, left_to_right: float) -> 'MessageBuilder':
        """Add pan value."""
        raw = PanMessage.encode_left_right_to_raw(left_to_right)
        self._data.extend(struct.pack('B', raw))
        return self
    
    def build(self) -> bytes:
        """Build complete message."""
        return bytes(self._data)
    
    def __bytes__(self) -> bytes:
        return self.build()
    
    def __repr__(self) -> str:
        return f"MessageBuilder(len={len(self._data)})"


class ProtocolDiscovery:
    """Helper class for protocol discovery."""

    @staticmethod
    def analyze_response(raw_bytes: bytes) -> dict:
        """
        Analyze a raw USB response to extract protocol information.

        Args:
            raw_bytes: Raw USB response bytes

        Returns:
            Dictionary with protocol analysis results
        """
        result = {
            "raw": raw_bytes.hex(),
            "length": len(raw_bytes),
            "header": raw_bytes[:2].hex() if len(raw_bytes) >= 2 else None,
            "command": format(raw_bytes[2], "02x") if len(raw_bytes) >= 3 else None,
            "cmd_byte": raw_bytes[2:4].hex() if len(raw_bytes) >= 4 else None,
            "data": raw_bytes[2:-2].hex() if len(raw_bytes) > 4 else None,
            "checksum_valid": False,
        }

        if len(raw_bytes) >= 4:
            data = raw_bytes[2:-2]
            if len(raw_bytes) >= 4:
                expected_checksum = CRC8.calculate(data)
                actual_checksum = (raw_bytes[-2] << 8) | raw_bytes[-1]
                result["checksum_valid"] = expected_checksum == actual_checksum

        return result


def encode_control_message(command: CommandType, channel: int, payload: bytes = b"") -> bytes:
    """
    Encode a control message for USB transmission.

    Args:
        command: Command type code
        channel: Channel number (0-indexed)
        payload: Optional data payload

    Returns:
        Encoded USB message bytes
    """
    # Header: 2 bytes
    header = bytes([0x01, 0x00])
    
    # Command byte
    cmd_byte = bytes([command])
    
    # Channel byte
    channel_byte = bytes([channel])
    
    # Combine command, channel, and payload
    data = header + cmd_byte + channel_byte + payload
    
    # Calculate CRC (last 2 bytes)
    crc = calculate_crc(data)
    
    # Full message: data + CRC
    message = data + crc
    return message


def decode_control_message(raw_response: bytes) -> dict:
    """
    Decode a USB response message.

    Args:
        raw_response: Raw USB response bytes

    Returns:
        Dictionary with decoded message components
    """
    result = {
        "header": None,
        "command": None,
        "command_type": None,
        "channel": None,
        "payload": None,
        "crc_valid": False,
    }

    if len(raw_response) < 6:
        return result

    result["header"] = raw_response[:2]
    try:
        command_type = CommandType(raw_response[2])
    except ValueError:
        command_type = None
    result["command"] = command_type
    result["command_type"] = command_type
    result["channel"] = raw_response[3]
    
    # Payload is everything between channel byte and CRC (last 2 bytes)
    payload_start = 4
    payload_end = -2
    if payload_end > payload_start:
        result["payload"] = raw_response[payload_start:payload_end]
    
    # Verify CRC
    data = raw_response[:-2]
    received_crc = raw_response[-2:]
    expected_crc = calculate_crc(data)
    result["crc_valid"] = (received_crc == expected_crc)

    return result


# Additional message classes needed by device.py
class MuteMessage:
    """Mute status message."""
    def __init__(self, muted: bool):
        self.muted = 1 if muted else 0
    
    def encode(self) -> bytes:
        return bytes([self.muted])


class SoloMessage:
    """Solo status message."""
    def __init__(self, soloed: bool):
        self.soloed = 1 if soloed else 0
    
    def encode(self) -> bytes:
        return bytes([self.soloed])


class PhaseMessage:
    """Phase inversion message."""
    def __init__(self, inverted: bool):
        self.inverted = 1 if inverted else 0
    
    def encode(self) -> bytes:
        return bytes([self.inverted])


class SourceMessage:
    """Headphones/source selection message."""
    def __init__(self, source: int):
        self.source = source & 0xFF
    
    def encode(self) -> bytes:
        return bytes([self.source])


class BlendMessage:
    """Monitor blend message."""
    def __init__(self, blend: int):
        self.blend = blend & 0xFF
    
    def encode(self) -> bytes:
        return bytes([self.blend])


class PresetMessage:
    """Preset selection message."""
    def __init__(self, preset_id: int):
        self.preset_id = preset_id & 0xFF
    
    def encode(self) -> bytes:
        return bytes([self.preset_id, 0x00, 0x00, 0xFF])


class RoutingMessage:
    """Routing configuration message."""
    def __init__(self, output: int, bypass: bool, mono: bool):
        self.output = output & 0xFF
        self.bypass = 1 if bypass else 0
        self.mono = 1 if mono else 0
    
    def encode(self) -> bytes:
        return bytes([
            self.output, self.bypass, self.mono, 0xFF, 0xFF, 0x00
        ])


class AuxSendMessage:
    """Aux send level message."""
    def __init__(self, aux_id: int, level: int):
        self.aux_id = aux_id & 0xFF
        self.level = level & 0xFF
    
    def encode(self) -> bytes:
        return bytes([self.aux_id, self.level])


class ReverbSendMessage:
    """Reverb send level message."""
    def __init__(self, level: int):
        self.level = level & 0xFF
    
    def encode(self) -> bytes:
        return bytes([self.level])


def encode_channel_mute_command(channel_id: int, muted: bool) -> bytes:
    """Build a mute command using the current verified-ready framing path."""
    return create_channel_command(channel_id, 0x25, MuteMessage(muted).encode())


def encode_channel_solo_command(channel_id: int, soloed: bool) -> bytes:
    """Build a solo command using the current verified-ready framing path."""
    return create_channel_command(channel_id, 0x26, SoloMessage(soloed).encode())


def encode_channel_phase_command(channel_id: int, inverted: bool) -> bytes:
    """Build a phase command using the current verified-ready framing path."""
    return create_channel_command(channel_id, 0x27, PhaseMessage(inverted).encode())


def encode_headphones_source_command(channel_id: int, source_id: int) -> bytes:
    """Build a headphones source command using the current verified-ready framing path."""
    return create_channel_command(channel_id, 0x61, SourceMessage(source_id).encode())


def encode_channel_preset_command(channel_id: int, preset_id: int) -> bytes:
    """Build a preset command using the current verified-ready framing path."""
    return create_channel_command(channel_id, 0x31, PresetMessage(preset_id).encode())
