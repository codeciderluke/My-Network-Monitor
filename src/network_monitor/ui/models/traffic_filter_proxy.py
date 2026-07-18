"""QSortFilterProxyModel for on-screen filtering."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QSortFilterProxyModel

from network_monitor.ui.models.traffic_table_model import TrafficTableModel
from network_monitor.ui.widgets.traffic_filter_bar import FilterCriteria

_QIndex = QModelIndex | QPersistentModelIndex


class TrafficFilterProxy(QSortFilterProxyModel):
    """Proxy that applies FilterCriteria to PacketRecords (display-only filtering)."""

    def __init__(self) -> None:
        super().__init__()
        self._criteria = FilterCriteria()

    def set_criteria(self, criteria: FilterCriteria) -> None:
        self._criteria = criteria
        self.invalidate()

    def filterAcceptsRow(self, source_row: int, source_parent: _QIndex) -> bool:
        criteria = self._criteria
        if criteria.is_empty():
            return True

        model = self.sourceModel()
        if not isinstance(model, TrafficTableModel):
            return True
        record = model.record_at(source_row)
        if record is None:
            return False

        if criteria.protocol != "All" and record.protocol != criteria.protocol:
            return False
        if criteria.direction != "All" and str(record.direction) != criteria.direction:
            return False
        if criteria.ip and (
            criteria.ip not in record.source_ip and criteria.ip not in record.destination_ip
        ):
            return False
        if criteria.port:
            ports = {str(record.source_port), str(record.destination_port)}
            if criteria.port not in ports:
                return False
        if criteria.process:
            name = (record.process_name or "").lower()
            if criteria.process.lower() not in name:
                return False
        if criteria.text:
            haystack = " ".join(
                [
                    record.source_ip,
                    record.destination_ip,
                    record.protocol,
                    record.summary,
                    record.domain_name or "",
                    record.process_name or "",
                ]
            ).lower()
            if criteria.text.lower() not in haystack:
                return False
        return True
