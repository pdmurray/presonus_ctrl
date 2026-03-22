# Presonus IO24 Python Control Library

A Python library for controlling the Presonus Revelator IO24 audio interface via USB.

## Status

This project currently has two layers of functionality:

- A stable mock-compatible API layer used by the current tests and CLI
- A provisional protocol layer that still needs real Windows USB packet capture before it should be treated as hardware-verified

That means the library API is usable for development and test-driven iteration today, but the underlying USB protocol implementation is still being reverse-engineered.

## Quick Start

For a local development checkout:

```bash
git clone <repo-url>
cd presonus_ctrl
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
presonus-io24 info
```

If Linux USB permissions are not set up yet:

```bash
./setup.sh
./setup.sh --test
```

## Current Implementation Status

### Implemented Now

- Device discovery and connection lifecycle
- Mock-compatible channel, master, routing, aux, and preset control methods
- State and model serialization helpers
- Protocol helper utilities used by the test suite
- CLI scaffolding for device interaction and protocol discovery workflows

### Capture-Verified

- No command families should be considered fully capture-verified yet

### Planned / Speculative

- Real packet-accurate command encoders
- Real response parsing for full device state
- Accurate routing, DSP, and state synchronization behavior based on captured traffic

## Overview

The library is intended to provide a high-level API for:

- Channel volume, pan, mute, solo, phase, and gain
- Fat channel DSP controls such as compressor, gate, EQ, and limiter
- Routing, aux sends, reverb sends, and headphones source selection
- Master volume and monitor blend controls
- Device info and state queries

Today, those APIs are best understood as a stable compatibility surface while the real USB protocol is still being mapped.

## Requirements

- Python 3.8+
- `pyusb`
- Presonus IO24 connected via USB for real-device work

## Setup

### Fresh Development Setup

Use this if you want to work on the codebase itself.

```bash
git clone <repo-url>
cd presonus_ctrl
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

Optional development dependencies:

```bash
python -m pip install -e .[dev]
```

What editable install does:

- installs the `presonus-io24` console command
- makes `import presonus` available in the virtual environment
- keeps the installed package linked to your working tree, so normal `.py` changes are picked up immediately

When to rerun `python -m pip install -e .`:

- after changing `pyproject.toml`
- after changing console entry points or dependencies
- usually not needed for ordinary Python code edits

### Fresh User Installation

Use this if you mainly want the CLI/library, not active development.

```bash
git clone <repo-url>
cd presonus_ctrl
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install .
```

After that, the CLI should be available in the active environment:

```bash
presonus-io24 --help
```

### Run From Anywhere With pipx

If you mainly want the CLI, `pipx` is the most convenient option. It installs
the command into an isolated environment and makes it available globally,
without needing to manually activate a project virtualenv every time.

Install `pipx` first if needed:

```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

Then install this project from a local checkout:

```bash
cd presonus_ctrl
pipx install .
```

Or, during development, install from the checkout with a distinct command name:

```bash
cd presonus_ctrl
pipx install --suffix=-local .
```

That gives you a command like:

```bash
presonus-io24-local info
```

When the package is eventually published, the intended user flow will be:

```bash
pipx install presonus-io24
presonus-io24 info
```

### Arch / CachyOS Setup

For Arch-based systems, a practical user-oriented setup is:

```bash
sudo pacman -S python python-pipx python-pyusb wireshark-qt wireshark-cli usbutils
pipx ensurepath
```

Then install the CLI from a local checkout:

```bash
cd presonus_ctrl
pipx install .
```

Or, for local development while keeping the command name distinct:

```bash
cd presonus_ctrl
pipx install --suffix=-local .
```

That gives you a command such as:

```bash
presonus-io24-local info
```

For Linux USB capture support on Arch/CachyOS, also make sure `usbmon` is available:

```bash
sudo modprobe usbmon
sudo tshark -D | grep usbmon
```

Since the Revelator was observed on USB bus `009`, a typical capture command is:

```bash
sudo tshark -i usbmon9 -w /tmp/revelator-linux.pcapng
```

