#!/usr/bin/env python3
"""Send a known reversible command sequence to the connected Revelator IO 24.

Use this while a separate usbmon capture is running so the exact host-side USB
traffic can be correlated with a known sequence of actions.
"""

from __future__ import annotations

import argparse
import time

from presonus.device import PresonusDevice, PresonusUSBError


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a known reversible command sequence")
    parser.add_argument("--channel", type=int, default=1, help="Channel to target")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between actions in seconds")
    parser.add_argument(
        "--mode",
        default="protocol",
        choices=["mock", "protocol", "auto"],
        help="Backend mode to use for transmission",
    )
    args = parser.parse_args()

    sequence = [
        ("mute_on", lambda d: d.set_channel_mute(args.channel, True)),
        ("mute_off", lambda d: d.set_channel_mute(args.channel, False)),
        ("solo_on", lambda d: d.set_channel_solo(args.channel, True)),
        ("solo_off", lambda d: d.set_channel_solo(args.channel, False)),
        ("phase_on", lambda d: d.set_channel_phase(args.channel, True)),
        ("phase_off", lambda d: d.set_channel_phase(args.channel, False)),
    ]

    try:
        with PresonusDevice(mode=args.mode) as device:
            print(f"opened=True mode={device.mode} channel={args.channel} delay={args.delay}")
            for name, action in sequence:
                print(f"action={name}")
                result = action(device)
                print(f"result={result}")
                time.sleep(args.delay)
            print("sequence_complete=True")
    except PresonusUSBError as exc:
        print(f"presonus_error={exc}")


if __name__ == "__main__":
    main()
