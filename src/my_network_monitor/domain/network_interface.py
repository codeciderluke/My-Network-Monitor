"""Network interface information."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class NetworkInterface:
    """Network interface targeted for capture."""

    name: str
    description: str = ""
    ipv4_addresses: list[str] = field(default_factory=list)
    ipv6_addresses: list[str] = field(default_factory=list)
    is_up: bool = True

    @property
    def display_name(self) -> str:
        """Name to display in the combo box."""
        primary = self.ipv4_addresses[0] if self.ipv4_addresses else "no IPv4"
        label = self.description or self.name
        return f"{label}  ·  {primary}"

    @property
    def all_addresses(self) -> list[str]:
        """All IPv4 and IPv6 addresses."""
        return [*self.ipv4_addresses, *self.ipv6_addresses]
