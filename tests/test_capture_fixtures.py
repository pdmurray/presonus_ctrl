"""Smoke tests for future capture fixture scaffolding."""

import json
from pathlib import Path


def test_packet_fixture_template_is_valid_json():
    path = Path("captures/fixtures/packet_fixture_template.json")
    data = json.loads(path.read_text())
    assert data["status"] in {"verified", "likely", "speculative"}
    assert "request_hex" in data
    assert "decoded" in data
