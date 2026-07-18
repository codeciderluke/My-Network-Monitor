"""Capture service based on Scapy AsyncSniffer."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable

from my_network_monitor.capture.capture_service import CaptureService

logger = logging.getLogger(__name__)

_NPCAP_HELP = (
    "Npcap is not installed, so real packet capture is unavailable.\n\n"
    "Install Npcap from https://npcap.com (enable the "
    "'WinPcap API-compatible mode' option) and restart the application.\n\n"
    "To preview the UI without capture, launch with the --demo option."
)


class CaptureError(RuntimeError):
    """Failure to start or stop a capture."""


def is_pcap_available() -> bool:
    """Return whether a pcap provider (Npcap) is available for capture."""
    try:
        from scapy.all import conf
    except Exception:  # pragma: no cover - environment dependent
        return False
    if sys.platform == "win32":
        return bool(getattr(conf, "use_pcap", False))
    return True


class ScapyCaptureService(CaptureService):
    """Capture service wrapping Scapy's `AsyncSniffer`."""

    def __init__(self) -> None:
        self._sniffer: object | None = None

    def list_interfaces(self) -> list[str]:
        try:
            from scapy.arch import get_windows_if_list

            return [iface["name"] for iface in get_windows_if_list()]
        except Exception:
            try:
                from scapy.all import get_if_list

                return list(get_if_list())
            except Exception:
                logger.exception("Failed to query interface list")
                return []

    def start(
        self,
        interface_name: str,
        packet_callback: Callable[[object], None],
        bpf_filter: str | None = None,
    ) -> None:
        if self._sniffer is not None:
            raise CaptureError("A capture is already running.")

        # Npcap pre-flight check: catch missing driver before the async start.
        if not is_pcap_available():
            raise CaptureError(_NPCAP_HELP)

        try:
            from scapy.all import AsyncSniffer
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise CaptureError(
                "Could not load Scapy. Check the package and Npcap installation."
            ) from exc

        try:
            sniffer = AsyncSniffer(
                iface=interface_name,
                prn=packet_callback,
                store=False,
                filter=bpf_filter or None,
            )
            sniffer.start()
        except Exception as exc:
            raise CaptureError(f"Failed to start capture: {exc}") from exc

        self._sniffer = sniffer
        logger.info("Capture started: iface=%s filter=%s", interface_name, bpf_filter)

    def stop(self) -> None:
        if self._sniffer is None:
            return
        try:
            self._sniffer.stop()  # type: ignore[attr-defined]
        except Exception:
            logger.exception("Error while stopping capture")
        finally:
            self._sniffer = None
            logger.info("Capture stopped")

    @property
    def is_running(self) -> bool:
        return self._sniffer is not None
