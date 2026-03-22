#!/usr/bin/env python3
"""Monitor a specific USB endpoint for packet changes.

This tool is intended for passive probing while manually changing hardware or
software state on the connected Revelator IO 24.
"""

import argparse
import time
from typing import Any

import usb.core
import usb.util


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor a specific USB endpoint for changes")
    parser.add_argument("--vendor", default="194f", help="USB vendor ID in hex")
    parser.add_argument("--product", default="0422", help="USB product ID in hex")
    parser.add_argument("--interface", type=int, required=True, help="Interface number to claim")
    parser.add_argument("--alt", type=int, default=0, help="Alternate setting to select")
    parser.add_argument("--endpoint", required=True, help="Endpoint address in hex, e.g. 0x81")
    parser.add_argument("--size", type=int, default=64, help="Read size")
    parser.add_argument("--seconds", type=float, default=20.0, help="How long to monitor")
    parser.add_argument("--timeout-ms", type=int, default=150, help="USB read timeout in milliseconds")
    parser.add_argument("--show-all", action="store_true", help="Print every packet, not only changes")
    args = parser.parse_args()

    vendor_id = int(args.vendor, 16)
    product_id = int(args.product, 16)
    endpoint = int(args.endpoint, 16)

    dev: Any = usb.core.find(idVendor=vendor_id, idProduct=product_id)
    if dev is None:
        raise SystemExit("device not found")

    previous = None
    start = time.time()
    idx = 0

    try:
        usb.util.claim_interface(dev, args.interface)
    except usb.core.USBError as exc:
        print(f"claim_error={type(exc).__name__}: {exc}")
        print("hint=That interface is likely owned by the OS audio stack right now.")
        return

    try:
        try:
            dev.set_interface_altsetting(interface=args.interface, alternate_setting=args.alt)
            print(f"set_alt_ok interface={args.interface} alt={args.alt}")
        except Exception as exc:
            print(f"set_alt_error={type(exc).__name__}: {exc}")

        print(
            f"monitoring interface={args.interface} alt={args.alt} endpoint=0x{endpoint:02x} "
            f"size={args.size} seconds={args.seconds}"
        )

        consecutive_timeouts = 0
        while time.time() - start < args.seconds:
            idx += 1
            try:
                packet = bytes(dev.read(endpoint, args.size, args.timeout_ms))
                consecutive_timeouts = 0
                changed = packet != previous
                if args.show_all or changed:
                    print(
                        f"t={time.time() - start:0.3f}s idx={idx} len={len(packet)} "
                        f"changed={changed} hex={packet.hex()}"
                    )
                previous = packet
            except KeyboardInterrupt:
                print("stopped_by_user=True")
                break
            except usb.core.USBTimeoutError:
                consecutive_timeouts += 1
                if consecutive_timeouts == 1 or consecutive_timeouts % 20 == 0:
                    print(
                        f"t={time.time() - start:0.3f}s idx={idx} timeout_count={consecutive_timeouts}"
                    )
            except Exception as exc:
                print(f"t={time.time() - start:0.3f}s idx={idx} read_error={type(exc).__name__}: {exc}")
            time.sleep(0.02)
    finally:
        try:
            usb.util.release_interface(dev, args.interface)
        except Exception:
            pass


if __name__ == "__main__":
    main()
