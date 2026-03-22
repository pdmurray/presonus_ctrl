"""Tests for capture session helper scaffolding."""

from tools.new_capture_session import slugify


def test_capture_helper_slugify():
    assert slugify("startup mute solo") == "startup-mute-solo"
    assert slugify("  Channel 1  Preset ") == "channel-1-preset"
