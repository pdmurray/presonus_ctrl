"""Mock-compatible backend for Presonus device control."""

from __future__ import annotations

from typing import Any, Optional

from ..models import (
    ChannelState,
    CompressorSettings,
    DeviceInfo,
    EqSettings,
    GateSettings,
    HeadphonesSource,
    IO24State,
    LimiterSettings,
    MasterState,
    OutputValue,
    PresetType,
)
from ..protocol import (
    AuxSendMessage,
    BlendMessage,
    MuteMessage,
    PhaseMessage,
    PresetMessage,
    ReverbSendMessage,
    RoutingMessage,
    SoloMessage,
    SourceMessage,
    create_channel_command,
)


class MockBackend:
    """Current mock-friendly control backend."""

    mode = "mock"

    def __init__(self, device: Any):
        self.device = device

    def _send_command(self, command: int, channel_id: int, payload: bytes = b"") -> bool:
        self.device._write_data(create_channel_command(channel_id, command, payload))
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

    def query_state(self) -> IO24State:
        self.device._ensure_ready()
        state = IO24State()
        for channel_id in range(1, self.device.MAX_CHANNELS + 1):
            try:
                data = self.device._read_data()
                state.channels[channel_id] = ChannelState.from_binary(data, channel_id)
            except Exception:
                state.channels[channel_id] = ChannelState(channel_id=channel_id)
        try:
            state.master = MasterState.from_binary(self.device._read_data())
        except Exception:
            state.master = MasterState()
        state.device_info = self.device._device_info
        self.device._last_state = state
        return state

    def get_device_info(self) -> DeviceInfo:
        self.device._ensure_ready()
        if self.device._device_info is None:
            usb_device = self.device._device
            self.device._device_info = DeviceInfo(
                vendor_id=f"{getattr(usb_device, 'idVendor', self.device.VENDOR_ID):04x}",
                product_id=f"{getattr(usb_device, 'idProduct', self.device.PRODUCT_ID):04x}",
                product_name=getattr(usb_device, 'product', None) or "Revelator IO 24",
                serial_number=getattr(usb_device, 'serial_number', None),
                firmware_version=None,
            )
        return self.device._device_info

    def set_channel_gain(self, channel_id: int, gain: float) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS or not -60.0 <= gain <= 12.0:
            return False
        return self._send_command(0x22, channel_id, bytes([int(round(gain + 60)) & 0x7F]))

    def set_channel_volume(self, channel_id: int, volume: float) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS or not -60.0 <= volume <= 0.0:
            return False
        raw = int(round((volume + 60.0) * 4)) & 0xFF
        return self._send_command(0x20, channel_id, bytes([raw]))

    def set_channel_pan(self, channel_id: int, pan: int) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS or not -100 <= pan <= 100:
            return False
        return self._send_command(0x24, channel_id, bytes([(pan + 100) & 0xFF]))

    def set_channel_mute(self, channel_id: int, muted: bool) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS:
            return False
        return self._send_command(0x25, channel_id, MuteMessage(muted).encode())

    def set_channel_solo(self, channel_id: int, solo: bool) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS:
            return False
        return self._send_command(0x26, channel_id, SoloMessage(solo).encode())

    def set_channel_phase(self, channel_id: int, phase_inv: bool) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS:
            return False
        return self._send_command(0x27, channel_id, PhaseMessage(phase_inv).encode())

    def set_channel_input_source(self, channel_id: int, source: str) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS or source not in ("mic", "line"):
            return False
        return self._send_command(0x28, channel_id, bytes([0 if source == "mic" else 1]))

    def set_headphones_source(self, *args: Any) -> bool:
        self.device._ensure_ready()
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
        return self._send_command(0x61, int(channel_id), SourceMessage(source_id).encode())

    def set_master_volume(self, volume: float) -> bool:
        self.device._ensure_ready()
        if not -60.0 <= volume <= 1.0:
            return False
        raw = int(round((min(volume, 0.0) + 60.0) * 4)) & 0xFF
        return self._send_command(0x60, 0, bytes([raw]))

    def set_monitor_blend(self, blend: int) -> bool:
        self.device._ensure_ready()
        if not -100 <= blend <= 100:
            return False
        return self._send_command(0x63, 0, BlendMessage(blend + 100).encode())

    def set_headphones_volume(self, volume: float) -> bool:
        self.device._ensure_ready()
        if not -60.0 <= volume <= 1.0:
            return False
        raw = int(round((min(volume, 0.0) + 60.0) * 4)) & 0xFF
        return self._send_command(0x62, 0, bytes([raw]))

    def set_compressor(self, channel_id: int, settings: CompressorSettings) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS:
            return False
        if settings.enabled and not (-80.0 <= settings.threshold < 0.0):
            return False
        return self._send_command(0x40, channel_id, bytes([1 if settings.enabled else 0, int(settings.ratio) & 0xFF]))

    def set_gate(self, channel_id: int, settings: GateSettings) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS:
            return False
        if settings.enabled and not (-80.0 <= settings.threshold <= -1.0):
            return False
        return self._send_command(0x41, channel_id, bytes([1 if settings.enabled else 0, int(settings.ratio) & 0xFF]))

    def set_eq(self, channel_id: int, eq: EqSettings) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS:
            return False
        return self._send_command(0x42, channel_id, bytes([len(eq.bands) & 0xFF]))

    def set_limiter(self, channel_id: int, limiter: LimiterSettings) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS:
            return False
        if limiter.enabled and not (-12.0 <= limiter.threshold <= -3.0):
            return False
        return self._send_command(0x43, channel_id, bytes([1 if limiter.enabled else 0]))

    def set_channel_preset(self, channel_id: int, preset: PresetType) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS:
            return False
        return self._send_command(0x31, channel_id, PresetMessage(self._preset_id(preset)).encode())

    def set_routing(self, channel_id: int, output: Any, volume: int, routed: bool, solo: bool) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS or not 0 <= volume <= 100:
            return False
        if isinstance(output, OutputValue):
            output_id = 0 if output == OutputValue.MAIN_L_R else 1
        elif isinstance(output, int):
            output_id = output & 0xFF
        else:
            return False
        return self._send_command(0x52, channel_id, RoutingMessage(output_id, routed, solo).encode())

    def set_aux_send_level(self, channel_id: int, aux_id: int, level: int) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS or aux_id not in (1, 2) or not 0 <= level <= 100:
            return False
        return self._send_command(0x70, channel_id, AuxSendMessage(aux_id, level).encode())

    def set_reverb_send_level(self, channel_id: int, level: int) -> bool:
        self.device._ensure_ready()
        if not 1 <= channel_id <= self.device.MAX_CHANNELS or not 0 <= level <= 100:
            return False
        return self._send_command(0x80, channel_id, ReverbSendMessage(level).encode())
