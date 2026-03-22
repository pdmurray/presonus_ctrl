"""Hybrid backend that prefers protocol-backed features when available."""

from __future__ import annotations

from typing import Any, Callable, Dict

from .mock_backend import MockBackend
from .protocol_backend import ProtocolBackend


class AutoBackend:
    """Use protocol-backed commands where implemented, else fall back to mock."""

    mode = "auto"

    def __init__(self, device: Any):
        self.device = device
        self.protocol = ProtocolBackend(device)
        self.mock = MockBackend(device)
        self._protocol_methods = {
            "set_channel_mute",
            "set_channel_solo",
            "set_channel_phase",
            "set_channel_preset",
            "set_headphones_source",
        }

    def _pick(self, name: str) -> Callable[..., Any]:
        if name in self._protocol_methods:
            return getattr(self.protocol, name)
        return getattr(self.mock, name)

    def __getattr__(self, name: str):
        return self._pick(name)

    def backend_for(self, name: str) -> str:
        return "protocol" if name in self._protocol_methods else "mock"

    def feature_map(self) -> Dict[str, str]:
        return {name: self.backend_for(name) for name in self._protocol_methods}
