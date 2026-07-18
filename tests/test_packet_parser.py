"""Packet parser tests (requires scapy; skipped if unavailable)."""

from __future__ import annotations

from datetime import datetime

import pytest

scapy = pytest.importorskip("scapy.all")

from network_monitor.analysis.packet_parser import PacketParser  # noqa: E402
from network_monitor.domain.packet_record import TrafficDirection  # noqa: E402

LOCAL_IP = "192.168.0.24"
REMOTE_IP = "142.250.196.132"


@pytest.fixture
def parser() -> PacketParser:
    return PacketParser("test0", {LOCAL_IP})


def _now() -> datetime:
    return datetime(2026, 7, 18, 12, 0, 0)


def test_parse_tcp_outbound(parser: PacketParser) -> None:
    from scapy.all import IP, TCP

    packet = IP(src=LOCAL_IP, dst=REMOTE_IP) / TCP(sport=50000, dport=443, flags="S")
    record = parser.parse(packet, _now())
    assert record is not None
    assert record.protocol == "TCP"
    assert record.direction == TrafficDirection.OUTBOUND
    assert record.source_port == 50000
    assert record.destination_port == 443


def test_parse_tcp_inbound(parser: PacketParser) -> None:
    from scapy.all import IP, TCP

    packet = IP(src=REMOTE_IP, dst=LOCAL_IP) / TCP(sport=443, dport=50000)
    record = parser.parse(packet, _now())
    assert record is not None
    assert record.direction == TrafficDirection.INBOUND


def test_parse_udp(parser: PacketParser) -> None:
    from scapy.all import IP, UDP

    packet = IP(src=LOCAL_IP, dst=REMOTE_IP) / UDP(sport=50000, dport=12345)
    record = parser.parse(packet, _now())
    assert record is not None
    assert record.protocol == "UDP"


def test_parse_dns(parser: PacketParser) -> None:
    from scapy.all import DNS, DNSQR, IP, UDP

    packet = (
        IP(src=LOCAL_IP, dst="8.8.8.8")
        / UDP(sport=50000, dport=53)
        / DNS(rd=1, qd=DNSQR(qname="example.com"))
    )
    record = parser.parse(packet, _now())
    assert record is not None
    assert record.protocol == "DNS"
    assert record.domain_name == "example.com"


def test_parse_icmp(parser: PacketParser) -> None:
    from scapy.all import ICMP, IP

    packet = IP(src=LOCAL_IP, dst=REMOTE_IP) / ICMP()
    record = parser.parse(packet, _now())
    assert record is not None
    assert record.protocol == "ICMP"


def test_parse_ipv6(parser: PacketParser) -> None:
    from scapy.all import TCP, IPv6

    parser.update_local_ips({"fe80::1"})
    packet = IPv6(src="fe80::1", dst="2001:4860:4860::8888") / TCP(sport=5000, dport=443)
    record = parser.parse(packet, _now())
    assert record is not None
    assert record.direction == TrafficDirection.OUTBOUND


def test_parse_arp(parser: PacketParser) -> None:
    from scapy.all import ARP

    packet = ARP(psrc=LOCAL_IP, pdst=REMOTE_IP)
    record = parser.parse(packet, _now())
    assert record is not None
    assert record.protocol == "ARP"


def test_non_ip_returns_none(parser: PacketParser) -> None:
    from scapy.all import Ether

    record = parser.parse(Ether(), _now())
    assert record is None
