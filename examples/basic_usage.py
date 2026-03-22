"""Basic example usage for the current Presonus IO24 API."""

from presonus.device import PresonusDevice, PresonusUSBError


def main() -> None:
    try:
        with PresonusDevice(mode="auto") as device:
            info = device.get_device_info()
            if info is None:
                print("No device info available")
                return
            print("Connected device:")
            print(f"  Product: {info.product_name}")
            print(f"  Vendor ID: 0x{info.vendor_id}")
            print(f"  Product ID: 0x{info.product_id}")
            if info.serial_number:
                print(f"  Serial: {info.serial_number}")

            print("\nCapabilities:")
            for feature, status in sorted(device.capabilities().features.items()):
                if feature in {
                    "channel_mute",
                    "channel_solo",
                    "channel_phase",
                    "headphones_source",
                    "channel_preset",
                }:
                    print(f"  {feature}: {status}")

            print("\nSending a reversible protocol-backed test sequence...")
            print(f"  mute on: {device.set_channel_mute(1, True)}")
            print(f"  mute off: {device.set_channel_mute(1, False)}")
            print(f"  solo on: {device.set_channel_solo(1, True)}")
            print(f"  solo off: {device.set_channel_solo(1, False)}")
            print(f"  phase on: {device.set_channel_phase(1, True)}")
            print(f"  phase off: {device.set_channel_phase(1, False)}")
    except PresonusUSBError as exc:
        print(f"Device error: {exc}")


if __name__ == "__main__":
    main()
