#!/usr/bin/env python3
"""Monitor the Presonus vendor endpoint for changes.

This is a passive Linux-side probe. It does not attempt to interpret the real
protocol; it only watches for traffic differences while you manipulate the
device manually.
"""

from __future__ import annotations

import argparse
import time

from presonus.device import PresonusDevice, PresonusUSBError


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor vendor endpoint 0x81 for packet changes")
    parser.add_argument("--seconds", type=float, default=20.0, help="How long to monitor")
    parser.add_argument("--timeout-ms", type=int, default=150, help="USB read timeout in milliseconds")
    parser.add_argument("--show-all", action="store_true", help="Print every packet, not just changes")
    args = parser.parse_args()

    previous = None
    start = time.time()
    count = 0

    try:
        with PresonusDevice(mode="mock") as device:
            print("opened=True")
            print(f"monitoring_for={args.seconds}s timeout_ms={args.timeout_ms}")
            while time.time() - start < args.seconds:
                count += 1
                try:
                    packet = device._read_data(timeout=args.timeout_ms)
                    changed = packet != previous
                    if args.show_all or changed:
                        print(
                            f"t={time.time() - start:0.3f}s idx={count} len={len(packet)} "
                            f"changed={changed} hex={packet.hex()}"
                        )
                    previous = packet
                except Exception as exc:
                    print(f"t={time.time() - start:0.3f}s idx={count} read_error={type(exc).__name__}: {exc}")
                time.sleep(0.02)
    except PresonusUSBError as exc:
        print(f"presonus_error={exc}")


if __name__ == "__main__":
    main()
