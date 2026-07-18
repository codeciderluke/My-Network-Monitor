"""UI model batch append + filter proxy integration tests (requires PySide6)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6.QtCore")

from conftest import make_record
from network_monitor.ui.models.traffic_filter_proxy import TrafficFilterProxy
from network_monitor.ui.models.traffic_table_model import TrafficTableModel
from network_monitor.ui.widgets.traffic_filter_bar import FilterCriteria


def test_batch_add_preserves_ring_buffer_limit() -> None:
    """Appending past max rows across batches keeps the ring buffer cap intact."""
    model = TrafficTableModel(max_rows=1000)
    for _ in range(30):
        model.append_records([make_record() for _ in range(100)])
    assert model.rowCount() == 1000


def test_filter_proxy_keeps_source_data() -> None:
    """The view filter limits display only and keeps the source data (spec Phase 7)."""
    model = TrafficTableModel(max_rows=5000)
    proxy = TrafficFilterProxy()
    proxy.setSourceModel(model)

    records = [make_record(protocol="TCP" if i % 2 else "UDP") for i in range(3000)]
    for i in range(0, 3000, 300):
        model.append_records(records[i : i + 300])

    assert model.rowCount() == 3000

    proxy.set_criteria(FilterCriteria(protocol="TCP"))
    assert proxy.rowCount() == 1500  # only half shown on screen
    assert model.rowCount() == 3000  # source is retained

    proxy.set_criteria(FilterCriteria())  # clear filter
    assert proxy.rowCount() == 3000


def test_filter_by_ip_and_port() -> None:
    model = TrafficTableModel(max_rows=100)
    proxy = TrafficFilterProxy()
    proxy.setSourceModel(model)

    model.append_records(
        [
            make_record(destination_ip="8.8.8.8", source_port=1000, destination_port=53),
            make_record(destination_ip="1.1.1.1", source_port=2000, destination_port=443),
        ]
    )

    proxy.set_criteria(FilterCriteria(ip="8.8.8.8"))
    assert proxy.rowCount() == 1

    proxy.set_criteria(FilterCriteria(port="443"))
    assert proxy.rowCount() == 1

    proxy.set_criteria(FilterCriteria(port="53"))
    assert proxy.rowCount() == 1
