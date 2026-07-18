"""Scapy packet -> PacketRecord converter."""

from __future__ import annotations

import logging
from datetime import datetime

from network_monitor.domain.packet_record import PacketRecord, TrafficDirection
from network_monitor.utils.ip_utils import is_loopback

logger = logging.getLogger(__name__)

# ICMP type summaries
_ICMP_TYPES = {
    0: "echo-reply",
    3: "dest-unreachable",
    5: "redirect",
    8: "echo-request",
    11: "time-exceeded",
}


class PacketParser:
    """Convert a single Scapy packet into a PacketRecord."""

    def __init__(self, interface_name: str, local_ips: set[str]) -> None:
        self._interface_name = interface_name
        self._local_ips = local_ips

    def update_local_ips(self, local_ips: set[str]) -> None:
        self._local_ips = local_ips

    def set_interface(self, interface_name: str) -> None:
        self._interface_name = interface_name

    def parse(
        self,
        packet: object,
        timestamp: datetime,
        store_raw: bool = False,
    ) -> PacketRecord | None:
        """Parse a Scapy packet. Returns None for packets outside the target scope."""
        try:
            return self._parse_inner(packet, timestamp, store_raw)
        except Exception:
            logger.debug("Packet parsing failed", exc_info=True)
            return None

    def _parse_inner(
        self, packet: object, timestamp: datetime, store_raw: bool
    ) -> PacketRecord | None:
        from scapy.layers.inet import ICMP, IP, TCP, UDP
        from scapy.layers.inet6 import IPv6
        from scapy.layers.l2 import ARP

        length = len(packet)  # type: ignore[arg-type]
        raw = bytes(packet) if store_raw else None  # type: ignore[call-overload]

        # --- ARP ---
        if packet.haslayer(ARP):  # type: ignore[attr-defined]
            arp = packet[ARP]  # type: ignore[index]
            return PacketRecord(
                timestamp=timestamp,
                interface_name=self._interface_name,
                direction=TrafficDirection.UNKNOWN,
                protocol="ARP",
                source_ip=arp.psrc,
                destination_ip=arp.pdst,
                source_port=None,
                destination_port=None,
                length=length,
                summary=f"ARP {arp.psrc} → {arp.pdst}",
                raw_bytes=raw,
            )

        # --- IP layer ---
        if packet.haslayer(IP):  # type: ignore[attr-defined]
            ip = packet[IP]  # type: ignore[index]
            src_ip, dst_ip = ip.src, ip.dst
        elif packet.haslayer(IPv6):  # type: ignore[attr-defined]
            ip6 = packet[IPv6]  # type: ignore[index]
            src_ip, dst_ip = ip6.src, ip6.dst
        else:
            return None

        direction = self._resolve_direction(src_ip, dst_ip)
        src_port: int | None = None
        dst_port: int | None = None
        domain_name: str | None = None

        protocol = "IP"
        summary = ""

        if packet.haslayer(TCP):  # type: ignore[attr-defined]
            tcp = packet[TCP]  # type: ignore[index]
            src_port, dst_port = int(tcp.sport), int(tcp.dport)
            protocol = "TCP"
            summary = f"TCP {self._flag_str(tcp)} {src_port}→{dst_port}"
        elif packet.haslayer(UDP):  # type: ignore[attr-defined]
            udp = packet[UDP]  # type: ignore[index]
            src_port, dst_port = int(udp.sport), int(udp.dport)
            protocol = "UDP"
            summary = f"UDP {src_port}→{dst_port}"
            domain_name = self._extract_dns(packet)
            if domain_name is not None or src_port == 53 or dst_port == 53:
                protocol = "DNS"
                summary = f"DNS {domain_name or 'query'}"
        elif packet.haslayer(ICMP):  # type: ignore[attr-defined]
            icmp = packet[ICMP]  # type: ignore[index]
            protocol = "ICMP"
            summary = f"ICMP {self._icmp_str(int(icmp.type))}"

        if not summary:
            summary = f"{protocol} {src_ip} → {dst_ip}"

        return PacketRecord(
            timestamp=timestamp,
            interface_name=self._interface_name,
            direction=direction,
            protocol=protocol,
            source_ip=src_ip,
            destination_ip=dst_ip,
            source_port=src_port,
            destination_port=dst_port,
            length=length,
            domain_name=domain_name,
            summary=summary,
            raw_bytes=raw,
        )

    def _resolve_direction(self, src_ip: str, dst_ip: str) -> TrafficDirection:
        src_local = src_ip in self._local_ips or is_loopback(src_ip)
        dst_local = dst_ip in self._local_ips or is_loopback(dst_ip)
        if src_local and dst_local:
            return TrafficDirection.LOCAL
        if src_local:
            return TrafficDirection.OUTBOUND
        if dst_local:
            return TrafficDirection.INBOUND
        return TrafficDirection.UNKNOWN

    @staticmethod
    def _flag_str(tcp: object) -> str:
        try:
            return str(tcp.flags)  # type: ignore[attr-defined]
        except Exception:
            return ""

    @staticmethod
    def _icmp_str(icmp_type: int) -> str:
        return _ICMP_TYPES.get(icmp_type, f"type-{icmp_type}")

    @staticmethod
    def _extract_dns(packet: object) -> str | None:
        try:
            from scapy.layers.dns import DNS

            if not packet.haslayer(DNS):  # type: ignore[attr-defined]
                return None
            dns = packet[DNS]  # type: ignore[index]
            # qdcount unreliable pre-serialization; read qd directly.
            question = getattr(dns, "qd", None)
            if question is None:
                return None
            # scapy 2.7+: qd may be a PacketListField.
            if isinstance(question, list):
                if not question:
                    return None
                question = question[0]
            qname = getattr(question, "qname", None)
            if qname is None:
                return None
            if isinstance(qname, bytes):
                return qname.rstrip(b".").decode("utf-8", "replace")
            return str(qname).rstrip(".")
        except Exception:
            return None
