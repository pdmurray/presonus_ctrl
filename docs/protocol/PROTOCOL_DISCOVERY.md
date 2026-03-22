# Protocol Discovery Guide - Presonus IO24 Control Utility

## 🎯 Overview

This document explains how to discover the control protocol for the Presonus Revelator IO24 by capturing USB traffic on Windows, then reverse-engineering it on Linux.

## 📋 Quick Start

**Short answer**: Just run the capture script, do some actions in the Presonus Control app, and the analyzer will tell you what to look for.

```bash
# On Linux (after capturing on Windows):
cd /home/patrmurr/code/example2/presonus_ctrl
python -m tools.analyze_usb /path/to/capture.pcap
```

The tool automatically detects:
- Command ID byte position
- Channel identifier byte position (1-24)
- Parameter value byte positions
- Fixed protocol signature bytes
- Likely default command ID

## 🪟 Phase 1: Windows Capture

### Recommended First Session

For the first capture session, keep the scope small and focus on commands we are
already prepared to promote into the protocol backend:

1. Startup baseline
2. Channel 1 mute on/off
3. Channel 1 solo on/off
4. Channel 1 phase invert on/off
5. Headphones source changes
6. Channel 1 preset load
7. Repeat the same actions on channel 10 and channel 24 where possible

Also follow `captures/notes/CAPTURE_CHECKLIST.md` so the captures are easy to
turn into fixture files and verified encoders later.

### Prerequisites

1. **Windows PC** with Presonus IO24 connected
2. **Wireshark** installed (with USBPcap)
3. **Presonus Control app** installed

### Capture Instructions

#### Option A: Automated capture (tshark)

```bash
# Find USB interfaces
tshark -L -e interface

# Start capture (example with USBPcap0)
python tools/capture_and_analyze.py -i USBPcap0 -o presonus_capture.pcap

# In Presonus Control app, perform actions:
# - Click on channels 1, 10, 24
# - Move fader min to max
# - Load different presets

# Press Ctrl+C when done
```

#### Option B: Wireshark GUI

1. Open Wireshark
2. Go to Capture → Interfaces
3. Select your USBPcap interface (USBPcap0 or USBPcap1)
4. Apply capture filter: `usb.capdata`
5. Click the blue shark fin to start
6. Perform actions in Presonus Control app (see table below)
7. Click red square to stop
8. Save as: `presonus_capture.pcap` (PCAP format)

### Recommended Actions to Perform

| Action | Purpose | What to Watch For |
|--------|---------|-------------------|
| Note initial packet count | Baseline | All startup commands |
| Click channel 1 | Identify channel byte | Packets with byte `0x01` |
| Click channel 10 | Confirm channel byte | Packets with byte `0x0A` |
| Click channel 24 | Confirm channel byte | Packets with byte `0x18` |
| Move fader to min | Identify value byte | Signed byte `0xFF` or `0xC0` |
| Move fader to nominal | Confirm value byte | Signed byte `0xFA` (-6) |
| Move fader to max | Confirm value byte | Unsigned `0x00` |
| Load preset "Off" | Identify command ID | First byte changes |
| Load preset "On" | Confirm command ID | Different first byte |

### Copy Capture to Linux

```bash
# Copy the .pcap file from Windows to your Linux machine
scp presonus_capture.pcap user@linux:/path/to/presonus_ctrl/
```

After copying the capture, also place it under:

- `captures/raw/`

And create companion notes under:

- `captures/notes/`

## 🔬 Phase 2: Linux Analysis

### Run the Auto-Detection Analysis

```bash
cd /home/patrmurr/code/example2/presonus_ctrl
python -m tools.analyze_usb presonus_capture.pcap
```

### Understanding the Output

The tool will output sections like:

```
🔍 AUTO-DETECTED PROTOCOL STRUCTURE
======================================

📌 Command ID Byte Position:
   Byte 0: [1, 2, 3, 4, 5]

📌 Channel Identifier Byte:
   Byte 2: values 1-24 (channel 1-24)

📌 Parameter Value Byte:
   Byte 3: 64 distinct values
   Raw range: -128 to 0 (signed 8-bit dB)

📌 Fixed Bytes (protocol signature):
   Byte 1: 0x01 (constant - protocol version)

📌 Default Command ID: 0x01
```

### What Each Section Means

| Section | What It Tells You | Use For |
|---------|-------------------|---------|
| Command ID Byte | Which byte varies per command type | Identify different operations |
| Channel Byte | Byte with values 1-24 | Target specific channel |
| Value Byte | Byte with parameter values | Set fader levels, etc. |
| Fixed Bytes | Constant bytes in every packet | Protocol frame structure |
| Default Command | First observed command ID | Initial handshake |

## 🛠 Phase 3: Implement Protocol

Based on the analysis, update `presonus_ctrl/presonus/protocol.py`:

```python
class IO24Protocol:
    # Example structure from analysis:
    # [CMD_ID][VER][CH_ID][VALUE][CRC]
    #  0xXX    0x01  0x01   0x80   0xXX
    
    CMD_FADER = 0x01
    CMD_PRESET = 0x02
    CMD_EQ = 0x03
    
    # Byte positions from auto-detection
    BYTE_CMD_ID = 0
    BYTE_VERSION = 1
    BYTE_CHANNEL = 2
    BYTE_VALUE = 3
    BYTE_CRC = -1
    
    @classmethod
    def encode_fader_command(cls, channel: int, value_db: int) -> bytes:
        """Encode a fader level change."""
        # Convert dB to signed 8-bit value
        value_byte = max(-128, min(0, value_db)) & 0xFF
        
        # Build packet (adjust positions based on your analysis)
        packet = bytes([
            cls.CMD_FADER,      # Command ID (byte 0)
            0x01,               # Protocol version (byte 1 - fixed)
            channel,            # Channel (byte 2)
            value_byte,         # Value (byte 3)
            # CRC would go here
        ])
        return packet
```

## 📝 Notes for Reverse Engineering

### Common Patterns

1. **Command IDs** are usually the first byte (0x00-0xFF)
2. **Channel IDs** are typically 1-24 (0x01-0x18 in hex)
3. **Level values** are often signed 8-bit:
   - -60dB ≈ 0xC0 (-64)
   - -6dB ≈ 0xFA (-6)
   - 0dB ≈ 0x00
4. **CRC/checksum** often varies based on other bytes

### Verification Strategy

Once you implement encoding:

```bash
# Compare captured vs. generated packets
python -c "
from presonus.protocol import IO24Protocol
pkt = IO24Protocol.encode_fader_command(1, -6)
print(f'Generated: {pkt.hex()}')
print('Compare with your captured packets...')
"
```

## 🐛 Troubleshooting

### No vendor interface packets found
- Ensure filter is `usb.capdata` not empty
- Try both USBPcap0 and USBPcap1 interfaces
- Check USB cable is properly connected

### Too few packets to analyze
- Perform more distinct actions
- Wait for initial handshake to complete before starting actions
- Try disconnecting and reconnecting the device mid-capture

### Analysis inconclusive
- Capture a longer session with more varied actions
- Try saving hex dumps: `--save-hexdir hex/`
- Manually inspect with Wireshark for patterns

## 📚 References

- [USBPcap GitHub](https://github.com/gpimm/USBPcap)
- [Wireshark USB Documentation](https://wiki.wireshark.org/USB)
- [scapy Documentation](https://scapy.readthedocs.io/)
