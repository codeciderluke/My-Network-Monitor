"""QAbstractTableModel for the detailed traffic log (ring buffer + batch append)."""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QColor

from my_network_monitor.config import MAX_VISIBLE_LOG_ROWS
from my_network_monitor.domain.packet_record import PacketRecord, TrafficDirection
from my_network_monitor.ui.theme import Palette, protocol_color
from my_network_monitor.utils.formatters import format_port, format_size

_QIndex = QModelIndex | QPersistentModelIndex

_DIRECTION_COLORS = {
    TrafficDirection.INBOUND: Palette.DIR_IN,
    TrafficDirection.OUTBOUND: Palette.DIR_OUT,
    TrafficDirection.LOCAL: Palette.DIR_LOCAL,
    TrafficDirection.UNKNOWN: Palette.DIR_UNKNOWN,
}


class TrafficTableModel(QAbstractTableModel):
    """Traffic log model backed by a fixed-size ring buffer."""

    HEADERS = (
        "Time",
        "Dir",
        "Proto",
        "Process",
        "PID",
        "Source",
        "S.Port",
        "Destination",
        "D.Port",
        "Size",
        "Summary",
    )

    def __init__(self, max_rows: int = MAX_VISIBLE_LOG_ROWS) -> None:
        super().__init__()
        self._rows: deque[PacketRecord] = deque(maxlen=max_rows)
        self._max_rows = max_rows

    # --- Qt interface ---
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
        if not index.isValid():
            return None
        record = self._rows[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self._cell_text(record, column)
        if role == Qt.ItemDataRole.ForegroundRole:
            return self._cell_color(record, column)
        if role == Qt.ItemDataRole.TextAlignmentRole and column in (4, 6, 8, 9):
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None

    # --- Batch append ---
    def append_records(self, records: Sequence[PacketRecord]) -> None:
        """Append multiple records at once; overflow is removed from the front."""
        if not records:
            return
        current = len(self._rows)
        incoming = len(records)
        free = self._max_rows - current

        # drop oldest when incoming exceeds free space
        if incoming > free:
            remove = incoming - free
            remove = min(remove, current)
            if remove > 0:
                self.beginRemoveRows(QModelIndex(), 0, remove - 1)
                for _ in range(remove):
                    self._rows.popleft()
                self.endRemoveRows()

        start = len(self._rows)
        # cap to buffer size (deque auto-drops overflow)
        insert_count = min(incoming, self._max_rows)
        self.beginInsertRows(QModelIndex(), start, start + insert_count - 1)
        self._rows.extend(records[-insert_count:])
        self.endInsertRows()

    def clear(self) -> None:
        self.beginResetModel()
        self._rows.clear()
        self.endResetModel()

    def record_at(self, row: int) -> PacketRecord | None:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    def all_records(self) -> list[PacketRecord]:
        return list(self._rows)

    # --- Cell rendering ---
    def _cell_text(self, record: PacketRecord, column: int) -> str:
        match column:
            case 0:
                return record.timestamp.strftime("%H:%M:%S.%f")[:-3]
            case 1:
                return str(record.direction)
            case 2:
                return record.protocol
            case 3:
                return record.process_name or "—"
            case 4:
                return str(record.process_id) if record.process_id else ""
            case 5:
                return record.source_ip
            case 6:
                return format_port(record.source_port)
            case 7:
                return record.domain_name or record.destination_ip
            case 8:
                return format_port(record.destination_port)
            case 9:
                return format_size(record.length)
            case 10:
                return record.summary
        return ""

    def _cell_color(self, record: PacketRecord, column: int) -> QColor | None:
        if column == 1:
            return QColor(_DIRECTION_COLORS.get(record.direction, Palette.DIR_UNKNOWN))
        if column == 2:
            return QColor(protocol_color(record.protocol))
        if column in (0, 4, 6, 8):
            return QColor(Palette.TEXT_MUTED)
        if column == 10:
            return QColor(Palette.TEXT_SECONDARY)
        return None
