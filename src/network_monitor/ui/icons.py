"""SVG-based line icon set rendered to QIcons at runtime."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from network_monitor.ui.theme import Palette

# 24x24 viewBox, stroke-based icon body (color substituted via {c})
_STROKE = 'stroke="{c}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"'
_FILL = 'fill="{c}"'

_ICONS: dict[str, str] = {
    # App logo - network activity waveform
    "logo": f'<polyline points="22 12 18 12 15 21 9 3 6 12 2 12" {_STROKE}/>',
    "activity": f'<polyline points="22 12 18 12 15 21 9 3 6 12 2 12" {_STROKE}/>',
    "play": f'<polygon points="6 4 20 12 6 20 6 4" {_FILL}/>',
    "pause": (
        f'<rect x="6" y="5" width="4" height="14" rx="1.5" {_FILL}/>'
        f'<rect x="14" y="5" width="4" height="14" rx="1.5" {_FILL}/>'
    ),
    "stop": f'<rect x="6" y="6" width="12" height="12" rx="2.5" {_FILL}/>',
    "refresh": (
        f'<path d="M23 4v6h-6" {_STROKE}/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" {_STROKE}/>'
    ),
    "trash": (
        f'<polyline points="3 6 5 6 21 6" {_STROKE}/>'
        f'<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 '
        f'2-2h4a2 2 0 0 1 2 2v2" {_STROKE}/>'
    ),
    "copy": (
        f'<rect x="9" y="9" width="13" height="13" rx="2" {_STROKE}/>'
        f'<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" {_STROKE}/>'
    ),
    "file": (
        f'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" {_STROKE}/>'
        f'<polyline points="14 2 14 8 20 8" {_STROKE}/>'
    ),
    "braces": (
        f'<path d="M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5a2 2 0 0 0 2 2h1" '
        f"{_STROKE}/>"
        f'<path d="M16 3h1a2 2 0 0 1 2 2v5a2 2 0 0 1 2 2 2 2 0 0 1-2 2v5a2 2 0 0 1-2 2h-1" '
        f"{_STROKE}/>"
    ),
    "database": (
        f'<ellipse cx="12" cy="5" rx="9" ry="3" {_STROKE}/>'
        f'<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" {_STROKE}/>'
        f'<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" {_STROKE}/>'
    ),
    "download": (
        f'<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" {_STROKE}/>'
        f'<polyline points="7 10 12 15 17 10" {_STROKE}/>'
        f'<line x1="12" y1="15" x2="12" y2="3" {_STROKE}/>'
    ),
    "upload": (
        f'<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" {_STROKE}/>'
        f'<polyline points="17 8 12 3 7 8" {_STROKE}/>'
        f'<line x1="12" y1="3" x2="12" y2="15" {_STROKE}/>'
    ),
    "link": (
        f'<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" {_STROKE}/>'
        f'<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" {_STROKE}/>'
    ),
    "cpu": (
        f'<rect x="4" y="4" width="16" height="16" rx="2" {_STROKE}/>'
        f'<rect x="9" y="9" width="6" height="6" {_STROKE}/>'
        f'<path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3" {_STROKE}/>'
    ),
    "alert": (
        f'<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 '
        f'3.86a2 2 0 0 0-3.42 0z" {_STROKE}/>'
        f'<line x1="12" y1="9" x2="12" y2="13" {_STROKE}/>'
        f'<line x1="12" y1="17" x2="12.01" y2="17" {_STROKE}/>'
    ),
    "filter": (f'<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" {_STROKE}/>'),
    "globe": (
        f'<circle cx="12" cy="12" r="10" {_STROKE}/>'
        f'<line x1="2" y1="12" x2="22" y2="12" {_STROKE}/>'
        f'<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10'
        f' 15.3 15.3 0 0 1 4-10z" {_STROKE}/>'
    ),
    "chart": (
        f'<line x1="3" y1="21" x2="21" y2="21" {_STROKE}/>'
        f'<polyline points="4 15 9 10 13 13 20 6" {_STROKE}/>'
    ),
}


def _svg_document(name: str, color: str) -> bytes:
    body = _ICONS[name].format(c=color)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">{body}</svg>').encode()


def icon(name: str, color: str | None = None, size: int = 20) -> QIcon:
    """Create a QIcon from a name and color."""
    color = color or Palette.TEXT_SECONDARY
    renderer = QSvgRenderer(QByteArray(_svg_document(name, color)))
    ratio = 2  # render scale factor for high-DPI
    pixmap = QPixmap(size * ratio, size * ratio)
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return QIcon(pixmap)


def app_pixmap(size: int = 64) -> QPixmap:
    """Pixmap for the app/window icon (cyan logo)."""
    renderer = QSvgRenderer(QByteArray(_svg_document("logo", Palette.ACCENT)))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(size * 0.12, size * 0.12, size * 0.76, size * 0.76))
    painter.end()
    return pixmap
