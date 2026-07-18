"""Shared test fixtures and helpers."""

from __future__ import annotations

from datetime import datetime

from network_monitor.domain.packet_record import PacketRecord, TrafficDirection


def make_record(
    direction: TrafficDirection = TrafficDirection.INBOUND,
    protocol: str = "TCP",
    length: int = 1000,
    source_ip: str = "142.250.0.1",
    destination_ip: str = "192.168.0.24",
    source_port: int | None = 443,
    destination_port: int | None = 50000,
    process_name: str | None = "chrome.exe",
) -> PacketRecord:
    """Helper for building a PacketRecord for tests."""
    return PacketRecord(
        timestamp=datetime(2026, 7, 18, 12, 0, 0),
        interface_name="test0",
        direction=direction,
        protocol=protocol,
        source_ip=source_ip,
        destination_ip=destination_ip,
        source_port=source_port,
        destination_port=destination_port,
        length=length,
        process_name=process_name,
        summary=f"{protocol} test",
    )
