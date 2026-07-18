"""Active connection tracking (5-tuple-based expiry management)."""

from __future__ import annotations

import threading
import time

from network_monitor.domain.packet_record import PacketRecord

_ConnKey = tuple[str, int | None, str, int | None]


class ConnectionTracker:
    """Track recently active connections and expire stale ones."""

    def __init__(self, ttl_seconds: float = 30.0) -> None:
        self._lock = threading.Lock()
        self._connections: dict[_ConnKey, float] = {}
        self._ttl = ttl_seconds

    def observe(self, record: PacketRecord, now: float) -> None:
        """Observe a packet and update the connection's last-activity time."""
        if record.protocol not in ("TCP", "UDP", "DNS"):
            return
        key: _ConnKey = (
            record.source_ip,
            record.source_port,
            record.destination_ip,
            record.destination_port,
        )
        with self._lock:
            self._connections[key] = now

    def expire(self, now: float) -> None:
        """Remove connections whose TTL has elapsed."""
        cutoff = now - self._ttl
        with self._lock:
            expired = [k for k, ts in self._connections.items() if ts < cutoff]
            for key in expired:
                del self._connections[key]

    def active_count(self) -> int:
        with self._lock:
            return len(self._connections)

    def clear(self) -> None:
        with self._lock:
            self._connections.clear()

    def maybe_expire(self, now: float | None = None) -> None:
        """Convenience method: expire based on the current time."""
        self.expire(now if now is not None else time.monotonic())
