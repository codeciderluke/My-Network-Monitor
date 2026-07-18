"""Lightweight table model for displaying top processes (optional)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

from my_network_monitor.utils.formatters import format_rate

_QIndex = QModelIndex | QPersistentModelIndex


class ProcessTableModel(QAbstractTableModel):
    """Model for a list of (process_name, bytes_per_second)."""

    HEADERS = ("Process", "Rate")

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[tuple[str, int]] = []

    def rowCount(self, parent: _QIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: _QIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> object:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return None

    def data(self, index: _QIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        name, value = self._rows[index.row()]
        return name if index.column() == 0 else format_rate(value)

    def set_rows(self, rows: list[tuple[str, int]]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()
