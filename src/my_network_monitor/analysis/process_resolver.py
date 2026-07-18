"""Connection-table-based process mapping (psutil)."""

from __future__ import annotations

import logging
import threading

import psutil

from my_network_monitor.domain.packet_record import PacketRecord

logger = logging.getLogger(__name__)

# (protocol, ip, port) -> pid
_ConnKey = tuple[str, str, int]


class ProcessResolver:
    """Cache the psutil connection table to map PID/process name."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._conn_map: dict[_ConnKey, int] = {}
        self._name_cache: dict[int, str] = {}
        self._connection_count = 0

    def refresh(self) -> None:
        """Refresh the connection table cache (called periodically from a separate thread)."""
        conn_map: dict[_ConnKey, int] = {}
        count = 0
        try:
            connections = psutil.net_connections(kind="inet")
        except (psutil.AccessDenied, PermissionError):
            logger.warning("Connection table access denied (administrator privileges required)")
            return
        except Exception:
            logger.exception("Failed to query connection table")
            return

        for conn in connections:
            if not conn.laddr or conn.pid is None:
                continue
            count += 1
            proto = "TCP" if conn.type == 1 else "UDP"
            key = (proto, conn.laddr.ip, conn.laddr.port)
            conn_map[key] = conn.pid

        with self._lock:
            self._conn_map = conn_map
            self._connection_count = count

    @property
    def connection_count(self) -> int:
        with self._lock:
            return self._connection_count

    def resolve(self, record: PacketRecord) -> None:
        """Fill in the record's process name/PID in place."""
        pid = self._lookup_pid(record)
        if pid is None:
            return
        record.process_id = pid
        record.process_name = self._process_name(pid)

    def _lookup_pid(self, record: PacketRecord) -> int | None:
        proto = record.protocol if record.protocol in ("TCP", "UDP") else "TCP"
        if record.protocol == "DNS":
            proto = "UDP"
        candidates: list[_ConnKey] = []
        if record.source_port is not None:
            candidates.append((proto, record.source_ip, record.source_port))
        if record.destination_port is not None:
            candidates.append((proto, record.destination_ip, record.destination_port))
        with self._lock:
            for key in candidates:
                pid = self._conn_map.get(key)
                if pid is not None:
                    return pid
        return None

    def _process_name(self, pid: int) -> str | None:
        with self._lock:
            cached = self._name_cache.get(pid)
        if cached is not None:
            return cached
        try:
            name = psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
        with self._lock:
            self._name_cache[pid] = name
        return name

    def clear_name_cache(self) -> None:
        with self._lock:
            self._name_cache.clear()
