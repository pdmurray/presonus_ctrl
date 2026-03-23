# mainMix_volume_Up_Down-chan1_chan2_playback_virtualA_virtualB_Reverb_Main.md

## Description
Captured all Main Mix channel faders, moving each slider from top to bottom of the range
and back multiple times, ending at minimum (-96.00 dB / fully down).

## Actions Performed (left to right)
1. **Channel 1** — fader swept full range (0.00 dB ↔ -96.00 dB), multiple passes, ended down
2. **Channel 2** — fader swept full range, multiple passes, ended down
3. **Playback** — fader swept full range, multiple passes, ended down
4. **Virtual A** — fader swept full range, multiple passes, ended down
5. **Virtual B** — fader swept full range, multiple passes, ended down
6. **Reverb** — fader swept full range, multiple passes, ended down
7. **Main** (top right) — fader swept full range, multiple passes, ended down

## Packet Characteristics
- Device address: 8
- Interface: USBPcap5
- Control packets: 543 bytes (URB_BULK)
- Background traffic: 27 and 267 byte packets (status/meter updates, ignore)

## Filter
```
usb.device_address == 8 && frame.len == 543
```
