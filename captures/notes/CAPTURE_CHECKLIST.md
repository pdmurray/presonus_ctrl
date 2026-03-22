# Packet Capture Checklist

Use this checklist when recording the first Windows USB captures.

## Before You Start

- Confirm the device is connected directly over USB
- Close unrelated audio/control applications
- Start a fresh capture in Wireshark or via `python tools/capture_and_analyze.py`
- Note the exact time the capture starts

## Capture These Actions In Order

1. Startup / idle baseline
2. Select channel 1
3. Mute channel 1 on, then off
4. Solo channel 1 on, then off
5. Phase invert channel 1 on, then off
6. Change headphones source through each available option
7. Load a preset on channel 1
8. Repeat the same actions on channel 10 and channel 24 where possible

## For Each Action

- Write down the UI action in plain language
- Note whether the action was toggled on or off
- Record the channel number
- Leave a short pause between actions so packets are easier to correlate

## After Capture

- Save the raw `.pcapng` file into `captures/raw/`
- Create a matching note file in `captures/notes/`
- Run `python -m tools.analyze_usb <capture-file>`
- Copy the most relevant packet hex into a fixture file under `captures/fixtures/`
