"""USB transport helpers for Presonus devices.

This module isolates raw PyUSB lifecycle and IO behavior from higher-level
device semantics.
"""

from __future__ import annotations

from typing import Any, Optional

import usb.core
import usb.util


class USBTransport:
    """Thin wrapper around PyUSB device lifecycle and IO."""

    def __init__(self, usb_interface: int, usb_endpoint: int):
        self.usb_interface = usb_interface
        self.usb_endpoint = usb_endpoint
        self.device: Optional[Any] = None
        self.handle: Optional[Any] = None
        self.initialized = False

    def attach(self, device: Any) -> None:
        """Attach and configure a USB device."""
        self.device = device
        if hasattr(device, "is_kernel_driver_active") and device.is_kernel_driver_active(self.usb_interface):
            if hasattr(device, "detach_kernel_driver"):
                device.detach_kernel_driver(self.usb_interface)
        if hasattr(device, "set_configuration"):
            try:
                device.set_configuration()
            except usb.core.USBError as exc:
                if getattr(exc, "errno", None) != 16:
                    raise
        try:
            usb.util.claim_interface(device, self.usb_interface)
        except (usb.core.USBError, AttributeError):
            pass
        if hasattr(device, "set_interface_altsetting"):
            try:
                device.set_interface_altsetting(interface=self.usb_interface, alternate_setting=1)
            except Exception:
                pass
        self.handle = device
        self.initialized = True

    def close(self) -> None:
        """Release the attached USB device."""
        if self.handle is not None:
            try:
                usb.util.release_interface(self.handle, self.usb_interface)
            except Exception:
                pass
            try:
                usb.util.dispose_resources(self.handle)
            except Exception:
                pass
        self.handle = None
        self.device = None
        self.initialized = False

    def ensure_ready(self) -> None:
        if not self.initialized:
            raise RuntimeError("Device not initialized")
        if self.handle is None:
            raise RuntimeError("USB handle not initialized")

    def write(self, data: bytes) -> int:
        self.ensure_ready()
        handle = self.handle
        assert handle is not None
        try:
            return int(handle.write(data))
        except TypeError:
            return int(handle.write(self.usb_endpoint, data))

    def read(self, timeout: int = 1000, size: int = 64) -> bytes:
        self.ensure_ready()
        handle = self.handle
        assert handle is not None
        try:
            response = handle.read(timeout)
        except TypeError:
            response = handle.read(self.usb_endpoint, size, timeout)
        return bytes(response)