### Linux Permissions / udev

On Linux, the device may be visible but not openable until udev permissions are configured.

The easiest path is:

```bash
./setup.sh
./setup.sh --test
```

If you want to install the rule manually instead:

```bash
sudo cp ./udev/99-presonus-io24.rules /etc/udev/rules.d/99-presonus-io24.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --attr-match=idVendor=194f --attr-match=idProduct=0422
```

Then unplug/replug the device and verify access:

```bash
./setup.sh --test
presonus-io24 info
```

### Future Packaging

This project is now in decent shape for a future user-facing package install flow.

Likely future targets:

- PyPI package for `pipx install presonus-io24`
- AUR package for Arch-based systems

An eventual AUR package would be a good fit once the protocol support and user workflow settle down further.

Packaging metadata is now mostly in place for that path (`LICENSE`, classifiers,
keywords, console entry point). The main remaining publishing task is to add
real project URLs once the canonical repository/homepage location is finalized.

### Install Dependencies Only

If you only want the low-level Python dependency manually:

```bash
pip install pyusb
```

But for normal usage, prefer one of the install flows above so the `presonus-io24` command is created.

On Linux, you may also need a udev rule:

```bash
sudo tee /etc/udev/rules.d/40-presonus.rules << 'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="194f", ATTR{idProduct}=="0422", MODE="0666", TAG+="uaccess"
EOF
sudo udevadm control --reload-rules
sudo udevadm trigger --attr-match=idVendor=194f --attr-match=idProduct=0422
```

Or use the provided helper:

```bash
./setup.sh
./setup.sh --test
```

## Usage

### Basic API Usage

```python
from presonus.device import PresonusDevice

with PresonusDevice() as device:
    info = device.get_device_info()
    print(info.product_name)

    device.set_channel_gain(1, 6.0)
    device.set_channel_volume(1, -10.0)
    device.set_channel_pan(1, 0)
    device.set_channel_mute(1, False)
```

### Backend Modes

`PresonusDevice` currently supports three modes:

- `mock` - default, stable compatibility backend used by the current suite
- `protocol` - partial capture-backed backend for the first simple setter family
- `auto` - prefers protocol-backed commands where implemented and falls back to the mock backend elsewhere

Example:

```python
from presonus.device import PresonusDevice

with PresonusDevice(mode="protocol") as device:
    device.set_channel_mute(1, True)
    device.set_channel_solo(1, False)
    device.set_channel_phase(1, True)
```

At the moment, `protocol` mode is intentionally limited. Unsupported command families raise `NotImplementedError` so they do not silently fall back to speculative behavior.

Use `auto` mode when you want the project to adopt capture-backed command families gradually without losing the broader mock-compatible API surface.

### Querying Mock-Compatible State

```python
from presonus.device import PresonusDevice

with PresonusDevice() as device:
    state = device.query_state()
    print(len(state.channels))
    print(state.master.to_dict() if state.master else None)
```

### Protocol Discovery Workflow

Real protocol verification is still in progress. See:

- `docs/protocol/PROTOCOL_DISCOVERY.md`
- `docs/TEST_RECOVERY_PLAN.md`
- `docs/NEXT_STEPS_PROTOCOL_PLAN.md`

To scaffold a capture session workspace locally:

```bash
presonus-io24 capture-note "startup mute solo"
```

## CLI

The CLI exposes device and protocol-discovery oriented commands.

Examples:

```bash
presonus-io24 info
presonus-io24 list
presonus-io24 discover --test
```

Development fallback:

```bash
python -m cli.main info
```

Some CLI commands are still intentionally placeholder-oriented until protocol capture confirms the true USB behavior.

## Public API

### `PresonusDevice`

Primary high-level device API:

