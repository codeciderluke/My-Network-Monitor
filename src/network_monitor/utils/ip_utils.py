"""IP address classification utilities."""

from __future__ import annotations

import ipaddress


def is_local_address(ip: str, local_ips: set[str]) -> bool:
    """Determine whether the given IP is a local interface address."""
    return ip in local_ips


def is_loopback(ip: str) -> bool:
    """Whether the address is a loopback address."""
    try:
        return ipaddress.ip_address(ip).is_loopback
    except ValueError:
        return False


def is_private(ip: str) -> bool:
    """Whether the address is a private address."""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def is_valid_ip(ip: str) -> bool:
    """Whether the string is a valid IP address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False
