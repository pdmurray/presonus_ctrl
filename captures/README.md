# Capture Workspace

Store packet-capture evidence here once Windows USB captures are available.

Suggested layout:

- `raw/` - original `.pcap` or `.pcapng` files
- `notes/` - per-capture action logs and observations
- `hex/` - extracted packet hex dumps when useful
- `fixtures/` - normalized packet fixtures for automated tests

Quick start:

```bash
presonus-io24 capture-note "startup mute solo"
```

Recommended naming:

- `raw/2026-03-21-startup-and-mute.pcapng`
- `notes/2026-03-21-startup-and-mute.md`
- `fixtures/channel-mute-on.json`

Do not edit the original raw captures after copying them here.
