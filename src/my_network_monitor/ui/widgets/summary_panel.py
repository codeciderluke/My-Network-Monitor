"""Left summary panel: metric cards + graph + stats + top lists + alerts."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from my_network_monitor.domain.alert import Alert, AlertSeverity
from my_network_monitor.domain.traffic_snapshot import TrafficSnapshot
from my_network_monitor.ui import icons
from my_network_monitor.ui.theme import Palette
from my_network_monitor.ui.widgets.metric_card import MetricCard, StatChip
from my_network_monitor.ui.widgets.traffic_chart import TrafficChart
from my_network_monitor.utils.formatters import format_rate, format_size

_SEVERITY_COLORS = {
    AlertSeverity.INFO: Palette.ACCENT,
    AlertSeverity.WARNING: Palette.WARNING,
    AlertSeverity.CRITICAL: Palette.CRITICAL,
}


class SummaryPanel(QScrollArea):
    """Scrollable left panel that displays the traffic summary."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("SummaryPanel")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        container.setObjectName("SummaryPanel")
        root = QVBoxLayout(container)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        rate_row = QHBoxLayout()
        rate_row.setSpacing(12)
        self._download_card = MetricCard(
            "Download", "MetricValueDownload", icons.icon("download", Palette.DOWNLOAD, 15)
        )
        self._upload_card = MetricCard(
            "Upload", "MetricValueUpload", icons.icon("upload", Palette.UPLOAD, 15)
        )
        rate_row.addWidget(self._download_card)
        rate_row.addWidget(self._upload_card)
        root.addLayout(rate_row)

        root.addWidget(_title("Last 60 Seconds", "chart"))
        self._chart = TrafficChart()
        self._chart.setMinimumHeight(170)
        root.addWidget(self._chart)

        root.addWidget(_title("Statistics", "cpu"))
        self._chips: dict[str, StatChip] = {}
        grid = QGridLayout()
        grid.setSpacing(10)
        chip_defs = [
            ("connections", "Connections"),
            ("pps", "Packets/s"),
            ("tcp", "TCP"),
            ("udp", "UDP"),
            ("dns", "DNS"),
            ("icmp", "ICMP"),
        ]
        for i, (key, label) in enumerate(chip_defs):
            chip = StatChip(label)
            self._chips[key] = chip
            grid.addWidget(chip, i // 3, i % 3)
        root.addLayout(grid)

        self._totals = QLabel("↓ 0 B   ↑ 0 B")
        self._totals.setObjectName("MetricSub")
        root.addWidget(self._totals)

        root.addWidget(_title("Top Processes", "cpu"))
        self._process_box = _RankList()
        root.addWidget(self._process_box)

        root.addWidget(_title("Top Destinations", "globe"))
        self._destination_box = _RankList()
        root.addWidget(self._destination_box)

        root.addWidget(_title("Alerts", "alert"))
        self._alerts_box = QVBoxLayout()
        self._alerts_box.setSpacing(6)
        alerts_container = QWidget()
        alerts_container.setLayout(self._alerts_box)
        root.addWidget(alerts_container)
        self._empty_alert = QLabel("No alerts")
        self._empty_alert.setObjectName("MetricSub")
        self._alerts_box.addWidget(self._empty_alert)

        root.addStretch(1)
        self.setWidget(container)

    def update_snapshot(self, snapshot: TrafficSnapshot) -> None:
        self._download_card.set_value(format_rate(snapshot.download_bytes_per_second))
        self._upload_card.set_value(format_rate(snapshot.upload_bytes_per_second))

        self._chips["connections"].set_value(str(snapshot.active_connections))
        self._chips["pps"].set_value(str(snapshot.packets_per_second))
        counts = snapshot.protocol_counts
        self._chips["tcp"].set_value(str(counts.get("TCP", 0)))
        self._chips["udp"].set_value(str(counts.get("UDP", 0)))
        self._chips["dns"].set_value(str(counts.get("DNS", 0)))
        self._chips["icmp"].set_value(str(counts.get("ICMP", 0)))

        self._totals.setText(
            f"↓ {format_size(snapshot.total_download_bytes)}   "
            f"↑ {format_size(snapshot.total_upload_bytes)}"
            + (f"   ·   dropped {snapshot.dropped_packets}" if snapshot.dropped_packets else "")
        )

        self._process_box.set_items(
            [(name, format_size(value)) for name, value in snapshot.top_processes]
        )
        self._destination_box.set_items(
            [(dest, format_size(value)) for dest, value in snapshot.top_destinations]
        )

    def update_chart(self, download: list[float], upload: list[float]) -> None:
        self._chart.update_data(download, upload)

    def add_alert(self, alert: Alert) -> None:
        self._empty_alert.setVisible(False)
        row = QLabel(f"{alert.message}  ·  {alert.detail}")
        row.setObjectName("AlertRow")
        color = _SEVERITY_COLORS.get(alert.severity, Palette.WARNING)
        row.setStyleSheet(
            f"QLabel#AlertRow {{ border-left-color: {color}; "
            f"background-color:{Palette.BG_ELEVATED}; border-radius:6px; padding:6px 10px; }}"
        )
        self._alerts_box.insertWidget(0, row)
        # Keep 5 most recent
        while self._alerts_box.count() > 6:
            item = self._alerts_box.takeAt(self._alerts_box.count() - 1)
            if item is None:
                break
            widget = item.widget()
            if widget is not None and widget is not self._empty_alert:
                widget.deleteLater()

    def clear_dynamic(self) -> None:
        self._chart.clear()
        self._process_box.set_items([])
        self._destination_box.set_items([])


class _RankList(QWidget):
    """Ranked list of name + value pairs."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 10, 12, 10)
        self._layout.setSpacing(6)
        self._empty = QLabel("No data")
        self._empty.setObjectName("MetricSub")
        self._layout.addWidget(self._empty)
        self._rows: list[QWidget] = []

    def set_items(self, items: list[tuple[str, str]]) -> None:
        for row in self._rows:
            row.deleteLater()
        self._rows.clear()
        self._empty.setVisible(not items)
        for name, value in items:
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            name_label = QLabel(_elide(name, 28))
            name_label.setObjectName("RankName")
            value_label = QLabel(value)
            value_label.setObjectName("RankValue")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(name_label)
            layout.addStretch(1)
            layout.addWidget(value_label)
            self._layout.addWidget(row)
            self._rows.append(row)


def _title(text: str, icon_name: str | None = None) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(2, 6, 2, 2)
    layout.setSpacing(7)
    if icon_name is not None:
        icon_label = QLabel()
        icon_label.setPixmap(icons.icon(icon_name, Palette.TEXT_MUTED, 13).pixmap(13, 13))
        layout.addWidget(icon_label)
    label = QLabel(text.upper())
    label.setObjectName("SectionTitle")
    layout.addWidget(label)
    layout.addStretch(1)
    return row


def _elide(text: str, length: int) -> str:
    return text if len(text) <= length else text[: length - 1] + "…"