```python
class PresonusDevice:
    def __init__(device_index: int = 0, mode: str = "mock")
    def capabilities() -> CapabilitySet
    def find_devices() -> List[Device]
    def open(index: int = 0) -> bool
    def close() -> None
    def get_device_info() -> DeviceInfo
    def query_state() -> IO24State

    def set_channel_gain(channel_id: int, gain: float) -> bool
    def set_channel_volume(channel_id: int, volume: float) -> bool
    def set_channel_pan(channel_id: int, pan: int) -> bool
    def set_channel_mute(channel_id: int, muted: bool) -> bool
    def set_channel_solo(channel_id: int, solo: bool) -> bool
    def set_channel_phase(channel_id: int, phase_inv: bool) -> bool
    def set_channel_input_source(channel_id: int, source: str) -> bool

    def set_compressor(channel_id: int, settings: CompressorSettings) -> bool
    def set_gate(channel_id: int, settings: GateSettings) -> bool
    def set_eq(channel_id: int, settings: EqSettings) -> bool
    def set_limiter(channel_id: int, settings: LimiterSettings) -> bool
    def set_channel_preset(channel_id: int, preset: PresetType) -> bool

    def set_routing(channel_id: int, output, volume: int, routed: bool, solo: bool) -> bool
    def set_aux_send_level(channel_id: int, aux_id: int, level: int) -> bool
    def set_reverb_send_level(channel_id: int, level: int) -> bool

    def set_master_volume(volume: float) -> bool
    def set_headphones_volume(volume: float) -> bool
    def set_headphones_source(source) -> bool
    def set_monitor_blend(blend: int) -> bool
```

### Models

The model layer provides stable structures for mocked state, API validation, and future parsing work:

```python
from presonus.models import (
    DeviceInfo,
    ChannelSettings,
    MasterSettings,
    IO24State,
    RoutingEntry,
    VolumeValue,
    GainValue,
    PanValue,
    BlendValue,
    PresetType,
    HeadphonesSource,
    OutputValue,
    FrequencyBand,
    CompressorSettings,
    GateSettings,
    EqSettings,
    LimiterSettings,
    FatChannelSettings,
)
```

## Testing Philosophy

The project currently distinguishes between two kinds of behavior:

- Mock-compatible behavior that is stable and test-supported now
- Protocol-accurate behavior that must be proven by real USB captures before being trusted

A passing test suite currently means the compatibility layer is coherent. It does not yet mean every command matches the real hardware protocol.

## Protocol Status

Reverse engineering is still required for the real control protocol.

The intended workflow is:

1. Capture Windows USB traffic while using Universal Control
2. Analyze the capture on Linux
3. Promote verified mappings into the protocol layer
4. Replace provisional encoders one command family at a time

See `docs/protocol/PROTOCOL_DISCOVERY.md` for the capture workflow.

## Contributor Workflow

If you want to help implement the real protocol:

1. Capture USB traffic for a small, well-defined action set
2. Store captures and extracted notes in a dedicated location
3. Record verified field mappings in a protocol mapping document
4. Add packet-based tests for the verified command family
5. Replace the provisional encoder with a capture-backed encoder

The detailed roadmap for this work is in `docs/NEXT_STEPS_PROTOCOL_PLAN.md`.

## Device Notes

Known project constants in the current implementation:

- Vendor ID: `0x194f`
- Product ID: `0x0422`
- Vendor-specific control interface observed on Linux: `5`
- Vendor-specific bulk endpoints observed on Linux: `0x01 OUT`, `0x81 IN`
- Logical channel count used by the compatibility layer: `24`

Other endpoint and packet-format details should be treated as provisional until confirmed by captures.

## Error Handling

```python
from presonus.device import PresonusDevice, PresonusUSBError

try:
    with PresonusDevice() as device:
        device.set_channel_volume(1, -12.0)
except PresonusUSBError as exc:
    print(f"Device error: {exc}")
```

## Related Docs

- `docs/TEST_RECOVERY_PLAN.md`
- `docs/NEXT_STEPS_PROTOCOL_PLAN.md`
- `docs/protocol/LINUX_PROBING_NOTES.md`
- `docs/protocol/CAPTURE_GUIDE.md`
- `docs/protocol/PROTOCOL_DISCOVERY.md`

## License

MIT License
