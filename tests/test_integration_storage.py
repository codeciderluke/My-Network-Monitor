"""Storage/export integration tests (SQLite batch persist, CSV/JSONL round-trip)."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import make_record
from network_monitor.domain.packet_record import TrafficDirection
from network_monitor.storage import database, export_service
from network_monitor.storage.traffic_repository import TrafficRepository


def test_sqlite_batch_persist(tmp_path: Path) -> None:
    """The storage worker writes 250 records to SQLite in batches."""
    db_path = tmp_path / "traffic.db"
    repo = TrafficRepository(str(db_path), batch_size=50, flush_interval_s=0.1)
    repo.start()

    for i in range(250):
        direction = TrafficDirection.INBOUND if i % 2 else TrafficDirection.OUTBOUND
        repo.submit(make_record(direction=direction, protocol="TCP"))

    repo.stop()  # stop() flushes remaining queue.
    assert repo.last_error is None

    conn = database.connect(str(db_path))
    try:
        count = conn.execute("SELECT COUNT(*) FROM traffic_log").fetchone()[0]
        protocols = {row[0] for row in conn.execute("SELECT DISTINCT protocol FROM traffic_log")}
    finally:
        conn.close()

    assert count == 250
    assert protocols == {"TCP"}


def test_sqlite_reopen_reads_data(tmp_path: Path) -> None:
    """Reopen the saved DB and verify fields round-trip (spec Phase 9)."""
    db_path = tmp_path / "reopen.db"
    repo = TrafficRepository(str(db_path), batch_size=10, flush_interval_s=0.1)
    repo.start()
    repo.submit(make_record(source_ip="10.0.0.5", destination_ip="8.8.8.8", protocol="DNS"))
    repo.stop()

    conn = database.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT protocol, source_ip, destination_ip FROM traffic_log LIMIT 1"
        ).fetchone()
    finally:
        conn.close()

    assert row == ("DNS", "10.0.0.5", "8.8.8.8")


def test_export_csv_roundtrip(tmp_path: Path) -> None:
    records = [make_record(protocol="TCP"), make_record(protocol="UDP")]
    path = tmp_path / "out.csv"

    count = export_service.export_csv(records, path)

    assert count == 2
    text = path.read_text(encoding="utf-8")
    assert "TCP" in text
    assert "UDP" in text
    assert text.count("\n") == 3  # header + 2 rows + trailing newline


def test_export_jsonl_roundtrip(tmp_path: Path) -> None:
    records = [make_record(protocol="TCP", destination_ip="1.1.1.1")]
    path = tmp_path / "out.jsonl"

    count = export_service.export_jsonl(records, path)

    assert count == 1
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["protocol"] == "TCP"
    assert parsed["destination_ip"] == "1.1.1.1"
