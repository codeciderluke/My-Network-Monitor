"""Domain models."""

from my_network_monitor.domain.alert import Alert, AlertSeverity
from my_network_monitor.domain.network_interface import NetworkInterface
from my_network_monitor.domain.packet_record import PacketRecord, TrafficDirection
from my_network_monitor.domain.traffic_snapshot import TrafficSnapshot

__all__ = [
    "Alert",
    "AlertSeverity",
    "NetworkInterface",
    "PacketRecord",
    "TrafficDirection",
    "TrafficSnapshot",
]
