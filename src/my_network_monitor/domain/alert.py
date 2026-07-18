"""Alert domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AlertSeverity(StrEnum):
    """Alert severity."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(slots=True)
class Alert:
    """Detected alert event."""

    timestamp: datetime
    severity: AlertSeverity
    message: str
    detail: str = ""
