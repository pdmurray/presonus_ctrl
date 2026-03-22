"""CLI main module for Presonus IO24 control."""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import click
import usb.core
import usb.util

from presonus import PresetType, PresonusDevice, PresonusUSBError


def _slugify(value: str) -> str:
    return "-".join(value.strip().lower().split())


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="presonus-io24")
@click.pass_context
def cli(ctx):
    """presonus-io24 - Control utility for Presonus Revelator IO24 audio interface.
    
    This CLI tool allows you to control your Presonus IO24 from Linux. The device
    is class-compliant for audio playback/recording, but this tool provides full
    control of the 'fat channel' settings, levels, presets, and more.
    
    NOTE: The USB control protocol has not been reverse-engineered yet.
    Basic commands like 'info' and 'list' are placeholders until the protocol
    is discovered through Windows USB traffic analysis.
    
    See docs/protocol/PROTOCOL_DISCOVERY.md for reverse engineering instructions.
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


@cli.command()
def info():
    """Display device information."""
    try:
        with PresonusDevice() as device:
            if device.device:
                info = device.get_device_info()
                if info is not None:
                    click.echo(f"Vendor ID:      0x{info.vendor_id}")
                    click.echo(f"Product ID:     0x{info.product_id}")
                    click.echo(f"Product Name:   {info.product_name}")
                    if info.serial_number:
                        click.echo(f"Serial Number:  {info.serial_number}")
                    if info.firmware_version:
                        click.echo(f"Firmware:       {info.firmware_version}")
            else:
                # Device not found in open context, try to find it
                devices = device.find_devices()
                if devices:
                    d = devices[0]
                    click.echo("Device found:")
                    click.echo(f"  Vendor ID:      0x{d.idVendor:04x}")
                    click.echo(f"  Product ID:     0x{d.idProduct:04x}")
                    click.echo(f"  Product Name:   {d.product or 'Unknown'}")
                    if d.serial_number:
                        click.echo(f"  Serial Number:  {d.serial_number}")
                else:
                    click.echo("No Presonus IO24 device found.", err=True)
                    sys.exit(1)
    except PresonusUSBError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--mode",
    type=click.Choice(["mock", "protocol", "auto"]),
    default="mock",
    show_default=True,
    help="Backend mode to inspect",
)
def capabilities(mode: str):
    """Show backend capability status."""
    device = PresonusDevice(mode=mode)
    caps = device.capabilities()
    click.echo(f"Mode: {caps.mode}")
    for feature, status in sorted(caps.features.items()):
        click.echo(f"{feature:20} {status}")


@cli.command(name="send-known-sequence")
@click.option("--channel", type=int, default=1, show_default=True, help="Channel to target")
@click.option("--delay", type=float, default=1.0, show_default=True, help="Delay between actions")
@click.option(
    "--mode",
    type=click.Choice(["mock", "protocol", "auto"]),
    default="protocol",
    show_default=True,
    help="Backend mode used for transmission",
)
def send_known_sequence(channel: int, delay: float, mode: str):
    """Send a reversible mute/solo/phase sequence to the device."""
    if not 1 <= channel <= 24:
        click.echo("Channel must be between 1 and 24", err=True)
        sys.exit(1)

    sequence = [
        ("mute_on", lambda d: d.set_channel_mute(channel, True)),
        ("mute_off", lambda d: d.set_channel_mute(channel, False)),
        ("solo_on", lambda d: d.set_channel_solo(channel, True)),
        ("solo_off", lambda d: d.set_channel_solo(channel, False)),
        ("phase_on", lambda d: d.set_channel_phase(channel, True)),
        ("phase_off", lambda d: d.set_channel_phase(channel, False)),
    ]

    try:
        with PresonusDevice(mode=mode) as device:
            click.echo(f"Opened device in {device.mode} mode")
            for name, action in sequence:
                result = action(device)
                click.echo(f"{name}: {result}")
                time.sleep(delay)
            click.echo("Sequence complete")
    except PresonusUSBError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command(name="capture-note")
@click.argument("name", type=str, required=True)
def capture_note(name: str):
    """Create a timestamped capture session note in captures/notes."""
    root = Path(__file__).resolve().parents[1]
    captures_dir = root / "captures"
    raw_dir = captures_dir / "raw"
    notes_dir = captures_dir / "notes"
    hex_dir = captures_dir / "hex"
    fixtures_dir = captures_dir / "fixtures"

    for directory in (raw_dir, notes_dir, hex_dir, fixtures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d")
    slug = f"{stamp}-{_slugify(name)}"
    raw_capture = raw_dir / f"{slug}.pcapng"
    note_file = notes_dir / f"{slug}.md"

    if note_file.exists():
        click.echo(f"Note file already exists: {note_file}", err=True)
        sys.exit(1)

    note_file.write_text(
        f"# Capture Session: {name}\n\n"
        f"## Metadata\n\n"
        f"- Date: {stamp}\n"
        f"- Session slug: {slug}\n"
        f"- Raw capture file: {raw_capture.relative_to(root)}\n"
        f"- Fixture candidates directory: {fixtures_dir.relative_to(root)}\n\n"
        f"## Planned Actions\n\n"
        f"1. Startup baseline\n"
        f"2. Channel 1 mute on/off\n"
        f"3. Channel 1 solo on/off\n"
        f"4. Channel 1 phase on/off\n"
        f"5. Headphones source changes\n"
        f"6. Channel 1 preset load\n\n"
        f"## Notes\n\n-\n"
    )

    click.echo(f"Created note file: {note_file}")
    click.echo(f"Suggested raw capture path: {raw_capture}")


@cli.command(name="monitor-endpoint")
@click.option("--interface", "interface_number", type=int, required=True, help="Interface number to claim")
@click.option("--alt", type=int, default=0, show_default=True, help="Alternate setting to select")
@click.option("--endpoint", required=True, help="Endpoint address in hex, e.g. 0x81")
@click.option("--size", type=int, default=64, show_default=True, help="Read size in bytes")
@click.option("--seconds", type=float, default=20.0, show_default=True, help="Monitor duration")
@click.option("--timeout-ms", type=int, default=150, show_default=True, help="USB read timeout")
@click.option("--show-all", is_flag=True, help="Print every packet, not just changes")
def monitor_endpoint(
    interface_number: int,
    alt: int,
    endpoint: str,
    size: int,
    seconds: float,
    timeout_ms: int,
    show_all: bool,
):
    """Passively monitor a USB endpoint for packet changes."""
    dev: Any = usb.core.find(idVendor=PresonusDevice.VENDOR_ID, idProduct=PresonusDevice.PRODUCT_ID)
    if dev is None:
        click.echo("Presonus device not found", err=True)
        sys.exit(1)

    endpoint_value = int(endpoint, 16)
    previous = None
    start = time.time()
    idx = 0

    try:
        usb.util.claim_interface(dev, interface_number)
    except usb.core.USBError as exc:
        click.echo(f"Claim error: {exc}", err=True)
        click.echo("Hint: that interface is probably owned by the OS audio stack.")
        sys.exit(1)

    try:
        try:
            dev.set_interface_altsetting(interface=interface_number, alternate_setting=alt)
            click.echo(f"Selected interface {interface_number} alt {alt}")
        except Exception as exc:
            click.echo(f"Alt-setting warning: {exc}")

        click.echo(
            f"Monitoring endpoint 0x{endpoint_value:02x} on interface {interface_number} for {seconds:.1f}s"
        )

        consecutive_timeouts = 0
        while time.time() - start < seconds:
            idx += 1
            try:
                packet = bytes(dev.read(endpoint_value, size, timeout_ms))
                consecutive_timeouts = 0
                changed = packet != previous
                if show_all or changed:
                    click.echo(
                        f"t={time.time() - start:0.3f}s idx={idx} len={len(packet)} changed={changed} hex={packet.hex()}"
                    )
                previous = packet
            except KeyboardInterrupt:
                click.echo("Stopped by user")
                break
            except usb.core.USBTimeoutError:
                consecutive_timeouts += 1
                if consecutive_timeouts == 1 or consecutive_timeouts % 20 == 0:
                    click.echo(f"t={time.time() - start:0.3f}s idx={idx} timeout_count={consecutive_timeouts}")
            except Exception as exc:
                click.echo(f"t={time.time() - start:0.3f}s idx={idx} read_error={type(exc).__name__}: {exc}")
            time.sleep(0.02)
    finally:
        try:
            usb.util.release_interface(dev, interface_number)
        except Exception:
            pass


@cli.command(name='list')
def list_channels():
    """List all channels and their current settings."""
    try:
        with PresonusDevice():
            # TODO: This will be implemented after protocol discovery
            click.echo("Channel listing not yet implemented. See PROTOCOL_DISCOVERY.md")
            # After implementation:
            # state = device.query_state()
            # if state and state.channels:
            #     for ch_id, ch_settings in sorted(state.channels.items()):
            #         click.echo(f"Channel {ch_id}:")
            #         click.echo(f"  Fader:      {ch_settings.fader:.1f} dB")
            #         click.echo(f"  Gain:       {ch_settings.gain:.1f} dB")
            #         click.echo(f"  Mute:       {'Yes' if ch_settings.mute else 'No'}")
            #         click.echo(f"  Solo:       {'Yes' if ch_settings.solo else 'No'}")
            #         click.echo(f"  Preset:     {ch_settings.preset.value if ch_settings.preset else 'None'}")
            # else:
            #     click.echo("No channels found.")
    except PresonusUSBError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(0)


@cli.command(name='set')
@click.argument("channel", type=int, required=True)
@click.option("--level", "-l", type=float, required=True, help="Level value (0.0 to 1.0)")
@click.option("--mute", is_flag=True, help="Mute the channel")
@click.option("--fader", "-f", type=float, help="Fader level in dB")
def set_channel(channel: int, level: float, mute: bool, fader: float):
    """Set channel parameters.
    
    CHANNEL must be 1-24.
    
    Examples:
        presonus-io24 set 1 --level 0.75
        presonus-io24 set 3 --mute
        presonus-io24 set 5 --fader -12.0
    """
    if not 1 <= channel <= 24:
        click.echo("Channel must be between 1 and 24", err=True)
        sys.exit(1)
    
    if not 0.0 <= level <= 1.0:
        click.echo("Level must be between 0.0 and 1.0", err=True)
        sys.exit(1)
    
    try:
        with PresonusDevice():
            click.echo(f"Setting channel {channel} parameters...")
            # TODO: Implement parameter setting after protocol discovery
    except PresonusUSBError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("channel", type=int, required=True)
@click.argument("param", type=str, required=True)
def get(channel: int, param: str):
    """Get a specific parameter value for a channel.
    
    CHANNEL must be 1-24.
    PARAM can be: fader, gain, mute, solo, pan, eq, preset
    
    Example: presonus-io24 get 1 fader
    """
    if not 1 <= channel <= 24:
        click.echo("Channel must be between 1 and 24", err=True)
        sys.exit(1)
    
    try:
        with PresonusDevice():
            # TODO: Implement parameter query
            click.echo(f"Getting {param} from channel {channel}...")
            # After implementation:
            # state = device.query_state()
            # if state and channel in state.channels:
            #     ch = state.channels[channel]
            #     if param == "fader":
            #         click.echo(f"{ch.fader:.1f} dB")
            #     elif param == "gain":
            #         click.echo(f"{ch.gain:.1f} dB")
            #     elif param == "mute":
            #         click.echo("Yes" if ch.mute else "No")
            #     elif param == "solo":
            #         click.echo("Yes" if ch.solo else "No")
            #     elif param == "pan":
            #         click.echo(f"{ch.pan}")
            #     elif param == "preset":
            #         click.echo(ch.preset.value if ch.preset else "None")
            #     elif param == "eq":
            #         click.echo(f"Low: {ch.eq['low']:.1f}dB, Low-mid: {ch.eq['low_mid']:.1f}dB, High-mid: {ch.eq['high_mid']:.1f}dB, High: {ch.eq['high']:.1f}dB")
            # else:
            #     click.echo(f"Channel {channel} not found or no data available.", err=True)
    except PresonusUSBError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("channel", type=int, required=True)
@click.argument("value", type=float, required=True)
def fader(channel: int, value: float):
    """Set channel fader level.
    
    CHANNEL must be 1-24.
    VALUE is the level in dB (typically -inf to +3).
    
    Examples:
        presonus-io24 fader 1 -12.0
        presonus-io24 fader 5 0.0
        presonus-io24 fader 8 3.0
    """
    if not 1 <= channel <= 24:
        click.echo("Channel must be between 1 and 24", err=True)
        sys.exit(1)
    
    try:
        with PresonusDevice():
            # TODO: Implement fader set
            click.echo(f"Setting channel {channel} fader to {value:.1f} dB...")
            # After implementation:
            # success = device.update_channel_settings(channel, {"fader": value})
            # if success:
            #     click.echo(f"Channel {channel} fader set to {value:.1f} dB")
            # else:
            #     click.echo(f"Failed to set channel {channel} fader.", err=True)
    except PresonusUSBError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)




@cli.command(name='fat')
@click.argument("channel", type=int, required=True)
@click.option("--compressor", type=str, help="Enable/disable compressor (on/off)")
@click.option("--gate", type=str, help="Enable/disable gate (on/off)")
@click.option("--eq", type=str, help="Enable/disable EQ (on/off)")
def fat_channel(channel: int, compressor: str, gate: str, eq: str):
    """Control fat channel settings.
    
    CHANNEL must be 1-24.
    Options: compressor, gate, eq (values: on/off)
    
    Example:
        presonus-io24 fat 1 --compressor on
    """
    if not 1 <= channel <= 24:
        click.echo("Channel must be between 1 and 24", err=True)
        sys.exit(1)
    
    try:
        with PresonusDevice():
            click.echo(f"Adjusting fat channel settings for channel {channel}...")
            # TODO: Implement fat channel control after protocol discovery
    except PresonusUSBError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
@cli.command()
@click.argument("channel", type=int, required=True)
@click.argument("preset_name", type=str, required=True)
def preset(channel: int, preset_name: str):
    """Load a fat channel preset.
    
    CHANNEL must be 1-24.
    PRESET_NAME can be: vocal, guitar, bass, keyboard, drums, custom
    
    Example: presonus-io24 preset 1 vocal
    """
    if not 1 <= channel <= 24:
        click.echo("Channel must be between 1 and 24", err=True)
        sys.exit(1)
    
    preset_map = {
        "vocal": PresetType.VOCAL,
        "guitar": PresetType.GUITAR,
        "bass": PresetType.BASS,
        "keyboard": PresetType.KEYBOARD,
        "drums": PresetType.DRUMS,
        "custom": PresetType.CUSTOM,
    }
    
    if preset_name.lower() not in preset_map:
        click.echo(
            f"Invalid preset '{preset_name}'. "
            f"Valid presets: {', '.join(preset_map.keys())}",
            err=True
        )
        sys.exit(1)
    
    try:
        with PresonusDevice():
            # TODO: Implement preset load
            click.echo(f"Loading preset '{preset_name}' on channel {channel}...")
            # After implementation:
            # success = device.update_channel_settings(
            #     channel, {"preset": preset_map[preset_name.lower()]}
            # )
            # if success:
            #     click.echo(f"Loaded preset '{preset_name}' on channel {channel}")
            # else:
            #     click.echo(f"Failed to load preset.", err=True)
    except PresonusUSBError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def levels():
    """Show all levels and gains for all channels."""
    try:
        with PresonusDevice():
            # TODO: Implement batch levels query
            click.echo("Level display not yet implemented. See PROTOCOL_DISCOVERY.md")
    except PresonusUSBError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("channel", type=int, required=True)
def monitor(channel: int):
    """Monitor parameter changes for a channel.
    
    Continuously poll and display changes for the specified channel.
    Press Ctrl+C to stop.
    
    Example: presonus-io24 monitor 1
    """
    if not 1 <= channel <= 24:
        click.echo("Channel must be between 1 and 24", err=True)
        sys.exit(1)
    
    click.echo(f"Monitoring channel {channel}... Press Ctrl+C to stop")
    
    try:
        with PresonusDevice():
            # TODO: Implement continuous monitoring
            # This would involve periodic polling and diffing
            while True:
                # After implementation:
                # state = device.query_state()
                # if state and channel in state.channels:
                #     ch = state.channels[channel]
                #     print(f"{channel} fader={ch.fader:.1f}dB gain={ch.gain:.1f}dB")
                click.echo("Monitoring not yet implemented. See PROTOCOL_DISCOVERY.md")
                import time
                time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\nStopped monitoring.")


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--test", is_flag=True, help="Run protocol discovery test mode")
def discover(verbose: bool, test: bool):
    """Protocol discovery mode for reverse engineering."""
    try:
        with PresonusDevice() as device:
            if test:
                click.echo("Running protocol discovery tests...")
                # Test device discovery
                devices = device.find_devices()
                click.echo(f"Found {len(devices)} device(s)")
                
                if devices:
                    # Get USB descriptors
                    click.echo("\n=== USB Descriptors ===")
                    for dev in devices:
                        click.echo(f"\nDevice: {dev.product or 'Unknown'}")
                        click.echo(f"  VID:PID = 0x{dev.idVendor:04x}:0x{dev.idProduct:04x}")
                        
                        # Get device descriptor
                        try:
                            dev_desc = device.get_descriptor(0x01)
                            click.echo(f"  Device Descriptor: {len(dev_desc)} bytes")
                        except Exception as e:
                            click.echo(f"  Device Descriptor: Error - {e}")
                
                # Test interface enumeration
                click.echo("\n=== Interface Analysis ===")
                click.echo("Note: Need to analyze interface 5 (Vendor Specific)")
                click.echo("Command: usbhid-dump -s <bus> -d 194f:0422 -i 255")
                
                if verbose:
                    click.echo("\n=== Protocol Discovery Helper ===")
                    click.echo("\nTo capture Windows USB traffic:")
                    click.echo("1. Install USBPcap on Windows")
                    click.echo("2. Run the Presonus Control app")
                    click.echo("3. Capture traffic while adjusting controls")
                    click.echo("4. Analyze vendor-specific interface (IF 5)")
                    click.echo("\nUpdate presonus_ctrl/docs/protocol/PROTOCOL_DISCOVERY.md with findings")
            else:
                click.echo("Use --test flag to run discovery tests")
                
    except PresonusUSBError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
