
"""Presonus Revelator IO24 control library."""

from .device import PresonusDevice, PresonusUSBError
from .models import (
    DeviceInfo,
    FatChannelSettings,
    ChannelSettings,
    MasterSettings,
    IO24State,
    PresetType,
)
from .capabilities import CapabilitySet
from .protocol import ProtocolDiscovery

__all__ = [
    "PresonusDevice",
    "PresonusUSBError",
    "DeviceInfo",
    "FatChannelSettings",
    "ChannelSettings",
    "MasterSettings",
    "IO24State",
    "PresetType",
    "CapabilitySet",
    "ProtocolDiscovery",
]

__version__ = "0.1.0"
