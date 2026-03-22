# USB Traffic Capture Guide for Presonus IO24 Control Protocol

## 🎯 Goal
Capture USB traffic from the Windows Control app, then analyze it to discover the protocol.

## 📋 Quick Summary for the User
You'll install **USBPcap** on Windows, use **Wireshark** to capture while doing actions in the Presonus Control app, then analyze the capture with our automated tool. The tool will tell you which bytes change and where, so you don't need to guess what to look for.

## 🔧 Prerequisites (Windows)

### Option A: USBPcap (Recommended)
1. Download from: https://github.com/gpimm/USBPcap/releases
2. Install `USBPcapInstaller.exe`
3. Accept the UAC prompt to install the driver
4. **Reboot required** after installation

### Option B: Microsoft Wireshark USBPcap
1. Open Wireshark
2. Go to `Edit → Preferences → Protocols → USBPcap`
3. Check "Enable USBPcap"
4. Restart Wireshark

## 🎬 Capture Process

### Step 1: Prepare the Capture
```
1. Connect your Presonus IO24 to Windows
2. Open Presonus Control app
3. In Wireshark: Capture → Interfaces
4. Find "USBPcap0" or "USBPcap1" (look for your USB controller)
5. Click the blue shark fin to start capturing
```

### Step 2: Perform Controlled Actions
Keep Wireshark capturing and do these actions **in order** (watch the packet count increase):

| Action | What to Do | What to Watch For |
|--------|------------|-------------------|
| **Baseline** | Note current packet count | All commands that happen on connect |
| **Channel 1** | Click/focus channel 1 | Look for packets with byte value `01` |
| **Channel 10** | Click/focus channel 10 | Look for packets with byte value `0a` (10) |
| **Channel 24** | Click/focus channel 24 | Look for packets with byte value `18` (24) |
| **Fader -60dB** | Drag fader to minimum | Look for packet with byte value `c0` (-64) or `ff` |
| **Fader -6dB** | Drag fader to nominal | Look for packet with byte value `fa` (-6) |
| **Fader 0dB** | Drag fader to maximum | Look for packet with byte value `00` |
| **Preset "Off"** | Load preset | Look for **command ID change** (first byte changes) |
| **Preset "On"** | Load preset | Look for **command ID change** |

### Step 3: Stop Capture
```
1. Click red square in Wireshark to stop
2. File → Save As...
3. Save as: presonus_io24_capture.pcap
4. Format: PCAP (libpcap - Ethernet)
```

## 🔬 Analysis Process (after capture)

### Copy PCAP to Linux
```bash
# Copy the .pcap file to your Linux machine
scp presonus_io24_capture.pcap user@linux:/path/to/presonus_ctrl/
```

### Run Automated Analysis
```bash
cd /home/patrmurr/code/example2/presonus_ctrl
python -m tools.analyze_usb presonus_io24_capture.pcap
```

### What the Tool Will Tell You:
The tool automatically detects:
- ✅ **Command ID byte position** - which byte tells us what type of command
- ✅ **Channel byte position** - which byte identifies channel 1-24
- ✅ **Value byte position** - which byte carries parameter values (dB, etc.)
- ✅ **Fixed bytes** - protocol signature bytes that never change
- ✅ **Likely default command** - what happens on initial connection

### Example Output:
```
🔍 AUTO-DETECTED PROTOCOL STRUCTURE
======================================================

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

## 📝 What to Note

After running analysis, note:
1. Which **byte position** is the command ID
2. Which **byte position** is the channel
3. Which **byte position** is the value
4. Any **fixed bytes** you should include in all commands
5. The **default command ID** (first one seen)

This info goes into `presonus_ctrl/presonus/protocol.py` for implementing the actual control functions.

## 🐛 Troubleshooting

### "No vendor interface packets found"
- You're capturing on the wrong interface
- In Wireshark filter: `usb.capdata`
- Try both `USBPcap0` and `USBPcap1`

### "Too few packets to analyze"
- Perform more distinct actions
- Make sure you're changing actual parameters
- Try a fresh capture (disconnect/reconnect device)

### "Scapy not installed"
```bash
pipx install scapy
# or
python3 -m pip install --user scapy
```
