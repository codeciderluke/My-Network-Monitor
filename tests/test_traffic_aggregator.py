"""Traffic aggregator tests."""

from conftest import make_record
from my_network_monitor.analysis.traffic_aggregator import TrafficAggregator
from my_network_monitor.domain.packet_record import TrafficDirection


def test_download_upload_rate() -> None:
    agg = TrafficAggregator()
    agg.add(make_record(direction=TrafficDirection.INBOUND, length=1000))
    agg.add(make_record(direction=TrafficDirection.OUTBOUND, length=500))

    snapshot = agg.snapshot(elapsed_seconds=1.0)
    assert snapshot.download_bytes_per_second == 1000
    assert snapshot.upload_bytes_per_second == 500
    assert snapshot.total_download_bytes == 1000
    assert snapshot.total_upload_bytes == 500


def test_rate_uses_elapsed_time() -> None:
    agg = TrafficAggregator()
    agg.add(make_record(direction=TrafficDirection.INBOUND, length=2000))
    snapshot = agg.snapshot(elapsed_seconds=2.0)
    assert snapshot.download_bytes_per_second == 1000


def test_interval_resets_after_snapshot() -> None:
    agg = TrafficAggregator()
    agg.add(make_record(direction=TrafficDirection.INBOUND, length=1000))
    agg.snapshot(1.0)
    # No new packets, so rate is 0.
    snapshot = agg.snapshot(1.0)
    assert snapshot.download_bytes_per_second == 0
    # Cumulative totals are retained.
    assert snapshot.total_download_bytes == 1000


def test_protocol_counts() -> None:
    agg = TrafficAggregator()
    agg.add(make_record(protocol="TCP"))
    agg.add(make_record(protocol="TCP"))
    agg.add(make_record(protocol="UDP"))
    snapshot = agg.snapshot(1.0)
    assert snapshot.protocol_counts["TCP"] == 2
    assert snapshot.protocol_counts["UDP"] == 1


def test_top_processes() -> None:
    agg = TrafficAggregator()
    agg.add(make_record(process_name="chrome.exe", length=5000))
    agg.add(make_record(process_name="python.exe", length=1000))
    snapshot = agg.snapshot(1.0)
    assert snapshot.top_processes[0][0] == "chrome.exe"


def test_reset_clears_totals() -> None:
    agg = TrafficAggregator()
    agg.add(make_record(direction=TrafficDirection.INBOUND, length=1000))
    agg.reset()
    snapshot = agg.snapshot(1.0)
    assert snapshot.total_download_bytes == 0
