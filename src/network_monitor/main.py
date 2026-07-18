"""Application entry point: python -m network_monitor.main"""

from __future__ import annotations

import argparse
import logging
import sys

from network_monitor.config import AppConfig
from network_monitor.logging_config import setup_logging

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Real-time network traffic monitor")
    parser.add_argument(
        "--demo", action="store_true", help="Run the UI with synthetic traffic (no capture)"
    )
    parser.add_argument("--config", default=None, help="Path to the TOML configuration file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = AppConfig.load(args.config)
    setup_logging(config.logging.level, config.logging.file_path)
    logger.info("Starting application (demo=%s)", args.demo)

    # Import Qt lazily for headless tests.
    from PySide6.QtWidgets import QApplication

    from network_monitor.ui.main_window import MainWindow
    from network_monitor.ui.theme import load_stylesheet

    app = QApplication(sys.argv)
    app.setApplicationName("Network Traffic Monitor")
    app.setStyleSheet(load_stylesheet())

    window = MainWindow(config, demo=args.demo)
    window.show()

    if not args.demo:
        _warn_if_no_capture(window)

    return app.exec()


def _warn_if_no_capture(window: object) -> None:
    """Check whether Npcap/Scapy is available and notify the user at launch."""
    from PySide6.QtWidgets import QMessageBox

    message: str | None = None
    try:
        import scapy.all  # noqa: F401

        from network_monitor.capture.scapy_capture_service import is_pcap_available

        if not is_pcap_available():
            message = (
                "Npcap is not installed, so real packet capture is unavailable.\n\n"
                "Install Npcap from https://npcap.com (enable the "
                "'WinPcap API-compatible mode' option) and restart.\n\n"
                "To preview the UI without capture, run with the --demo option."
            )
    except Exception:
        message = (
            "Scapy/Npcap could not be loaded.\n\n"
            "Real capture requires Npcap to be installed and administrator privileges.\n"
            "To preview the UI only, run with the --demo option."
        )

    if message is not None:
        logger.warning("Capture unavailable: %s", message.splitlines()[0])
        QMessageBox.information(window, "Packet Capture Setup", message)  # type: ignore[arg-type]


if __name__ == "__main__":
    raise SystemExit(main())
