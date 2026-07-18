"""Network interface discovery service."""

from __future__ import annotations

import logging
import socket

import psutil

from network_monitor.capture.capture_service import CaptureService
from network_monitor.domain.network_interface import NetworkInterface

logger = logging.getLogger(__name__)


class InterfaceService:
    """Build the interface list from psutil and the capture backend."""

    def __init__(self, capture_service: CaptureService) -> None:
        self._capture_service = capture_service

    def list_interfaces(self) -> list[NetworkInterface]:
        """Return the interface list including name, IP, and status."""
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        capture_names = set(self._capture_service.list_interfaces())

        interfaces: list[NetworkInterface] = []
        for name, addr_list in addrs.items():
            ipv4 = [a.address for a in addr_list if a.family == socket.AF_INET]
            ipv6 = [a.address.split("%")[0] for a in addr_list if a.family == socket.AF_INET6]
            stat = stats.get(name)
            interfaces.append(
                NetworkInterface(
                    name=name,
                    description=name,
                    ipv4_addresses=ipv4,
                    ipv6_addresses=ipv6,
                    is_up=bool(stat.isup) if stat else False,
                )
            )

        interfaces.sort(key=_interface_sort_key, reverse=True)
        if capture_names:
            logger.debug("Capture backend interfaces: %s", capture_names)
        return interfaces

    def local_ips(self) -> set[str]:
        """Set of local IPs across all interfaces (used for direction resolution)."""
        result: set[str] = set()
        for iface in self.list_interfaces():
            result.update(iface.all_addresses)
        return result

    def default_interface(self) -> NetworkInterface | None:
        """First interface that is up and has an IPv4 address."""
        for iface in self.list_interfaces():
            if iface.is_up and iface.ipv4_addresses and not _is_loopback_name(iface.name):
                return iface
        interfaces = self.list_interfaces()
        return interfaces[0] if interfaces else None


def _interface_sort_key(iface: NetworkInterface) -> tuple[int, int, int]:
    return (
        int(iface.is_up),
        int(bool(iface.ipv4_addresses)),
        int(not _is_loopback_name(iface.name)),
    )


def _is_loopback_name(name: str) -> bool:
    lowered = name.lower()
    return "loopback" in lowered or lowered.startswith("lo")
