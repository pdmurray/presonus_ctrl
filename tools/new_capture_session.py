#!/usr/bin/env python3
"""Create a new packet-capture session workspace.

This helper creates a timestamped note file and suggests matching paths for the
raw capture and derived fixture files so a capture session stays organized.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


TEMPLATE = """# Capture Session: {session_name}

## Metadata

- Date: {date}
- Session slug: {slug}
- Raw capture file: {raw_capture}
- Fixture candidates directory: {fixture_dir}

## Environment

- Windows machine:
- Presonus app version:
- Device firmware version:
- USBPcap interface used:

## Planned Actions

1. Startup baseline
2. Channel 1 mute on/off
3. Channel 1 solo on/off
4. Channel 1 phase on/off
5. Headphones source changes
6. Channel 1 preset load
7. Repeat on channel 10 and 24 where possible

## Action Log

- [ ] Start capture
- [ ] Record baseline idle packets
- [ ] Perform action 1:
- [ ] Perform action 2:
- [ ] Perform action 3:
- [ ] Perform action 4:
- [ ] Perform action 5:
- [ ] Perform action 6:
- [ ] Save raw capture

## Notes

-

## Follow-up

- Run: `python -m tools.analyze_usb {raw_capture}`
- Copy relevant packet hex into fixture files under `captures/fixtures/`
- Update `docs/protocol/PROTOCOL_MAP.md`
"""


def slugify(value: str) -> str:
    return "-".join(value.strip().lower().split())


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a new Presonus capture session scaffold")
    parser.add_argument("name", help="Short session name, e.g. 'startup mute solo'")
    parser.add_argument(
        "--root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Project root containing the captures directory",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    captures_dir = root / "captures"
    raw_dir = captures_dir / "raw"
    notes_dir = captures_dir / "notes"
    hex_dir = captures_dir / "hex"
    fixtures_dir = captures_dir / "fixtures"

    for directory in (raw_dir, notes_dir, hex_dir, fixtures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d")
    slug = f"{stamp}-{slugify(args.name)}"
    raw_capture = raw_dir / f"{slug}.pcapng"
    note_file = notes_dir / f"{slug}.md"

    if note_file.exists():
        raise SystemExit(f"Note file already exists: {note_file}")

    note_file.write_text(
        TEMPLATE.format(
            session_name=args.name,
            date=stamp,
            slug=slug,
            raw_capture=raw_capture.relative_to(root),
            fixture_dir=fixtures_dir.relative_to(root),
        )
    )

    print(f"Created note file: {note_file}")
    print(f"Suggested raw capture path: {raw_capture}")
    print(f"Fixture directory: {fixtures_dir}")
    print("Next: start your Windows capture and save the file at the suggested raw path.")


if __name__ == "__main__":
    main()
