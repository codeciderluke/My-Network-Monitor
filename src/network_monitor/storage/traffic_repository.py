"""Storage worker responsible for batched persistence."""

from __future__ import annotations

import logging
import queue
import threading

from network_monitor.config import STORAGE_QUEUE_MAXSIZE
from network_monitor.domain.packet_record import PacketRecord
from network_monitor.storage import database

logger = logging.getLogger(__name__)

_INSERT_SQL = """
INSERT INTO traffic_log (
    timestamp, interface_name, direction, protocol,
    source_ip, source_port, destination_ip, destination_port,
    packet_length, process_name, process_id, domain_name, summary
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class TrafficRepository:
    """Threaded worker that batches queued PacketRecords into SQLite."""

    def __init__(
        self,
        database_path: str,
        batch_size: int = 100,
        flush_interval_s: float = 1.0,
    ) -> None:
        self._database_path = database_path
        self._batch_size = batch_size
        self._flush_interval = flush_interval_s
        self._queue: queue.Queue[PacketRecord] = queue.Queue(maxsize=STORAGE_QUEUE_MAXSIZE)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._error: str | None = None

    @property
    def last_error(self) -> str | None:
        return self._error

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="storage-worker", daemon=True)
        self._thread.start()
        logger.info("Storage worker started: %s", self._database_path)

    def submit(self, record: PacketRecord) -> None:
        """Enqueue a record for storage (dropped if the queue is full)."""
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            logger.debug("Storage queue full - dropping record")

    def stop(self, timeout: float = 3.0) -> None:
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=timeout)
        self._thread = None
        logger.info("Storage worker stopped")

    def _run(self) -> None:
        try:
            conn = database.connect(self._database_path)
        except Exception as exc:
            self._error = f"Failed to open DB: {exc}"
            logger.exception(self._error)
            return

        batch: list[tuple[object, ...]] = []
        try:
            while not self._stop_event.is_set() or not self._queue.empty():
                try:
                    record = self._queue.get(timeout=self._flush_interval)
                    batch.append(_to_row(record))
                except queue.Empty:
                    pass
                if len(batch) >= self._batch_size or (batch and self._queue.empty()):
                    self._flush(conn, batch)
                    batch = []
            if batch:
                self._flush(conn, batch)
        finally:
            conn.close()

    def _flush(self, conn: object, batch: list[tuple[object, ...]]) -> None:
        try:
            conn.executemany(_INSERT_SQL, batch)  # type: ignore[attr-defined]
            conn.commit()  # type: ignore[attr-defined]
        except Exception as exc:
            self._error = f"Storage failed: {exc}"
            logger.exception(self._error)


def _to_row(record: PacketRecord) -> tuple[object, ...]:
    return (
        record.timestamp.isoformat(),
        record.interface_name,
        str(record.direction),
        record.protocol,
        record.source_ip,
        record.source_port,
        record.destination_ip,
        record.destination_port,
        record.length,
        record.process_name,
        record.process_id,
        record.domain_name,
        record.summary,
    )
