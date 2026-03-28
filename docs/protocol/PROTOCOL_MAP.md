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

---

## Main Mix Faders (Windows Capture)

### Command Family

- Human action: sweep all Main Mix faders through their range in Universal Control
- Status: `likely`
- Capture file: `captures/raw/mainMix_volume_Up_Down-chan1_chan2_playback_virtualA_virtualB_Reverb_Main.pcapng`
- Packet numbers: many bulk OUT packets beginning around frame `13630`
- Notes:
  - capture note identifies the interesting traffic as `usb.device_address == 8 && frame.len == 543`
  - most packets are bulk OUT on endpoint `0x01`
  - a compact single-strip packet shape appears first, then a denser multi-strip packet shape appears near the end of the capture

### Likely Frame Layout

- Header bytes: `04 02 01 01`
- Likely fader value offset: byte `4`
  - this byte sweeps through the range as sliders move
- Likely strip identifier offset: byte `32`
  - observed values: `0`, `1`, `2`, `3`, `4`, `5`
- Likely dB float offset for single-strip packets: bytes `36:40` as little-endian float
- Likely grouped dB float offsets for multi-strip packets:
  - `44:48`
  - `52:56`
  - `60:64`
  - `68:72`
  - `76:80`
- Likely grouped strip ids paired with those floats:
  - `48:52` -> `04 00 00 00`
  - `56:60` -> `00 00 00 00`
  - `64:68` -> `01 00 00 00`
  - `72:76` -> `02 00 00 00`
  - `80:84` -> `05 00 00 00`

### Observed Segments

The capture splits into these likely strip-id blocks by byte `32`:

1. id `3` from packet index `0-274`
2. id `4` from packet index `275-457`
3. id `0` from packet index `458-595`
4. id `1` from packet index `596-698`
5. id `2` from packet index `699-790`
6. id `5` from packet index `791-893`
7. id `3` again from packet index `894-983`, but now with grouped multi-strip float values

This likely corresponds to the left-to-right sweep recorded in the note, but the exact mapping from id to visible strip name is not yet verified.

### Examples

1. Early single-strip packet:
   - Raw packet prefix: `040201013c0000005074655364000000000000006d72706df00100000000000003000000090aac3d`
   - Decoded meaning:
     - likely strip id `3`
     - likely fader byte `0x3c`
     - likely dB float `0.0840035155`

2. Minimum-looking single-strip packet:
   - Raw packet prefix: `040201014e0000005074655364000000000000006d72706df001000000000000040000000000c0c2`
   - Decoded meaning:
     - likely strip id `4`
     - likely fader byte `0x4e`
     - likely dB float `-96.0`

3. Late grouped packet:
   - Raw packet prefix: `040201015e0000005074655364000000000000006d72706df001000000000000030000000462c0c2040000000462c0c2000000000462c0c2010000000462c0c2020000000462c0c2050000000462c0c2`
   - Decoded meaning:
     - likely packet family rooted at strip id `3`
     - likely grouped float values for strip ids `4`, `0`, `1`, `2`, `5`
     - each float block shares the same little-endian value in this example

### What This Suggests

- Windows/Universal Control uses a packet family for level/fader updates that is very different from the current provisional Linux write packets
- Single-strip updates appear to carry:
  - a compact fader byte
  - a strip id
  - a float value
- Some later packets appear to bundle multiple strip values into one frame
- The decoded float field is very likely dB, not a normalized scalar:
  - capture values reach `-96.0`
  - user confirmed Universal Control displays `-96.0 dB` as the minimum fader value
  - user also noted the GUI max appears to be approximately `+10 dB`

### Current Mapping Hypothesis

Based on the recorded left-to-right action order in the capture note, the first-pass
hypothesis for the early single-strip packet blocks is:

- id `3` -> Channel 1
- id `4` -> Channel 2
- id `0` -> Playback
- id `1` -> Virtual A
- id `2` -> Virtual B
- id `5` -> Reverb

The final repeated `id 3` grouped packet family is still ambiguous. It may be:

- a Main/master fader update packet family
- a grouped UI/state refresh packet after the left-to-right sweep completes
- or a combination of both

### What Still Needs Verification

- exact mapping from strip ids `0-5` to:
  - channel 1
  - channel 2
  - playback
  - virtual A
  - virtual B
  - reverb
  - main
- whether the current mapping hypothesis above is correct
- whether byte `4` is the raw fader position or another control field
- whether bytes `36:40` and grouped float blocks are dB values, normalized values, or another meter/control representation
- whether the final grouped packets correspond specifically to the Main master fader or to a UI/state refresh packet family
