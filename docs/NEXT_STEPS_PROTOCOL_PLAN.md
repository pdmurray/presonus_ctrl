# Next Steps: Mock/Protocol Split and Capture-Backed Implementation

## Overview

The project now has a stable, passing mock-compatible test suite. The next phase is to separate that compatibility layer from the future capture-backed protocol implementation, then replace provisional command encoders with verified USB protocol logic derived from Windows packet captures.

This document covers:

1. Splitting the current mock-compatible layer from future capture-backed protocol code
2. Replacing provisional command payloads with capture-backed implementations
3. Updating project documentation and contributor workflow to reflect that split

---

## 1. Split Mock-Compatible vs Capture-Backed Layers

### Goals

- Keep today's stable, testable public API
- Isolate all guessed/provisional USB behavior behind an explicitly temporary layer
- Make it easy to swap in real protocol encoders as captures become available
- Prevent the passing suite from implying that the real hardware protocol is fully known

### Target Architecture

#### `presonus/device.py`
- Remains the public high-level API
- Stops knowing byte-level protocol details directly
- Delegates command building and transport behavior to a backend/adapter layer

#### New `presonus/backends/` package
- `mock_backend.py`
  - deterministic, test-friendly behavior
  - implements the current compatibility behavior
  - builds placeholder payloads only as needed for mock tests
- `protocol_backend.py`
  - real backend using verified protocol mappings
  - initially partial
  - expanded incrementally as captures are analyzed

#### New `presonus/usb_transport.py`
- Handles raw USB open/read/write/release behavior only
- No command semantics
- Used by both backends

#### `presonus/protocol.py`
- Narrowed to protocol primitives only:
  - frame format
  - command IDs
  - encode/decode helpers
  - response analysis helpers

#### Optional `presonus/capabilities.py`
- Declares implementation status for features:
  - `mock_supported`
  - `capture_verified`
  - `unknown`

### Recommended Dependency Flow

- `PresonusDevice` -> backend -> transport

Rules:
- `PresonusDevice` should not construct payload bytes directly
- backend should be responsible for:
  - validation of support
  - command encoding choice
  - response parsing
- transport should only:
  - open USB device
  - close USB device
  - write bytes
  - read bytes

### Concrete Refactor Phases

#### Phase A: Extract transport
- Move USB open/close/read/write logic from `PresonusDevice` into `usb_transport.py`
- Keep `PresonusDevice` public API unchanged

#### Phase B: Introduce backend interface
Suggested methods:
- `set_channel_volume(...)`
- `set_channel_pan(...)`
- `set_channel_mute(...)`
- `set_channel_solo(...)`
- `set_channel_gain(...)`
- `set_channel_phase(...)`
- `set_channel_input_source(...)`
- `set_headphones_source(...)`
- `set_master_volume(...)`
- `set_monitor_blend(...)`
- `set_headphones_volume(...)`
- `set_compressor(...)`
- `set_gate(...)`
- `set_eq(...)`
- `set_limiter(...)`
- `set_channel_preset(...)`
- `set_routing(...)`
- `set_aux_send_level(...)`
- `set_reverb_send_level(...)`
- `query_state()`
- `get_device_info()`

Start by implementing the current behavior in `MockBackend`.

#### Phase C: Make `PresonusDevice` delegate
- Preserve existing public methods
- `PresonusDevice` becomes orchestration layer only
- Backend chosen by explicit mode or policy

#### Phase D: Add `ProtocolBackend`
- Initially implement only capture-backed commands
- Unknown commands should fail explicitly instead of guessing
- No silent speculative fallback by default

### Mode Selection Strategy

Recommended:
- `PresonusDevice(mode="mock" | "protocol" | "auto")`

Behavior:
- `mock`
  - current stable compatibility behavior
- `protocol`
  - capture-verified protocol only
- `auto`
  - optional later mode
  - uses verified protocol implementations where available
  - otherwise fails clearly or falls back only if policy allows

### Backend Contract

Internally, prefer richer result handling even if public methods still return `bool`.

Suggested internal result structure:
- `success: bool`
- `error: Optional[str]`
- `payload: Optional[bytes]`
- `verified: bool`

### Test Strategy for the Split

- Keep current passing suite on `MockBackend`
- Add protocol-specific suites for:
  - frame encoding
  - command byte mappings
  - response parsing
- Mark protocol tests by verification level:
  - `verified_from_capture`
  - `speculative`
- Do not let speculative protocol tests gate the main green suite

### Deliverables for Step 1

- backend interface definition
- extracted USB transport module
- `MockBackend` using current compatibility behavior
- `ProtocolBackend` skeleton with partial verified support
- tests reorganized by backend/protocol verification level

---

## 2. Replace Provisional Payloads with Capture-Backed Implementations

### Goals

- Stop inventing command bytes and payload layouts
- Replace them incrementally with evidence-backed implementations
- Keep provenance for every verified mapping
- Ensure that every promoted encoder/decoder can be traced back to a capture

### Source of Truth to Establish

