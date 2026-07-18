"""Abstract capture service interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable


class CaptureService(ABC):
    """Packet capture backend interface."""

    @abstractmethod
    def list_interfaces(self) -> list[str]:
        """List of names of interfaces available for capture."""
        raise NotImplementedError

    @abstractmethod
    def start(
        self,
        interface_name: str,
        packet_callback: Callable[[object], None],
        bpf_filter: str | None = None,
    ) -> None:
        """Start capturing. The callback is invoked on the capture thread."""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """Stop capturing and release resources."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Whether a capture is currently running."""
        raise NotImplementedError
