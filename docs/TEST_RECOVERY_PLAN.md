# Test Recovery Plan for Presonus IO24 Control Library

## Current State

**Test Results:** Approximately 95 passed, 100 failed, 5 errors

The test suite is in a mixed state: the basic package/layout exists, a lot of API surface is sketched, but code and tests assert different contracts. The biggest issue is not "missing one feature"; it's that code, tests, and protocol assumptions disagree with each other.

**Where It Stands:**
- `presonus/models.py` is mostly shaped to satisfy simpler model tests, but it no longer cleanly matches richer device/protocol tests
- `presonus/device.py` is the main hotspot: discovery, open/close behavior, command building, and state querying don't match what tests expect
- `presonus/protocol.py` contains partial protocol helpers plus older/newer abstractions that don't line up with each other
- The test suite mixes:
  - API-contract tests that are reasonable to satisfy now
  - Placeholder/mock protocol tests
  - Highly specific protocol assertions that are not justified yet without packet captures

---

## Major Failure Clusters

### 1. Device Lifecycle Contract Drift
- `find_devices()` returns indices, but tests expect USB device objects
- `open()` bypasses `find_devices()`, doesn't keep `_device`, uses `device.open()`, has different signature/error contract than tests expect
- `PresonusDevice` has no `_device` at init and no `device` property, breaking both device tests and `cli info`

### 2. Model/API Surface Mismatch
- Missing helpers like `VolumeValue.from_db()` and `GainValue.from_db()`
- `PanValue` shape doesn't match test expectations (`value` vs `raw/left_to_right`)
- `FrequencyBand` is a dataclass, but tests use it like an enum
- `EqSettings`, `CompressorSettings`, `GateSettings`, `LimiterSettings`, `DeviceInfo`, and `FatChannelSettings` expose different fields than tests expect

### 3. Command Building/Wiring Bugs
- `device.py` calls `create_channel_command()` with arguments reversed
- Passes message objects instead of encoded bytes
- Several message classes used by `device.py` are not imported there
- Broad `except Exception: return False` hides real bugs, so tests that expect specific errors fail differently

### 4. Protocol Helpers Drift
- `protocol.py` has multiple abstractions that don't map cleanly to each other
- `ProtocolDiscovery.analyze_response()` returns different keys than `test_protocol.py` tests
- `CommandType` and `ProtocolCommand` coexist with differing responsibilities

### 5. CLI vs. Implementation Inconsistencies
- CLI `info` expects `device.device` which doesn't exist in implementation
- `list`, `set`, `fader`, `fat channel`, and `preset` are documented as placeholders but not enforced consistently in the test suite

---

## Recovery Strategy

- Stabilize the mocked/public API so the library and CLI are internally consistent
- Keep protocol implementation minimal and honest
- Classify tests:
  - `unit/mock-supported` — pass now or shortly
  - `protocol-speculative` — mark `xfail` until real packet capture is available

---

## File-by-File Plan

### `presonus/device.py`

**Fix discovery contract**
- `find_devices()` should return actual USB device objects, not indices
- Filter by `v_vendor_id==0x194f` / `product_id==0x0422`

**Fix lifecycle contract**
- Initialize `_device`, `_initialized`, and `_handle` in `__init__`
- Add `device` property so `cli/main.py` can safely use `device.device`
- `open(index=0)` should use `find_devices()` and handle:
  - No device at index
  - Kernel driver active → detach
  - Set configuration

**Fix open/close behavior**
- Use libusb/`pyusb` handle properly, not raw `device.open()`
- Ensure `close()` safely releases interface/resources

**Fix control methods**
- Import missing message classes: `ChannelMessage`, `MasterMessage`, `DSPMessage`, `RoutingMessage`
- Pass encoded payload bytes to the device
- Stop swallowing all exceptions; only return `False` for validation failures

**Add/normalize methods expected by tests**
- `set_channel_input_source`
- `set_channel_preset`
- `set_device_preset`
- `set_routing`
- `set_aux_send_level`
- `set_reverb_send_level`

**Fix state methods**
- `query_state()` should build 24 mock-compatible channels and a `MasterState`
- `get_device_info()` should construct `DeviceInfo` with correct field names

**Targeted fixes**
- `create_channel_command(...)` argument order
- `write_bulk` / `transfer` error paths
- `query_state()` mock mode

---

### `presonus/models.py`

**Reconcile value/helper types**
- `VolumeValue.from_db()` should normalize dB
- `GainValue.from_db()` should normalize gain
- `PanValue.from_db()` and a stable `.value` contract

