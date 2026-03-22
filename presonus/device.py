"""Public device API for Presonus IO24 control."""

from __future__ import annotations

from typing import Any, Iterable, List, Optional

import usb.core

from .backends import AutoBackend, MockBackend, ProtocolBackend
from .capabilities import AUTO_CAPABILITIES, MOCK_CAPABILITIES, PROTOCOL_CAPABILITIES, CapabilitySet
from .usb_transport import USBTransport


class PresonusUSBError(Exception):
    """Error communicating with the USB device."""


class PresonusDevice:
    """High-level Presonus device API.

    The default backend is currently mock-compatible while the real hardware
    protocol is still being verified from packet captures.
    """

    VENDOR_ID = 0x194F
    PRODUCT_ID = 0x0422
    MAX_CHANNELS = 24
    USB_INTERFACE = 5
    USB_ENDPOINT = 0x01

    def __init__(self, device_index: int = 0, mode: str = "mock"):
        self._device_index = device_index
        self._device_info = None
        self._last_state = None
        self._transport = USBTransport(self.USB_INTERFACE, self.USB_ENDPOINT)
        self._mode = mode
        self._backend = self._build_backend(mode)

    def _build_backend(self, mode: str):
        if mode == "protocol":
            return ProtocolBackend(self)
        if mode == "auto":
            return AutoBackend(self)
        return MockBackend(self)

    @property
    def mode(self) -> str:
        return self._backend.mode

    def capabilities(self) -> CapabilitySet:
        if self.mode == "protocol":
            return PROTOCOL_CAPABILITIES
        if self.mode == "auto":
            return AUTO_CAPABILITIES
        return MOCK_CAPABILITIES

    @property
    def _device(self) -> Optional[Any]:
        return self._transport.device

    @_device.setter
    def _device(self, value: Optional[Any]) -> None:
        self._transport.device = value

    @property
    def _handle(self) -> Optional[Any]:
        return self._transport.handle

    @_handle.setter
    def _handle(self, value: Optional[Any]) -> None:
        self._transport.handle = value

    @property
    def _initialized(self) -> bool:
        return self._transport.initialized

    @_initialized.setter
    def _initialized(self, value: bool) -> None:
        self._transport.initialized = value

    @property
    def device(self) -> Optional[Any]:
        return self._device

    @classmethod
    def find_devices(cls) -> List[Any]:
        """Return Presonus devices discovered by PyUSB."""
        found = usb.core.find(find_all=True)
        if found is None:
            return []
        devices = list(found) if isinstance(found, Iterable) else [found]
        return [
            dev
            for dev in devices
            if getattr(dev, "idVendor", None) == cls.VENDOR_ID
            and getattr(dev, "idProduct", None) == cls.PRODUCT_ID
        ]

    def __enter__(self) -> "PresonusDevice":
        self.open(index=self._device_index)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def open(self, device_index: Optional[int] = None, *, index: Optional[int] = None) -> bool:
        """Open device connection."""
        target_index = self._device_index if device_index is None and index is None else (
            index if index is not None else device_index
        )
        assert target_index is not None

        devices = self.find_devices()
        if not devices or target_index < 0 or target_index >= len(devices):
            raise PresonusUSBError(f"No device found at index {target_index}")

        try:
            self._transport.attach(devices[target_index])
        except usb.core.USBError as exc:
            raise PresonusUSBError(f"USB error: {exc}") from exc

        self._device_index = target_index
        return True

    def close(self) -> None:
        """Close device connection."""
        self._transport.close()

    def _ensure_ready(self) -> None:
        try:
            self._transport.ensure_ready()
        except RuntimeError as exc:
            raise PresonusUSBError(str(exc)) from exc

    def _write_data(self, data: bytes) -> int:
        try:
            return self._transport.write(data)
        except Exception as exc:
            raise PresonusUSBError(f"USB write error: {exc}") from exc

    def _read_data(self, timeout: int = 1000) -> bytes:
        try:
            return self._transport.read(timeout)
        except Exception as exc:
            raise PresonusUSBError(f"USB read error: {exc}") from exc

    def get_descriptor(self, descriptor_type: int, index: int = 0, length: int = 64) -> bytes:
        """Read a USB descriptor when available.

        This is mainly exposed to support discovery/debug tooling.
        """
        self._ensure_ready()
        handle = self._handle
        assert handle is not None
        if hasattr(handle, "ctrl_transfer"):
            try:
                data = handle.ctrl_transfer(0x80, 0x06, (descriptor_type << 8) | index, 0, length)
                return bytes(data)
            except Exception as exc:
                raise PresonusUSBError(f"USB descriptor read error: {exc}") from exc
        return b""

    def query_state(self):
        return self._backend.query_state()

    def get_device_info(self):
        return self._backend.get_device_info()

    def set_channel_gain(self, channel_id: int, gain: float) -> bool:
        return self._backend.set_channel_gain(channel_id, gain)

    def set_channel_volume(self, channel_id: int, volume: float) -> bool:
        return self._backend.set_channel_volume(channel_id, volume)

    def set_channel_pan(self, channel_id: int, pan: int) -> bool:
        return self._backend.set_channel_pan(channel_id, pan)

    def set_channel_mute(self, channel_id: int, muted: bool) -> bool:
        return self._backend.set_channel_mute(channel_id, muted)

    def set_channel_solo(self, channel_id: int, solo: bool) -> bool:
        return self._backend.set_channel_solo(channel_id, solo)

    def set_channel_phase(self, channel_id: int, phase_inv: bool) -> bool:
        return self._backend.set_channel_phase(channel_id, phase_inv)

    def set_channel_input_source(self, channel_id: int, source: str) -> bool:
        return self._backend.set_channel_input_source(channel_id, source)

    def set_headphones_source(self, *args: Any) -> bool:
        return self._backend.set_headphones_source(*args)

    def set_master_volume(self, volume: float) -> bool:
        return self._backend.set_master_volume(volume)

    def set_monitor_blend(self, blend: int) -> bool:
        return self._backend.set_monitor_blend(blend)

    def set_headphones_volume(self, volume: float) -> bool:
        return self._backend.set_headphones_volume(volume)

    def set_compressor(self, channel_id: int, settings: Any) -> bool:
        return self._backend.set_compressor(channel_id, settings)

    def set_gate(self, channel_id: int, settings: Any) -> bool:
        return self._backend.set_gate(channel_id, settings)

    def set_eq(self, channel_id: int, eq: Any) -> bool:
        return self._backend.set_eq(channel_id, eq)

    def set_limiter(self, channel_id: int, limiter: Any) -> bool:
        return self._backend.set_limiter(channel_id, limiter)

    def set_channel_preset(self, channel_id: int, preset: Any) -> bool:
        return self._backend.set_channel_preset(channel_id, preset)

    def set_routing(self, channel_id: int, output: Any, volume: int, routed: bool, solo: bool) -> bool:
        return self._backend.set_routing(channel_id, output, volume, routed, solo)

    def set_aux_send_level(self, channel_id: int, aux_id: int, level: int) -> bool:
        return self._backend.set_aux_send_level(channel_id, aux_id, level)

    def set_reverb_send_level(self, channel_id: int, level: int) -> bool:
        return self._backend.set_reverb_send_level(channel_id, level)
