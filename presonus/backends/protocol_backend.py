"""Capture-backed protocol backend skeleton.

This backend is the future home for packet-capture-verified command encoding.
It currently implements only a small set of simple setter paths so the project
can start migrating from the mock backend without claiming full protocol
coverage.
"""

from __future__ import annotations

from typing import Any, Optional

from ..models import HeadphonesSource, PresetType
from ..protocol import (
    encode_channel_mute_command,
    encode_channel_phase_command,
    encode_channel_preset_command,
    encode_channel_solo_command,
    encode_headphones_source_command,
)


class ProtocolBackend:
    """Partial backend for capture-verified-ready command families."""

    mode = "protocol"

    def __init__(self, device: Any):
        self.device = device

    def _unsupported(self, name: str):
        raise NotImplementedError(
            f"Protocol backend method '{name}' is not implemented yet. "
            "Use the mock backend until packet captures verify this command family."
        )

    def _write(self, data: bytes) -> bool:
        self.device._ensure_ready()
        self.device._write_data(data)
        return True

    @staticmethod
    def _preset_id(preset: PresetType) -> int:
        preset_map = {
            PresetType.VOCAL: 0x01,
            PresetType.GUITAR: 0x02,
            PresetType.BASS: 0x03,
            PresetType.KEYBOARD: 0x04,
            PresetType.DRUMS: 0x05,
            PresetType.CUSTOM: 0xFF,
            PresetType.SNARE: 0x05,
            PresetType.DRUM_MIC: 0x05,
        }
        return preset_map[preset]

    @staticmethod
    def _source_id(source: Any) -> Optional[int]:
        if isinstance(source, HeadphonesSource):
            source = source.value
        if isinstance(source, str):
            mapping = {"line": 0, "main": 0, "monitor": 1, "mix_a": 1, "hotkey": 2, "mix_b": 2}
            return mapping.get(source.lower())
        if isinstance(source, int) and source in (0, 1, 2):
            return source
        return None

    def set_channel_mute(self, channel_id: int, muted: bool) -> bool:
        if not 1 <= channel_id <= self.device.MAX_CHANNELS:
            return False
        return self._write(encode_channel_mute_command(channel_id, muted))

    def set_channel_solo(self, channel_id: int, solo: bool) -> bool:
        if not 1 <= channel_id <= self.device.MAX_CHANNELS:
            return False
        return self._write(encode_channel_solo_command(channel_id, solo))

    def set_channel_phase(self, channel_id: int, phase_inv: bool) -> bool:
        if not 1 <= channel_id <= self.device.MAX_CHANNELS:
            return False
        return self._write(encode_channel_phase_command(channel_id, phase_inv))

    def set_channel_preset(self, channel_id: int, preset: PresetType) -> bool:
        if not 1 <= channel_id <= self.device.MAX_CHANNELS:
            return False
        return self._write(encode_channel_preset_command(channel_id, self._preset_id(preset)))

    def set_headphones_source(self, *args: Any) -> bool:
        if len(args) == 1:
            channel_id = 0
            source = args[0]
        elif len(args) == 2:
            channel_id, source = args
        else:
            return False
        if channel_id not in (0, 1, 2, 3, 4):
            return False
        source_id = self._source_id(source)
        if source_id is None:
            return False
        return self._write(encode_headphones_source_command(int(channel_id), source_id))

    def query_state(self):
        self._unsupported("query_state")

    def get_device_info(self):
        self._unsupported("get_device_info")

    def set_channel_gain(self, channel_id: int, gain: float) -> bool:
        self._unsupported("set_channel_gain")

    def set_channel_volume(self, channel_id: int, volume: float) -> bool:
        self._unsupported("set_channel_volume")

    def set_channel_pan(self, channel_id: int, pan: int) -> bool:
        self._unsupported("set_channel_pan")

    def set_channel_input_source(self, channel_id: int, source: str) -> bool:
        self._unsupported("set_channel_input_source")

    def set_master_volume(self, volume: float) -> bool:
        self._unsupported("set_master_volume")

    def set_monitor_blend(self, blend: int) -> bool:
        self._unsupported("set_monitor_blend")

    def set_headphones_volume(self, volume: float) -> bool:
        self._unsupported("set_headphones_volume")

    def set_compressor(self, channel_id: int, settings: Any) -> bool:
        self._unsupported("set_compressor")

    def set_gate(self, channel_id: int, settings: Any) -> bool:
        self._unsupported("set_gate")

    def set_eq(self, channel_id: int, eq: Any) -> bool:
        self._unsupported("set_eq")

    def set_limiter(self, channel_id: int, limiter: Any) -> bool:
        self._unsupported("set_limiter")

    def set_routing(self, channel_id: int, output: Any, volume: int, routed: bool, solo: bool) -> bool:
        self._unsupported("set_routing")

    def set_aux_send_level(self, channel_id: int, aux_id: int, level: int) -> bool:
        self._unsupported("set_aux_send_level")

    def set_reverb_send_level(self, channel_id: int, level: int) -> bool:
        self._unsupported("set_reverb_send_level")
