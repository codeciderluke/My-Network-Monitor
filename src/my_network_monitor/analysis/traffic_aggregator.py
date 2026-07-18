"""Traffic aggregator: computes rate, totals, protocols, and top processes."""

from __future__ import annotations

import threading
from collections import Counter, deque

from my_network_monitor.config import HISTORY_SECONDS
from my_network_monitor.domain.packet_record import PacketRecord, TrafficDirection
from my_network_monitor.domain.traffic_snapshot import TrafficSnapshot


class TrafficAggregator:
    """Accumulate packets and periodically produce a TrafficSnapshot."""

    def __init__(self, history_seconds: int = HISTORY_SECONDS) -> None:
        self._lock = threading.Lock()

        # Totals (whole run)
        self._total_download = 0
        self._total_upload = 0

        # Interval (since last snapshot)
        self._interval_download = 0
        self._interval_upload = 0
        self._interval_packets = 0

        self._protocol_counts: Counter[str] = Counter()
        self._process_bytes: Counter[str] = Counter()
        self._destination_bytes: Counter[str] = Counter()

        self._download_history: deque[float] = deque(maxlen=history_seconds)
        self._upload_history: deque[float] = deque(maxlen=history_seconds)

        self._dropped_packets = 0
        self._active_connections = 0

    def add(self, record: PacketRecord) -> None:
        """Apply a single parsed packet to the aggregation."""
        with self._lock:
            self._interval_packets += 1
            self._protocol_counts[record.protocol] += 1
            self._destination_bytes[record.destination_ip] += record.length
            if record.process_name:
                self._process_bytes[record.process_name] += record.length

            if record.direction == TrafficDirection.INBOUND:
                self._total_download += record.length
                self._interval_download += record.length
            elif record.direction == TrafficDirection.OUTBOUND:
                self._total_upload += record.length
                self._interval_upload += record.length

    def set_dropped(self, dropped: int) -> None:
        with self._lock:
            self._dropped_packets = dropped

    def set_active_connections(self, count: int) -> None:
        with self._lock:
            self._active_connections = count

    def snapshot(self, elapsed_seconds: float) -> TrafficSnapshot:
        """Compute the rate since the last call and reset the interval counters."""
        elapsed = max(elapsed_seconds, 1e-6)
        with self._lock:
            download_rate = self._interval_download / elapsed
            upload_rate = self._interval_upload / elapsed
            packets_per_second = int(self._interval_packets / elapsed)

            self._download_history.append(download_rate)
            self._upload_history.append(upload_rate)

            snapshot = TrafficSnapshot(
                download_bytes_per_second=download_rate,
                upload_bytes_per_second=upload_rate,
                total_download_bytes=self._total_download,
                total_upload_bytes=self._total_upload,
                packets_per_second=packets_per_second,
                active_connections=self._active_connections,
                dropped_packets=self._dropped_packets,
                protocol_counts=dict(self._protocol_counts),
                top_processes=self._process_bytes.most_common(5),
                top_destinations=self._destination_bytes.most_common(5),
            )

            self._interval_download = 0
            self._interval_upload = 0
            self._interval_packets = 0
            return snapshot

    def history(self) -> tuple[list[float], list[float]]:
        """Copy of the recent (download, upload) history."""
        with self._lock:
            return list(self._download_history), list(self._upload_history)

    def reset(self) -> None:
        with self._lock:
            self._total_download = 0
            self._total_upload = 0
            self._interval_download = 0
            self._interval_upload = 0
            self._interval_packets = 0
            self._protocol_counts.clear()
            self._process_bytes.clear()
            self._destination_bytes.clear()
            self._download_history.clear()
            self._upload_history.clear()
            self._dropped_packets = 0