**Resolve naming collision with `OutputValue`**
- Tests use it as RoutingEnum
- README/models imply numeric output values
- Consider split into two types or keep compatibility aliases

**Fix enum/alias surface**
- `HeadphonesSource` needs names matching tests (`LINE`, `MONITOR`, `HOTKEY`)
- `FrequencyBand` should be a stable enumeration (with `LOW`, `LOW_MID`, `HIGH_MID`, `HIGH`)

**Expand DSP setting dataclasses to test expectations**
- `CompressorSettings.output_gain`
- `GateSettings.ratio`, `hold`
- `LimiterSettings.release`, `lookahead`
- `EqSettings.set_band(...)`

**Keep model serialization simple and stable**
- `to_dict` should satisfy model/API tests without claiming hardware truth

---

### `presonus/protocol.py`

**Unified public protocol abstraction**
- Choose one primary public protocol abstraction
- Expose:
  - `CommandType`
  - `encode_control_message`
  - `decode_control_message`
  - `ProtocolDiscovery.analyze_response`
- Normalize `ProtocolDiscovery.analyze_response()` output keys:
  - `raw`, `length`, `header`, `cmd_byte`
- Keep all protocol implementation explicitly provisional:
  - enough to satisfy placeholder/mock tests
  - do not invent capture-level accuracy without captured evidence

---

### `cli/main.py`

**Align CLI with actual device contract**
- `info` should no longer rely on undocumented internals
- Keep placeholder commands honest
- `list`, `set`, `fader`, `fat channel`, `preset` should stay as placeholders until protocol discovery supports them

---

### `tests/conftest.py`

**Review and simplify fixtures**
- Fix stale fixtures: `sample_preset`, `sample_fat_channel`
- Remove or fix any fixtures referencing nonexistent fields/classes

---

## Test Triage

### Keep and make pass now
- `tests/test_models.py`
- Most of `tests/test_device.py`
- Most of `tests/test_device_api.py`
- Most of `tests/test_cli.py`
- Input validation parts of `tests/test_errors.py`
- Placeholder protocol tests that only assert helper behavior

### Rewrite after API stabilization
- Tests with unit mismatch (dB vs normalized)
- `HeadphonesSource` tests if enum names don't match intent
- CLI tests that assume control paths but CLI says "not implemented"
- Test fixtures in `tests/conftest.py` referencing nonexistent fields

### Mark `xfail` or move to `speculative_protocol`
- Exact command-byte assertions
- Packet encode/decode semantics without capture evidence
- Routing/DSP payload semantics
- Binary parsing not backed by packet captures

---

## Execution Order

1. **Stabilize `models.py`**
   - Helper constructors, enums, DSP settings
2. **Stabilize `device.py` lifecycle**
   - Discovery, open/close, context manager, `_device`, `device`
3. **Fix mocked control-path methods in `device.py`**
   - Channel/master/routing/aux/reverb/preset methods
4. **Add protocol compatibility shim in `protocol.py`**
   - Enough for placeholder protocol tests
5. **Re-run tests and classify remaining failures**
   - Genuine API bugs
   - Inconsistent tests
   - Speculative protocol tests
6. **Update test suite**
   - Rewrite inconsistent tests
   - Mark speculative as `xfail`

---

## Expected End State Before Packet Capture

Probably green under:
- models
- CLI basics
- device discovery/lifecycle
- mocked control methods
- serialization / discovery placeholders

Deferred until protocol capture:
- exact routing bytes
- exact DSP packet formats
- exact protocol decode/CRC semantics tied to real hardware

---

## Policy Recommendations

### Unit vs. Protocol Speculation Boundary
- Create two test categories:
  - `unit/mock-supported`
  - `protocol-speculative`
- This keeps CI meaningful instead of encouraging guessed implementations

### Validation vs. Speculation
- Keep validation tests happy now (db, ranges, enums)
- Mark all speculative protocol tests explicitly

### Keep Protocol Implementation Minimal
- Minimal encoders/decoders that pass placeholder tests
- Do not commit to byte-level protocol assumptions without captured evidence

---

## Notes for Implementation

- Be explicit about what is mock/test behavior and what is claimed hardware protocol behavior
- If packet capture is performed, use it to decide which speculative tests become authoritative and which must be rewritten

---

## Quick Summary

- Fix device discovery/open/close context manager first
- Fix models/helpers/enums/DSP settings second
- Fix device command wiring and missing control methods third
- Fix state/query/device-info behavior fourth
- Add protocol compatibility shim fifth
- Re-run tests and classify, then rewrite/speculative xfail
