"""Aggregated traffic snapshot delivered to the UI periodically."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class TrafficSnapshot:
    """Aggregated traffic summary at a single point in time."""

    download_bytes_per_second: float = 0.0
    upload_bytes_per_second: float = 0.0
    total_download_bytes: int = 0
    total_upload_bytes: int = 0
    packets_per_second: int = 0
    active_connections: int = 0
    dropped_packets: int = 0
    protocol_counts: dict[str, int] = field(default_factory=dict)
    top_processes: list[tuple[str, int]] = field(default_factory=list)
    top_destinations: list[tuple[str, int]] = field(default_factory=list)
