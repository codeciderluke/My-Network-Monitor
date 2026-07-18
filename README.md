# My Network Monitor

A real-time network traffic monitor for Windows, built with Python 3.12 and
PySide6. It captures, parses, aggregates, and stores L3/L4 traffic metadata
through a polished dark-theme GUI.

![Python](https://img.shields.io/badge/python-3.12+-blue)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41cd52)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows-0078d6)

> Scope: captures L3/L4 metadata for TCP, UDP, DNS, ICMP, IPv4, IPv6 and ARP.
> It does **not** decrypt HTTPS content or block packets.

## Features

- Live capture on any wired/wireless interface (Scapy + Npcap)
- Inbound/outbound direction detection and per-protocol analysis
- Real-time download/upload speed with a rolling 60-second chart
- Detailed, filterable packet log (`QTableView` + ring buffer, 10k rows)
- Per-process attribution (top processes / destinations)
- SQLite persistence and CSV / JSON Lines export
- Non-blocking threaded pipeline — the UI never freezes under load
- Sleek dark theme with SVG icons, optimized for Full HD

## Requirements

- Windows 10 / 11
- Python 3.12+
- [Npcap](https://npcap.com/) (for real capture; enable "WinPcap API-compatible mode")
- Administrator privileges (for real capture only)

## Quick start

The bundled batch file sets up a virtual environment on first run:

```bat
run.bat            :: real capture (requests administrator rights)
run.bat --demo     :: preview the UI with synthetic traffic (no Npcap/admin)
```

Or run it manually:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m my_network_monitor.main --demo
```

## Documentation

- [User Manual (PDF)](docs/MyNetworkMonitor_UserManual.pdf)

## Architecture

```
Scapy Capture Thread → bounded raw queue → Parser Thread
   → Traffic Aggregator / Connection Tracker / Process Resolver
   → UI batch buffer → QTimer(250ms) → Summary Panel + Log Table
```

Packet capture and the GUI are fully decoupled; the UI refreshes only in
batches via `QTimer`, so heavy traffic never blocks the interface.

## Development

```powershell
pip install -e ".[dev]"
ruff check src tests
ruff format src tests
mypy
pytest
```

## Building a release (.exe)

```powershell
pip install -e ".[build]"
pyinstaller my-network-monitor.spec
```

The standalone executable is produced in `dist/`. See
[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) for obligations that apply
when distributing a bundled binary (Scapy is GPL v2).

## License

Released under the [MIT License](LICENSE) © 2026 Codecider Lab.
Third-party dependency licenses are listed in
[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
