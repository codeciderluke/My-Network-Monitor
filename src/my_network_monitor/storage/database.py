"""SQLite schema and connection management."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS traffic_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    interface_name TEXT NOT NULL,
    direction TEXT NOT NULL,
    protocol TEXT NOT NULL,
    source_ip TEXT,
    source_port INTEGER,
    destination_ip TEXT,
    destination_port INTEGER,
    packet_length INTEGER NOT NULL,
    process_name TEXT,
    process_id INTEGER,
    domain_name TEXT,
    summary TEXT
);
CREATE INDEX IF NOT EXISTS idx_traffic_timestamp ON traffic_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_traffic_protocol ON traffic_log(protocol);
CREATE INDEX IF NOT EXISTS idx_traffic_destination
    ON traffic_log(destination_ip, destination_port);
"""


def connect(database_path: str | Path) -> sqlite3.Connection:
    """Connect to the DB file and ensure the schema exists."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn
