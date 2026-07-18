"""Synthetic packet generator for demo mode (preview the UI without Npcap)."""

from __future__ import annotations

from datetime import datetime

from network_monitor.domain.packet_record import PacketRecord, TrafficDirection

_HOSTS = [
    ("142.250.196.132", "google.com", "chrome.exe", 4120),
    ("151.101.1.69", "reddit.com", "chrome.exe", 4120),
    ("140.82.112.3", "github.com", "Code.exe", 9812),
    ("8.8.8.8", "dns.google", "svchost.exe", 1044),
    ("13.107.42.14", "microsoft.com", "python.exe", 7723),
    ("104.16.132.229", "cloudflare.com", "firefox.exe", 3310),
]
_PROTOCOLS = ("TCP", "TCP", "TCP", "UDP", "DNS", "ICMP")
_LOCAL_IP = "192.168.0.24"


class DemoSource:
    """Builds varied synthetic packets from an index, without pseudo-random numbers."""

    def __init__(self) -> None:
        self._tick = 0

    def generate_batch(self, count: int) -> list[PacketRecord]:
        records: list[PacketRecord] = []
        now = datetime.now()
        for _ in range(count):
            records.append(self._make_record(now))
            self._tick += 1
        return records

    def _make_record(self, now: datetime) -> PacketRecord:
        host_ip, domain, proc, pid = _HOSTS[self._tick % len(_HOSTS)]
        protocol = _PROTOCOLS[self._tick % len(_PROTOCOLS)]
        inbound = self._tick % 3 != 0
        length = 64 + (self._tick * 137) % 1400
        if inbound:
            length = 200 + (self._tick * 311) % 8000  # downloads are larger

        direction = TrafficDirection.INBOUND if inbound else TrafficDirection.OUTBOUND
        src_ip, dst_ip = (host_ip, _LOCAL_IP) if inbound else (_LOCAL_IP, host_ip)
        port = 443 if protocol == "TCP" else 53 if protocol == "DNS" else 0
        summary = f"{protocol} {domain}" if protocol == "DNS" else f"{protocol} {domain}:{port}"

        return PacketRecord(
            timestamp=now,
            interface_name="Demo",
            direction=direction,
            protocol=protocol,
            source_ip=src_ip,
            destination_ip=dst_ip,
            source_port=(port if inbound else 50000 + self._tick % 10000),
            destination_port=(50000 + self._tick % 10000 if inbound else port),
            length=length,
            process_name=proc,
            process_id=pid,
            domain_name=domain if protocol == "DNS" else None,
            summary=summary,
        )
