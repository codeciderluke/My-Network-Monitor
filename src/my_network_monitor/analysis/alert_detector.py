"""Simple threshold-based alert detection."""

from __future__ import annotations

from datetime import datetime

from my_network_monitor.domain.alert import Alert, AlertSeverity
from my_network_monitor.domain.traffic_snapshot import TrafficSnapshot


class AlertDetector:
    """Inspect snapshots and raise alerts when thresholds are exceeded."""

    def __init__(
        self,
        high_upload_bps: float = 5 * 1024 * 1024,
        high_download_bps: float = 50 * 1024 * 1024,
        packet_drop_threshold: int = 1000,
    ) -> None:
        self._high_upload = high_upload_bps
        self._high_download = high_download_bps
        self._drop_threshold = packet_drop_threshold
        self._last_dropped = 0

    def evaluate(self, snapshot: TrafficSnapshot, now: datetime) -> list[Alert]:
        """Return the list of alerts raised from the snapshot."""
        alerts: list[Alert] = []

        if snapshot.upload_bytes_per_second >= self._high_upload:
            alerts.append(
                Alert(
                    timestamp=now,
                    severity=AlertSeverity.WARNING,
                    message="High upload traffic",
                    detail=f"{snapshot.upload_bytes_per_second / 1024 / 1024:.1f} MB/s",
                )
            )
        if snapshot.download_bytes_per_second >= self._high_download:
            alerts.append(
                Alert(
                    timestamp=now,
                    severity=AlertSeverity.WARNING,
                    message="High download traffic",
                    detail=f"{snapshot.download_bytes_per_second / 1024 / 1024:.1f} MB/s",
                )
            )
        new_drops = snapshot.dropped_packets - self._last_dropped
        if new_drops >= self._drop_threshold:
            alerts.append(
                Alert(
                    timestamp=now,
                    severity=AlertSeverity.CRITICAL,
                    message="Packet drops detected",
                    detail=f"+{new_drops} (total {snapshot.dropped_packets})",
                )
            )
        self._last_dropped = snapshot.dropped_packets
        return alerts
