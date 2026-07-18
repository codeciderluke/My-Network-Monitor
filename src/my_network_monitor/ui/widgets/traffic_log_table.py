"""Detailed traffic log table widget (QTableView + model + proxy)."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QModelIndex, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from my_network_monitor.domain.packet_record import PacketRecord
from my_network_monitor.ui.models.traffic_filter_proxy import TrafficFilterProxy
from my_network_monitor.ui.models.traffic_table_model import TrafficTableModel
from my_network_monitor.ui.widgets.traffic_filter_bar import FilterCriteria


class TrafficLogTable(QWidget):
    """Table displaying real-time logs. Supports auto-scroll/filter/double-click."""

    row_double_clicked = Signal(object)  # PacketRecord

    def __init__(self, max_rows: int = 10_000) -> None:
        super().__init__()

        self._model = TrafficTableModel(max_rows=max_rows)
        self._proxy = TrafficFilterProxy()
        self._proxy.setSourceModel(self._model)
        self._auto_scroll = True

        self._view = QTableView()
        self._view.setModel(self._proxy)
        self._configure_view()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)

        self._view.doubleClicked.connect(self._on_double_click)

    def _configure_view(self) -> None:
        view = self._view
        view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        view.setAlternatingRowColors(True)
        view.setShowGrid(False)
        view.setSortingEnabled(False)
        view.verticalHeader().setVisible(False)
        view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        view.setWordWrap(False)
        view.setFont(QFont("Cascadia Mono, Consolas, monospace", 10))

        header = view.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setHighlightSections(False)
        view.verticalHeader().setDefaultSectionSize(28)

        # Widths tuned for Full HD; last column stretches
        widths = (124, 54, 66, 150, 62, 168, 70, 210, 70, 84)
        for column, width in enumerate(widths):
            view.setColumnWidth(column, width)

    # --- Data updates ---
    def append_records(self, records: Sequence[PacketRecord]) -> None:
        self._model.append_records(records)
        if self._auto_scroll:
            self._view.scrollToBottom()

    def clear(self) -> None:
        self._model.clear()

    def set_auto_scroll(self, enabled: bool) -> None:
        self._auto_scroll = enabled

    def set_filter(self, criteria: FilterCriteria) -> None:
        self._proxy.set_criteria(criteria)

    def visible_count(self) -> int:
        return self._proxy.rowCount()

    def total_count(self) -> int:
        return self._model.rowCount()

    def all_records(self) -> list[PacketRecord]:
        return self._model.all_records()

    def selected_records(self) -> list[PacketRecord]:
        records: list[PacketRecord] = []
        for index in self._view.selectionModel().selectedRows():
            source = self._proxy.mapToSource(index)
            record = self._model.record_at(source.row())
            if record is not None:
                records.append(record)
        return records

    def _on_double_click(self, index: QModelIndex) -> None:
        source = self._proxy.mapToSource(index)
        record = self._model.record_at(source.row())
        if record is not None:
            self.row_double_clicked.emit(record)
