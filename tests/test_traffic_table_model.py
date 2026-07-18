"""Traffic table model tests (requires PySide6; skipped if unavailable)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6.QtCore")

from conftest import make_record
from my_network_monitor.ui.models.traffic_table_model import TrafficTableModel


def test_append_records() -> None:
    model = TrafficTableModel(max_rows=100)
    model.append_records([make_record(), make_record()])
    assert model.rowCount() == 2


def test_max_rows_enforced() -> None:
    model = TrafficTableModel(max_rows=5)
    model.append_records([make_record() for _ in range(10)])
    assert model.rowCount() == 5


def test_max_rows_across_batches() -> None:
    model = TrafficTableModel(max_rows=5)
    for _ in range(4):
        model.append_records([make_record(), make_record()])
    assert model.rowCount() == 5


def test_clear() -> None:
    model = TrafficTableModel(max_rows=10)
    model.append_records([make_record()])
    model.clear()
    assert model.rowCount() == 0


def test_record_at() -> None:
    model = TrafficTableModel(max_rows=10)
    rec = make_record(protocol="UDP")
    model.append_records([rec])
    assert model.record_at(0) is rec
    assert model.record_at(99) is None


def test_column_count() -> None:
    model = TrafficTableModel()
    assert model.columnCount() == len(TrafficTableModel.HEADERS)
