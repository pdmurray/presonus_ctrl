"""Tests for backend mode and capability reporting."""

from presonus.device import PresonusDevice


def test_mock_capabilities_report_mode():
    device = PresonusDevice(mode="mock")
    caps = device.capabilities()
    assert caps.mode == "mock"
    assert caps.status("channel_volume") == "mock_supported"


def test_protocol_capabilities_report_verified_ready_features():
    device = PresonusDevice(mode="protocol")
    caps = device.capabilities()
    assert caps.mode == "protocol"
    assert caps.status("channel_mute") == "verified_ready"
    assert caps.status("channel_volume") == "unknown"


def test_auto_capabilities_and_mode():
    device = PresonusDevice(mode="auto")
    caps = device.capabilities()
    assert device.mode == "auto"
    assert caps.mode == "auto"
    assert caps.status("channel_mute") == "verified_ready"
    assert caps.status("channel_volume") == "mock_supported"
