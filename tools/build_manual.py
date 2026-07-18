"""Generate the English user manual PDF using PySide6 (QTextDocument + QPdfWriter).

Run:  python tools/build_manual.py [output.pdf]
No extra dependencies required beyond PySide6.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QMarginsF, QUrl
from PySide6.QtGui import (
    QFont,
    QFontDatabase,
    QPageLayout,
    QPageSize,
    QPdfWriter,
    QTextDocument,
)
from PySide6.QtWidgets import QApplication

_FONT_FILES = (
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/consola.ttf",
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from my_network_monitor import __version__  # noqa: E402
from my_network_monitor.ui import icons  # noqa: E402

ACCENT = "#0e7490"
ACCENT_LIGHT = "#22d3ee"
INK = "#11161f"
MUTED = "#5c6773"
BAND = "#0b0e14"
ROW_ALT = "#f2f6fa"
BORDER = "#d5dde6"


def _bar(title: str, number: str = "") -> str:
    label = f"{number}&nbsp;&nbsp;{title}" if number else title
    return (
        f'<table width="100%" cellpadding="6" cellspacing="0" '
        f'style="margin-top:16px;margin-bottom:6px;">'
        f'<tr><td bgcolor="{ACCENT}" '
        f'style="color:#ecfeff;font-size:13pt;font-weight:bold;">{label}</td></tr></table>'
    )


def _rows(pairs: list[tuple[str, str]], c1: str = "Item", c2: str = "Description") -> str:
    head = (
        f'<tr><td bgcolor="{INK}" style="color:#ecfeff;font-weight:bold;width:32%;">{c1}</td>'
        f'<td bgcolor="{INK}" style="color:#ecfeff;font-weight:bold;">{c2}</td></tr>'
    )
    body = []
    for i, (a, b) in enumerate(pairs):
        bg = ROW_ALT if i % 2 else "#ffffff"
        body.append(
            f'<tr><td bgcolor="{bg}" style="font-weight:bold;color:{INK};">{a}</td>'
            f'<td bgcolor="{bg}" style="color:{INK};">{b}</td></tr>'
        )
    return (
        f'<table width="100%" cellpadding="6" cellspacing="0" '
        f'style="border:1px solid {BORDER};margin-bottom:4px;">{head}{"".join(body)}</table>'
    )


def _p(text: str) -> str:
    return f'<p style="color:{INK};line-height:150%;margin:4px 0;">{text}</p>'


def _code(text: str) -> str:
    return (
        f'<table width="100%" cellpadding="8" cellspacing="0" style="margin:4px 0;">'
        f'<tr><td bgcolor="{BAND}" style="color:#7ef0ff;font-family:Consolas,monospace;'
        f'font-size:9.5pt;">{text}</td></tr></table>'
    )


def _bullets(items: list[str]) -> str:
    lis = "".join(f'<li style="color:{INK};margin:2px 0;">{x}</li>' for x in items)
    return f'<ul style="margin:4px 0;">{lis}</ul>'


def _pagebreak() -> str:
    return '<div style="page-break-before:always;"></div>'


def build_html() -> str:
    parts: list[str] = []

    # ---------- Cover ----------
    parts.append(
        f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
        f'<td bgcolor="{BAND}" align="center" style="padding:60px 40px;">'
        f'<img src="mem://logo" width="96" height="96"/><br/>'
        f'<span style="color:#e6edf3;font-size:30pt;font-weight:bold;">My </span>'
        f'<span style="color:{ACCENT_LIGHT};font-size:30pt;font-weight:bold;">Network</span>'
        f'<span style="color:#e6edf3;font-size:30pt;font-weight:bold;"> Monitor</span><br/>'
        f'<span style="color:#8b98a9;font-size:13pt;">Real-time network traffic monitor '
        f'for Windows</span><br/><br/>'
        f'<span style="color:{ACCENT_LIGHT};font-size:12pt;">User Manual</span><br/>'
        f'<span style="color:#5c6773;font-size:10pt;">Version {__version__}</span><br/><br/>'
        f'<span style="color:#8b98a9;font-size:10pt;">Designed by Codecider Lab</span>'
        f'</td></tr></table>'
    )

    # ---------- 1. Overview ----------
    parts.append(_bar("Overview", "1."))
    parts.append(
        _p(
            "My Network Monitor is a Windows desktop application that captures and "
            "visualizes live network traffic in real time. The left panel shows an at-a-glance "
            "summary (speeds, chart, statistics, top talkers, alerts); the right panel shows a "
            "detailed, filterable packet log."
        )
    )
    parts.append(
        _p(
            "It analyzes L3/L4 metadata for TCP, UDP, DNS, ICMP, IPv4, IPv6 and ARP. It does "
            "<b>not</b> decrypt HTTPS content or block packets."
        )
    )

    # ---------- 2. Requirements ----------
    parts.append(_bar("System Requirements", "2."))
    parts.append(
        _rows(
            [
                ("Operating System", "Windows 10 or Windows 11"),
                ("Python", "3.12 or later"),
                ("Capture driver", "Npcap (required for real capture)"),
                ("Privileges", "Administrator (for real capture)"),
                ("Libraries", "PySide6, pyqtgraph, scapy, psutil"),
            ]
        )
    )

    # ---------- 3. Installation ----------
    parts.append(_bar("Installation", "3."))
    parts.append(_p("1. Install Python 3.12+ and add it to PATH."))
    parts.append(
        _p(
            "2. Install Npcap from "
            '<span style="color:'
            + ACCENT
            + ';">https://npcap.com</span> and enable the '
            '"WinPcap API-compatible mode" option.'
        )
    )
    parts.append(_p("3. Install dependencies (a virtual environment is created automatically):"))
    parts.append(_code("pip install -r requirements.txt"))

    # ---------- 4. Running ----------
    parts.append(_bar("Running the Application", "4."))
    parts.append(_p("The simplest way to launch is the bundled batch file:"))
    parts.append(_code("run.bat&nbsp;&nbsp;&nbsp;&nbsp;:: real capture (requests admin rights)"))
    parts.append(_code("run.bat --demo&nbsp;&nbsp;:: preview UI with synthetic traffic"))
    parts.append(
        _p(
            "On first run, <b>run.bat</b> creates a virtual environment and installs "
            "dependencies. Real-capture mode automatically requests Administrator elevation. "
            "Demo mode needs neither Npcap nor admin rights and is ideal for exploring the UI."
        )
    )
    parts.append(_p("You can also start it directly:"))
    parts.append(_code("python -m my_network_monitor.main --demo"))

    parts.append(_pagebreak())

    # ---------- 5. UI Overview ----------
    parts.append(_bar("Interface Overview", "5."))
    parts.append(
        _rows(
            [
                ("Toolbar", "Interface selector, refresh, Start / Pause / Stop, SQLite toggle, "
                            "live capture status."),
                ("Summary panel (left)", "Download/upload speed, 60-second chart, protocol "
                                         "statistics, top processes and destinations, alerts."),
                ("Log table (right)", "Real-time per-packet log with color-coded direction and "
                                      "protocol."),
                ("Filter bar", "Display filters applied to the visible log."),
                ("Action bar", "Auto-scroll toggle, row copy, clear, CSV / JSONL export."),
                ("Status bar", "Current status messages and the product credit."),
            ],
            "Area",
            "What it shows",
        )
    )

    # ---------- 6. Capturing ----------
    parts.append(_bar("Capturing Traffic", "6."))
    parts.append(
        _bullets(
            [
                "Select a network interface from the toolbar dropdown (use the refresh button "
                "to re-scan).",
                "Click <b>Start</b> to begin capturing on the selected interface.",
                "Click <b>Pause</b> to freeze the log while capture and statistics continue; "
                "click again to resume.",
                "Click <b>Stop</b> to end capture and cleanly shut down all worker threads.",
            ]
        )
    )
    parts.append(
        _p(
            "Capture, parsing, and storage run on background threads, so the interface stays "
            "responsive even under heavy traffic. If the packet queue saturates, the dropped "
            "count is shown rather than freezing the app."
        )
    )

    # ---------- 7. Summary panel ----------
    parts.append(_bar("Reading the Summary Panel", "7."))
    parts.append(
        _rows(
            [
                ("Download / Upload", "Current inbound / outbound speed with automatic units."),
                ("60-second chart", "Rolling download (green) and upload (blue) speed history."),
                ("Statistics", "Active connections, packets/s, and per-protocol counts."),
                ("Top Processes", "Processes using the most bandwidth."),
                ("Top Destinations", "Remote hosts receiving the most bytes."),
                ("Alerts", "Threshold warnings such as high upload or dropped packets."),
            ],
            "Element",
            "Meaning",
        )
    )

    # ---------- 8. Log table ----------
    parts.append(_bar("The Traffic Log Table", "8."))
    parts.append(
        _rows(
            [
                ("Time", "Packet capture time."),
                ("Dir", "IN (inbound), OUT (outbound), or LOCAL."),
                ("Proto", "TCP, UDP, DNS, ICMP, or ARP."),
                ("Process / PID", "Owning process name and id (when resolvable)."),
                ("Source / S.Port", "Source IP address and port."),
                ("Destination / D.Port", "Destination IP (or domain) and port."),
                ("Size", "Packet length."),
                ("Summary", "Short human-readable description."),
            ],
            "Column",
            "Description",
        )
    )
    parts.append(_p("Double-click any row to open the packet detail view."))

    parts.append(_pagebreak())

    # ---------- 9. Filtering ----------
    parts.append(_bar("Filtering", "9."))
    parts.append(
        _p(
            "The filter bar applies a <b>display filter</b>: it changes what is shown without "
            "discarding captured data. Clear the fields to see everything again."
        )
    )
    parts.append(
        _bullets(
            [
                "Protocol and Direction dropdowns.",
                "IP address, Port, and Process substring search.",
                "Free-text search across source, destination, protocol, domain, and summary.",
            ]
        )
    )
    parts.append(
        _p(
            "A <b>capture filter</b> (BPF, e.g. <i>tcp port 443</i>) limits which packets are "
            "captured in the first place and is set via configuration."
        )
    )

    # ---------- 10. Packet detail ----------
    parts.append(_bar("Packet Detail View", "10."))
    parts.append(
        _p(
            "Double-clicking a log row opens a dialog with the full metadata (time, direction, "
            "interface, protocol, process, addresses, ports, length, summary) and a Hex / ASCII "
            "dump of the raw bytes."
        )
    )
    parts.append(
        _p(
            "For privacy, raw payload capture is <b>off by default</b>; enable "
            "<i>store_raw_payload</i> in configuration to populate the hex view."
        )
    )

    # ---------- 11. Saving & Export ----------
    parts.append(_bar("Saving and Exporting", "11."))
    parts.append(
        _rows(
            [
                ("SQLite", "Enable the toolbar toggle to persist packets to a database "
                           "(batched, non-blocking)."),
                ("CSV", "Export the current log via the action bar."),
                ("JSON Lines", "Export the current log as one JSON object per line."),
            ],
            "Format",
            "How to use",
        )
    )

    # ---------- 12. Configuration ----------
    parts.append(_bar("Configuration", "12."))
    parts.append(_p("Settings are read from an optional TOML file (pass it with --config):"))
    parts.append(
        _code(
            "[capture]<br/>default_interface = &quot;&quot;<br/>bpf_filter = &quot;ip or ip6&quot;"
            "<br/>queue_size = 50000<br/>store_raw_payload = false<br/><br/>"
            "[ui]<br/>refresh_interval_ms = 250<br/>chart_interval_ms = 1000<br/>"
            "max_visible_rows = 10000<br/>auto_scroll = true<br/><br/>"
            "[storage]<br/>enable_sqlite = false<br/>database_path = &quot;./data/traffic.db&quot;"
            "<br/>batch_size = 100<br/>flush_interval_ms = 1000"
        )
    )

    parts.append(_pagebreak())

    # ---------- 13. Troubleshooting ----------
    parts.append(_bar("Troubleshooting", "13."))
    parts.append(
        _rows(
            [
                ("\"Npcap is not installed\"",
                 "Install Npcap from npcap.com with WinPcap-compatible mode, then restart. "
                 "Use --demo to preview without capture."),
                ("No interfaces listed",
                 "Run as Administrator and click the refresh button."),
                ("Process names missing",
                 "Some short-lived or privileged connections cannot be mapped; they show as "
                 "empty."),
                ("Dropped packets shown",
                 "Traffic exceeded processing capacity; the app keeps running and reports the "
                 "count."),
                ("UI text looks garbled in console",
                 "Console-only encoding issue (e.g. localized adapter names); the GUI and log "
                 "file are correct."),
            ],
            "Symptom",
            "Resolution",
        )
    )

    # ---------- 14. Privacy & Security ----------
    parts.append(_bar("Privacy and Security", "14."))
    parts.append(
        _bullets(
            [
                "Captured metadata can be sensitive; raw payloads are not stored by default.",
                "The application never uploads data or performs remote analytics.",
                "Review exported files before sharing, as they may contain private information.",
                "Administrator rights are used only for packet capture.",
            ]
        )
    )

    parts.append(
        f'<p align="center" style="color:{MUTED};font-size:9pt;margin-top:24px;">'
        f'My Network Monitor v{__version__} &nbsp;&middot;&nbsp; '
        f'Designed by Codecider Lab</p>'
    )

    return (
        '<html><body style="font-family:\'Segoe UI\',sans-serif;font-size:10.5pt;">'
        + "".join(parts)
        + "</body></html>"
    )


def main() -> int:
    default_out = Path("docs/MyNetworkMonitor_UserManual.pdf")
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else default_out
    out.parent.mkdir(parents=True, exist_ok=True)
    app = QApplication(sys.argv)  # noqa: F841 - required for text/font rendering

    # Explicitly load fonts so glyphs embed even in a headless environment.
    for font_file in _FONT_FILES:
        if Path(font_file).exists():
            QFontDatabase.addApplicationFont(font_file)

    writer = QPdfWriter(str(out))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageMargins(QMarginsF(16, 16, 16, 18), QPageLayout.Unit.Millimeter)
    writer.setResolution(200)
    writer.setTitle("My Network Monitor - User Manual")

    doc = QTextDocument()
    doc.setDefaultFont(QFont("Segoe UI", 11))
    logo = icons.app_pixmap(160).toImage()
    doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl("mem://logo"), logo)
    doc.setHtml(build_html())
    doc.print_(writer)

    print(f"Wrote {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
