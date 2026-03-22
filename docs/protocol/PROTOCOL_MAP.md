# Protocol Map

This document is the source-of-truth template for promoting packet-capture
findings into the real protocol backend.

## Status Levels

- `verified`: confirmed by packet capture and covered by tests
- `likely`: strongly suggested by capture evidence but not fully validated
- `speculative`: placeholder assumption, not suitable for the capture-backed backend

## Command Mapping Template

### Command Family

- Human action:
- Status:
- Capture file:
- Packet numbers:
- Notes:

### Frame Layout

- Header bytes:
- Command byte offset:
- Channel byte offset:
- Payload offsets:
- Checksum/CRC bytes:

### Examples

1. Action:
   - Raw packet:
   - Decoded meaning:

2. Action:
   - Raw packet:
   - Decoded meaning:

### Code Targets

- Encoder function:
- Decoder function:
- Backend method:
- Test file:

---

## Initial Priorities

1. Channel mute
2. Channel solo
3. Channel phase
4. Headphones source
5. Preset selection
6. Master/channel level controls
7. Routing and aux sends
8. DSP blocks
