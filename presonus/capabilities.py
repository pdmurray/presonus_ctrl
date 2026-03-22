"""Capability reporting for Presonus device backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class CapabilitySet:
    """Describes which command families are available in a backend."""

    mode: str
    features: Dict[str, str]

    def status(self, feature: str) -> str:
        return self.features.get(feature, "unknown")

    def to_dict(self) -> Dict[str, object]:
        return {"mode": self.mode, "features": dict(self.features)}


MOCK_CAPABILITIES = CapabilitySet(
    mode="mock",
    features={
        "device_info": "mock_supported",
        "query_state": "mock_supported",
        "channel_gain": "mock_supported",
        "channel_volume": "mock_supported",
        "channel_pan": "mock_supported",
        "channel_mute": "mock_supported",
        "channel_solo": "mock_supported",
        "channel_phase": "mock_supported",
        "channel_input_source": "mock_supported",
        "headphones_source": "mock_supported",
        "master_volume": "mock_supported",
        "headphones_volume": "mock_supported",
        "monitor_blend": "mock_supported",
        "compressor": "mock_supported",
        "gate": "mock_supported",
        "eq": "mock_supported",
        "limiter": "mock_supported",
        "channel_preset": "mock_supported",
        "routing": "mock_supported",
        "aux_send": "mock_supported",
        "reverb_send": "mock_supported",
    },
)


PROTOCOL_CAPABILITIES = CapabilitySet(
    mode="protocol",
    features={
        "channel_mute": "verified_ready",
        "channel_solo": "verified_ready",
        "channel_phase": "verified_ready",
        "headphones_source": "verified_ready",
        "channel_preset": "verified_ready",
    },
)


AUTO_CAPABILITIES = CapabilitySet(
    mode="auto",
    features={
        **MOCK_CAPABILITIES.features,
        **PROTOCOL_CAPABILITIES.features,
    },
)
