"""Capture-to-parse pipeline worker."""

from __future__ import annotations

import contextlib
import logging
import queue
import threading
from collections.abc import Callable
from datetime import datetime
from typing import Any

from my_network_monitor.analysis.connection_tracker import ConnectionTracker
from my_network_monitor.analysis.packet_parser import PacketParser
from my_network_monitor.analysis.process_resolver import ProcessResolver
from my_network_monitor.analysis.traffic_aggregator import TrafficAggregator
from my_network_monitor.config import (
    PARSED_QUEUE_MAXSIZE,
    RAW_QUEUE_MAXSIZE,
)
from my_network_monitor.domain.packet_record import PacketRecord

logger = logging.getLogger(__name__)

StorageSink = Callable[[PacketRecord], None]


class PacketPipeline:
    """raw queue -> parser thread -> parsed queue / aggregation / storage."""

    def __init__(
        self,
        parser: PacketParser,
        aggregator: TrafficAggregator,
        process_resolver: ProcessResolver,
        connection_tracker: ConnectionTracker,
        store_raw: bool = False,
    ) -> None:
        self._parser = parser
        self._aggregator = aggregator
        self._process_resolver = process_resolver
        self._connection_tracker = connection_tracker
        self._store_raw = store_raw

        self._raw_queue: queue.Queue[tuple[object, datetime]] = queue.Queue(
            maxsize=RAW_QUEUE_MAXSIZE
        )
        self._parsed_queue: queue.Queue[PacketRecord] = queue.Queue(maxsize=PARSED_QUEUE_MAXSIZE)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._dropped = 0
        self._storage_sink: StorageSink | None = None

    # Capture callback (capture thread)
    def enqueue_packet(self, packet: object) -> None:
        """Capture callback: stamp the timestamp and enqueue immediately."""
        try:
            self._raw_queue.put_nowait((packet, datetime.now()))
        except queue.Full:
            self._dropped += 1

    def set_storage_sink(self, sink: StorageSink | None) -> None:
        self._storage_sink = sink

    @property
    def dropped_packets(self) -> int:
        return self._dropped

    def reset_dropped(self) -> None:
        self._dropped = 0

    # Parser thread
    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="parser-worker", daemon=True)
        self._thread.start()
        logger.info("Parser worker started")

    def stop(self, timeout: float = 3.0) -> None:
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=timeout)
        self._thread = None
        _drain(self._raw_queue)
        logger.info("Parser worker stopped")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                packet, timestamp = self._raw_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            self._process(packet, timestamp)

    def _process(self, packet: object, timestamp: datetime) -> None:
        record = self._parser.parse(packet, timestamp, store_raw=self._store_raw)
        if record is None:
            return
        self._process_resolver.resolve(record)
        self._aggregator.add(record)
        self._connection_tracker.observe(record, timestamp.timestamp())
        self._aggregator.set_dropped(self._dropped)

        if self._storage_sink is not None:
            self._storage_sink(record)

        # UI queue full: aggregation already applied, drop detail log only.
        with contextlib.suppress(queue.Full):
            self._parsed_queue.put_nowait(record)

    def inject_record(self, record: PacketRecord) -> None:
        """Inject a complete record near the end of the pipeline (demo/tests)."""
        self._aggregator.add(record)
        self._connection_tracker.observe(record, record.timestamp.timestamp())
        with contextlib.suppress(queue.Full):
            self._parsed_queue.put_nowait(record)

    # UI consumption (UI thread)
    def drain_ui(self, max_items: int) -> list[PacketRecord]:
        """Pop up to max_items records for UI updates."""
        items: list[PacketRecord] = []
        for _ in range(max_items):
            try:
                items.append(self._parsed_queue.get_nowait())
            except queue.Empty:
                break
        return items


def _drain(q: queue.Queue[Any]) -> None:
    try:
        while True:
            q.get_nowait()
    except queue.Empty:
        pass
