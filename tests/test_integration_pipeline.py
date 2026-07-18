"""Capture pipeline integration tests (fake capture service; requires scapy)."""

from __future__ import annotations

import queue
import threading
import time
from collections.abc import Callable
from datetime import datetime

import pytest

pytest.importorskip("scapy.all")

from my_network_monitor.analysis.connection_tracker import ConnectionTracker
from my_network_monitor.analysis.packet_parser import PacketParser
from my_network_monitor.analysis.process_resolver import ProcessResolver
from my_network_monitor.analysis.traffic_aggregator import TrafficAggregator
from my_network_monitor.capture.capture_service import CaptureService
from my_network_monitor.capture.capture_worker import PacketPipeline
from my_network_monitor.domain.packet_record import TrafficDirection

LOCAL_IP = "192.168.0.24"
REMOTE_IP = "142.250.196.132"


def _build_packets(count: int) -> list[object]:
    """List of scapy TCP packets alternating between inbound and outbound."""
    from scapy.all import IP, TCP

    packets: list[object] = []
    for i in range(count):
        if i % 2 == 0:
            packets.append(IP(src=LOCAL_IP, dst=REMOTE_IP) / TCP(sport=50000 + i, dport=443))
        else:
            packets.append(IP(src=REMOTE_IP, dst=LOCAL_IP) / TCP(sport=443, dport=50000 + i))
    return packets


class FakeCaptureService(CaptureService):
    """Capture service that pushes packets via callback without real Npcap."""

    def __init__(self, packets: list[object]) -> None:
        self._packets = packets
        self._callback: Callable[[object], None] | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def list_interfaces(self) -> list[str]:
        return ["fake0"]

    def start(
        self,
        interface_name: str,
        packet_callback: Callable[[object], None],
        bpf_filter: str | None = None,
    ) -> None:
        self._callback = packet_callback
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        assert self._callback is not None
        for packet in self._packets:
            self._callback(packet)

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    @property
    def is_running(self) -> bool:
        return self._running


def _make_pipeline(iface: str = "fake0") -> tuple[PacketPipeline, TrafficAggregator]:
    parser = PacketParser(iface, {LOCAL_IP})
    aggregator = TrafficAggregator()
    pipeline = PacketPipeline(parser, aggregator, ProcessResolver(), ConnectionTracker())
    return pipeline, aggregator


def _collect(pipeline: PacketPipeline, expected: int, timeout: float = 5.0) -> list[object]:
    collected: list[object] = []
    deadline = time.monotonic() + timeout
    while len(collected) < expected and time.monotonic() < deadline:
        collected.extend(pipeline.drain_ui(1000))
        if len(collected) < expected:
            time.sleep(0.02)
    return collected


def test_capture_start_stop_end_to_end() -> None:
    """The full path from capture start to parsing to the UI queue works."""
    pipeline, aggregator = _make_pipeline()
    service = FakeCaptureService(_build_packets(100))

    pipeline.start()
    service.start("fake0", pipeline.enqueue_packet)

    records = _collect(pipeline, expected=100)

    service.stop()
    pipeline.stop()

    assert len(records) == 100
    snapshot = aggregator.snapshot(1.0)
    assert snapshot.total_download_bytes > 0
    assert snapshot.total_upload_bytes > 0
    assert snapshot.protocol_counts.get("TCP") == 100


def test_start_stop_repeated_without_error() -> None:
    """Repeated start/stop cycles raise no exceptions (spec Phase 3)."""
    pipeline, _ = _make_pipeline()
    for _ in range(3):
        pipeline.start()
        service = FakeCaptureService(_build_packets(20))
        service.start("fake0", pipeline.enqueue_packet)
        _collect(pipeline, expected=20, timeout=3.0)
        service.stop()
        pipeline.stop()
    assert pipeline._thread is None


def test_parser_worker_clean_shutdown() -> None:
    """The parser worker thread shuts down cleanly and the raw queue drains."""
    pipeline, _ = _make_pipeline()
    pipeline.start()
    thread = pipeline._thread
    assert thread is not None and thread.is_alive()

    pipeline.stop()
    assert pipeline._thread is None
    assert not thread.is_alive()


def test_queue_saturation_increments_drop_counter() -> None:
    """When the raw queue fills up, the drop counter increases and capture continues."""
    pipeline, _ = _make_pipeline()
    # Saturate: small queue, no consumer.
    pipeline._raw_queue = queue.Queue(maxsize=5)

    for _ in range(20):
        pipeline.enqueue_packet(object())

    assert pipeline.dropped_packets == 15


def test_interface_change_updates_direction() -> None:
    """Interface/local IP changes are reflected in parse results (direction/interface name)."""
    from scapy.all import IP, TCP

    parser = PacketParser("wifi0", {LOCAL_IP})
    packet = IP(src=LOCAL_IP, dst=REMOTE_IP) / TCP(sport=50000, dport=443)

    first = parser.parse(packet, datetime(2026, 7, 18, 12, 0, 0))
    assert first is not None
    assert first.interface_name == "wifi0"
    assert first.direction == TrafficDirection.OUTBOUND

    # Switch interface and local IPs.
    parser.set_interface("eth0")
    parser.update_local_ips({REMOTE_IP})

    second = parser.parse(packet, datetime(2026, 7, 18, 12, 0, 0))
    assert second is not None
    assert second.interface_name == "eth0"
    # REMOTE_IP is now local, so direction reverses.
    assert second.direction == TrafficDirection.INBOUND
