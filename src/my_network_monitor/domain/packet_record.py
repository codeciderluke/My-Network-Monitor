"""Single packet metadata record."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TrafficDirection(StrEnum):
    """Traffic direction."""

    INBOUND = "IN"
    OUTBOUND = "OUT"
    LOCAL = "LOCAL"
    UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class PacketRecord:
    """Metadata for a single parsed packet."""

    timestamp: datetime
    interface_name: str
    direction: TrafficDirection
    protocol: str
    source_ip: str
    destination_ip: str
    source_port: int | None
    destination_port: int | None
    length: int
    process_name: str | None = None
    process_id: int | None = None
    domain_name: str | None = None
    summary: str = ""
    raw_bytes: bytes | None = None
