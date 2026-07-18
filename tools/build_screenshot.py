"""Render a demo-mode screenshot of the app for the README.

Run:  python tools/build_screenshot.py [output.png]
Loads system fonts explicitly so text renders in a headless environment.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QEvent, QTimer
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from my_network_monitor.config import AppConfig
from my_network_monitor.ui.main_window import MainWindow
from my_network_monitor.ui.theme import load_stylesheet

_FONT_FILES = (
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/malgun.ttf",  # Korean fallback for localized interface names
)


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/screenshot.png")
    out.parent.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    for font_file in _FONT_FILES:
        if Path(font_file).exists():
            QFontDatabase.addApplicationFont(font_file)
    app.setStyleSheet(load_stylesheet())

    window = MainWindow(AppConfig(), demo=True)
    window.resize(1600, 920)
    window.show()

    def capture() -> None:
        window._controller._emit_snapshot()
        app.processEvents()
        # Flush deferred widget deletions so rank lists don't overlap.
        app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        window.grab().save(str(out))
        print(f"Wrote {out.resolve()}")
        os._exit(0)

    QTimer.singleShot(3000, capture)
    app.exec()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
