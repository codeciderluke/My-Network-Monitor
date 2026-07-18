"""Tests for the Scapy capture service pre-flight Npcap check."""

from __future__ import annotations

import pytest

pytest.importorskip("scapy.all")

import my_network_monitor.capture.scapy_capture_service as svc_mod
from my_network_monitor.capture.scapy_capture_service import (
    CaptureError,
    ScapyCaptureService,
    is_pcap_available,
)


def test_is_pcap_available_returns_bool() -> None:
    assert isinstance(is_pcap_available(), bool)


def test_start_raises_when_pcap_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """When Npcap is unavailable, start() fails fast instead of dying async."""
    monkeypatch.setattr(svc_mod, "is_pcap_available", lambda: False)
    service = ScapyCaptureService()

    with pytest.raises(CaptureError):
        service.start("eth0", lambda _packet: None)

    # Failed start must not stay running.
    assert not service.is_running


def test_start_rejects_double_start(monkeypatch: pytest.MonkeyPatch) -> None:
    """Starting an already-running capture raises CaptureError."""
    monkeypatch.setattr(svc_mod, "is_pcap_available", lambda: True)
    service = ScapyCaptureService()
    service._sniffer = object()  # simulate an active sniffer

    with pytest.raises(CaptureError):
        service.start("eth0", lambda _packet: None)