#### New capture artifacts directory
Example:
- `captures/`
  - raw `.pcap` / `.pcapng`
  - extracted hex dumps
  - analysis notes
  - action logs

#### New protocol mapping document
Example:
- `docs/protocol/PROTOCOL_MAP.md`

Each command entry should include:
- human action
- capture file name
- packet offsets or relevant packet numbers
- command ID
- channel byte location
- payload byte layout
- checksum/CRC notes
- confidence level

### Verification Workflow Per Command

For each command family:

1. Choose one command family
2. Capture 3-5 examples of the same action
   - different channels
   - different values
3. Identify:
   - fixed bytes
   - command byte
   - channel byte
   - value byte(s)
   - checksum bytes
4. Encode findings in `PROTOCOL_MAP.md`
5. Add a verified encoder function/class
6. Add tests using real captured examples
7. Switch backend method from provisional encoder to verified encoder

### Implementation Pattern Per Command Family

Example verified encoder naming:
- `encode_set_mute(channel, muted)`
- `encode_set_solo(channel, solo)`
- `encode_set_phase(channel, inverted)`
- `encode_set_volume(channel, value_db)`

Rules:
- every verified encoder must cite capture evidence
- every verified encoder must have exact byte-level tests
- no fallback guessing inside verified encoder functions

### Recommended Command Family Order

#### First wave: lowest ambiguity, highest value
1. channel mute
2. channel solo
3. channel phase
4. headphones source
5. preset selection

#### Second wave: moderate ambiguity
6. master volume
7. headphones volume
8. monitor blend
9. channel volume/fader
10. input gain

#### Third wave: more complex routing controls
11. aux send
12. reverb send
13. routing

#### Final wave: highest complexity
14. compressor
15. gate
16. EQ
17. limiter
18. full state query parsing

### State Query Plan

Do not start with a full binary parser.

Instead:
1. verify whether there is a single "get state" command
2. determine whether the Windows control app issues multiple queries instead
3. only implement parsers after command/response pairs are captured

Recommended parser layering:
- raw response decoder
- semantic parser
- model constructor

### Provenance Policy

Every verified encoder/decoder should record:
- capture file name
- packet examples
- unresolved assumptions

Use confidence levels:
- `verified`
- `likely`
- `speculative`

Only `verified` mappings should power the default real protocol backend.

### Test Migration Plan

For each verified command:
- add "encode matches capture" tests
- add "decode extracts expected fields" tests

For unresolved commands:
- keep as `xfail`
- or move to a separate speculative protocol suite

### Deliverables for Step 2

- `docs/protocol/PROTOCOL_MAP.md`
- packet capture corpus under `captures/`
- first verified encoder set for boolean/source/preset commands
- `ProtocolBackend` updated to use those encoders
- verified packet-based tests

---

## 3. README Update Plan

### Top-Level Positioning

The README should clearly state that the project currently has:
- a stable mock/test API layer
- a provisional protocol layer
- ongoing reverse engineering for real USB control

It should no longer imply that all controls are hardware-verified today.

### Add a Status Matrix

Suggested sections:
- `Implemented (mock-compatible)`
- `Capture-verified`
- `Planned / speculative`

List command families under each.

### Update Usage Examples

Examples should reflect the current public API that actually exists.

Include:
- one mock-safe API example
- one future protocol-mode example marked as capture-backed/partial

Avoid implying verified hardware control for commands that are still provisional.

### Update API Reference

Fix mismatches such as:
- `set_channel_preset` signature
- output/routing type names
- headphones source semantics
- channel count/spec wording
- distinction between compatibility-layer behavior and capture-verified behavior

### Add Protocol Status Section

Link to:
- `docs/protocol/PROTOCOL_DISCOVERY.md`

Explain:
- packet-capture workflow
- how verified mappings are promoted into code
- why passing tests do not yet equal real hardware support

### Add Testing Philosophy Section

Explain:
- mock-compatible tests
- capture-verified tests
- speculative protocol tests

### Update Device Specs Section

Remove or qualify anything not yet confirmed, especially:
- endpoint claims
- channel count claims
- command format assumptions

### Add Contributor Workflow

Describe:
- how to add a new capture-backed command
- where to store capture evidence
- how to write a verified protocol test

---

## Recommended Execution Order

1. Extract USB transport
2. Introduce backend interface
3. Move current behavior into `MockBackend`
4. Add `ProtocolBackend` skeleton
5. Update README to document the split
6. Add `docs/protocol/PROTOCOL_MAP.md`
7. Start capture-backed implementation with:
   - mute
   - solo
   - phase
   - preset
   - headphones source
8. Add packet-based tests
9. Convert protocol suite from placeholder assertions to evidence-backed assertions

---

## Expected Outcome

### Near Term
- public API remains stable
- main suite stays green
- protocol work can proceed without destabilizing compatibility behavior

### Medium Term
- simple commands become capture-verified
- speculative protocol tests are replaced with packet-backed tests
- confidence in real hardware support improves incrementally

### Long Term
- `ProtocolBackend` becomes the primary real implementation
- mock backend remains useful for tests and offline development
- protocol assumptions are replaced entirely by verified mappings
