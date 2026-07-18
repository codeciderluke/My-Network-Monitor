"""Dark theme color palette and stylesheet loader."""

from __future__ import annotations

import sys
from pathlib import Path


class Palette:
    """Refined dark palette (GitHub Dark family + cyan accent)."""

    # Background layers
    BG_BASE = "#0b0e14"  # bottom-most background
    BG_SURFACE = "#11161f"  # panel surface
    BG_ELEVATED = "#161c26"  # cards/inputs
    BG_HOVER = "#1c2431"

    # Borders/dividers
    BORDER = "#232b38"
    BORDER_STRONG = "#2f3a4c"

    # Text
    TEXT_PRIMARY = "#e6edf3"
    TEXT_SECONDARY = "#8b98a9"
    TEXT_MUTED = "#5c6773"

    # Accents
    ACCENT = "#22d3ee"  # cyan
    ACCENT_DIM = "#0e7490"
    ACCENT_SOFT = "#164e5b"

    # Status/direction
    DOWNLOAD = "#34d399"  # download (inbound) - green
    UPLOAD = "#60a5fa"  # upload (outbound) - blue
    DIR_IN = "#34d399"
    DIR_OUT = "#60a5fa"
    DIR_LOCAL = "#a78bfa"
    DIR_UNKNOWN = "#6b7688"

    WARNING = "#fbbf24"
    CRITICAL = "#f87171"
    SUCCESS = "#34d399"

    # Protocol badge colors
    PROTO_TCP = "#60a5fa"
    PROTO_UDP = "#34d399"
    PROTO_DNS = "#c084fc"
    PROTO_ICMP = "#fbbf24"
    PROTO_ARP = "#f472b6"
    PROTO_OTHER = "#8b98a9"


PROTOCOL_COLORS = {
    "TCP": Palette.PROTO_TCP,
    "UDP": Palette.PROTO_UDP,
    "DNS": Palette.PROTO_DNS,
    "ICMP": Palette.PROTO_ICMP,
    "ARP": Palette.PROTO_ARP,
}


def protocol_color(protocol: str) -> str:
    return PROTOCOL_COLORS.get(protocol, Palette.PROTO_OTHER)


def _asset_root() -> Path:
    """Resource root for both source runs and PyInstaller bundles."""
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle is not None:  # frozen (PyInstaller)
        return Path(bundle)
    return Path(__file__).resolve().parents[3]


def load_stylesheet() -> str:
    """Read and return assets/styles/dark.qss."""
    qss_path = _asset_root() / "assets" / "styles" / "dark.qss"
    if qss_path.exists():
        return qss_path.read_text(encoding="utf-8")
    return ""
