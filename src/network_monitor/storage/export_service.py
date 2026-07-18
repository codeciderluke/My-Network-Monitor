"""CSV / JSON Lines export."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from pathlib import Path

from network_monitor.domain.packet_record import PacketRecord
from network_monitor.utils.formatters import format_port

_FIELDS = [
    "timestamp",
    "direction",
    "interface_name",
    "protocol",
    "process_name",
    "process_id",
    "source_ip",
    "source_port",
    "destination_ip",
    "destination_port",
    "length",
    "domain_name",
    "summary",
]


def _record_to_dict(record: PacketRecord) -> dict[str, object]:
    return {
        "timestamp": record.timestamp.isoformat(),
        "direction": str(record.direction),
        "interface_name": record.interface_name,
        "protocol": record.protocol,
        "process_name": record.process_name or "",
        "process_id": record.process_id,
        "source_ip": record.source_ip,
        "source_port": format_port(record.source_port),
        "destination_ip": record.destination_ip,
        "destination_port": format_port(record.destination_port),
        "length": record.length,
        "domain_name": record.domain_name or "",
        "summary": record.summary,
    }


def export_csv(records: Iterable[PacketRecord], path: str | Path) -> int:
    """Write records to CSV and return the number saved."""
    count = 0
    with Path(path).open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(_record_to_dict(record))
            count += 1
    return count


def export_jsonl(records: Iterable[PacketRecord], path: str | Path) -> int:
    """Write records to JSON Lines and return the number saved."""
    count = 0
    with Path(path).open("w", encoding="utf-8") as fp:
        for record in records:
            fp.write(json.dumps(_record_to_dict(record), ensure_ascii=False))
            fp.write("\n")
            count += 1
    return count
