"""Alert detection tests."""

from datetime import datetime

from my_network_monitor.analysis.alert_detector import AlertDetector
from my_network_monitor.domain.alert import AlertSeverity
from my_network_monitor.domain.traffic_snapshot import TrafficSnapshot


def test_high_upload_triggers_warning() -> None:
    detector = AlertDetector(high_upload_bps=1_000_000)
    snapshot = TrafficSnapshot(upload_bytes_per_second=2_000_000)
    alerts = detector.evaluate(snapshot, datetime.now())
    assert len(alerts) == 1
    assert alerts[0].severity == AlertSeverity.WARNING


def test_no_alert_when_below_threshold() -> None:
    detector = AlertDetector(high_upload_bps=1_000_000)
    snapshot = TrafficSnapshot(upload_bytes_per_second=500_000)
    assert detector.evaluate(snapshot, datetime.now()) == []


def test_packet_drop_alert() -> None:
    detector = AlertDetector(packet_drop_threshold=100)
    snapshot = TrafficSnapshot(dropped_packets=200)
    alerts = detector.evaluate(snapshot, datetime.now())
    assert any(a.severity == AlertSeverity.CRITICAL for a in alerts)
