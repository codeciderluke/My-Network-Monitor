"""Main window: toolbar + left summary panel + right detail log."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from network_monitor.config import AppConfig
from network_monitor.domain.alert import Alert
from network_monitor.domain.packet_record import PacketRecord
from network_monitor.domain.traffic_snapshot import TrafficSnapshot
from network_monitor.storage import export_service
from network_monitor.ui import icons
from network_monitor.ui.controllers.main_controller import MainController
from network_monitor.ui.theme import Palette
from network_monitor.ui.widgets.packet_detail_dialog import PacketDetailDialog
from network_monitor.ui.widgets.summary_panel import SummaryPanel
from network_monitor.ui.widgets.traffic_filter_bar import TrafficFilterBar
from network_monitor.ui.widgets.traffic_log_table import TrafficLogTable

logger = logging.getLogger(__name__)

_BRAND = "Designed by Codecider Lab"


class MainWindow(QMainWindow):
    """Application main window."""

    def __init__(self, config: AppConfig, demo: bool = False) -> None:
        super().__init__()
        self._config = config
        self._demo = demo
        self._controller = MainController(config)

        self.setWindowTitle("Network Traffic Monitor — Codecider Lab")
        self.setWindowIcon(QIcon(icons.app_pixmap(64)))
        self._apply_initial_geometry()

        self._build_toolbar()
        self._build_central()
        self._build_statusbar()

        self._connect_controller()
        self._populate_interfaces()
        self._update_button_states(running=False)

        if demo:
            self._start()

    # ---------- Full HD geometry ----------
    def _apply_initial_geometry(self) -> None:
        """Optimize the window size/position for large screens such as 1920x1080."""
        self.setMinimumSize(1180, 720)
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(1600, 940)
            return
        available = screen.availableGeometry()
        # ~88% of screen, capped at Full HD.
        width = min(int(available.width() * 0.88), 1760)
        height = min(int(available.height() * 0.9), 1000)
        self.resize(width, height)
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())

    # ---------- Top toolbar ----------
    def _build_toolbar(self) -> None:
        bar = QWidget()
        bar.setObjectName("TopToolbar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(12)

        # Logo icon + title
        logo = QLabel()
        logo.setPixmap(icons.app_pixmap(30))
        logo.setObjectName("LogoIcon")
        layout.addWidget(logo)

        title = QLabel()
        title.setObjectName("AppTitle")
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setText(
            f'<span style="color:{Palette.TEXT_PRIMARY};">Network </span>'
            f'<span style="color:{Palette.ACCENT};">Traffic</span>'
            f'<span style="color:{Palette.TEXT_PRIMARY};"> Monitor</span>'
        )
        layout.addWidget(title)
        layout.addSpacing(18)

        iface_label = QLabel()
        iface_label.setPixmap(icons.icon("globe", Palette.TEXT_MUTED, 16).pixmap(16, 16))
        layout.addWidget(iface_label)

        self._interface_combo = QComboBox()
        self._interface_combo.setMinimumWidth(300)
        layout.addWidget(self._interface_combo)

        self._refresh_button = QPushButton()
        self._refresh_button.setObjectName("IconButton")
        self._refresh_button.setIcon(icons.icon("refresh", Palette.TEXT_SECONDARY, 18))
        self._refresh_button.setFixedSize(40, 38)
        self._refresh_button.setToolTip("Refresh interfaces")
        self._refresh_button.clicked.connect(self._populate_interfaces)
        layout.addWidget(self._refresh_button)

        layout.addStretch(1)

        self._sqlite_check = QCheckBox("  Save to SQLite")
        self._sqlite_check.setIcon(icons.icon("database", Palette.TEXT_SECONDARY, 16))
        self._sqlite_check.setChecked(config_default_sqlite(self._config))
        layout.addWidget(self._sqlite_check)
        layout.addSpacing(6)

        self._start_button = QPushButton("  Start")
        self._start_button.setObjectName("PrimaryButton")
        self._start_button.setIcon(icons.icon("play", "#ecfeff", 16))
        self._start_button.clicked.connect(self._start)
        layout.addWidget(self._start_button)

        self._pause_button = QPushButton("  Pause")
        self._pause_button.setIcon(icons.icon("pause", Palette.TEXT_PRIMARY, 16))
        self._pause_button.setCheckable(True)
        self._pause_button.toggled.connect(self._on_pause)
        layout.addWidget(self._pause_button)

        self._stop_button = QPushButton("  Stop")
        self._stop_button.setObjectName("DangerButton")
        self._stop_button.setIcon(icons.icon("stop", "#fca5a5", 16))
        self._stop_button.clicked.connect(self._stop)
        layout.addWidget(self._stop_button)

        # Status indicator
        self._status_dot = QLabel("●")
        self._status_dot.setObjectName("StatusDot")
        self._status_dot.setStyleSheet(f"color:{Palette.TEXT_MUTED};")
        self._status_text = QLabel("Idle")
        self._status_text.setObjectName("StatusText")
        layout.addSpacing(10)
        layout.addWidget(self._status_dot)
        layout.addWidget(self._status_text)

        self._toolbar_widget = bar

    # ---------- Central area ----------
    def _build_central(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._toolbar_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._summary_panel = SummaryPanel()
        self._summary_panel.setMinimumWidth(340)
        self._summary_panel.setMaximumWidth(500)
        splitter.addWidget(self._summary_panel)

        # Right: log table + filter + actions
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._log_table = TrafficLogTable(max_rows=self._config.ui.max_visible_rows)
        self._log_table.row_double_clicked.connect(self._show_detail)
        right_layout.addWidget(self._log_table, 1)

        self._filter_bar = TrafficFilterBar()
        self._filter_bar.filter_changed.connect(self._log_table.set_filter)
        right_layout.addWidget(self._filter_bar)

        right_layout.addWidget(self._build_log_actions())

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([420, 1300])

        outer.addWidget(splitter, 1)
        self.setCentralWidget(central)

    def _build_log_actions(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("LogActionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 8, 14, 10)
        layout.setSpacing(8)

        self._autoscroll_check = QCheckBox("Auto-scroll")
        self._autoscroll_check.setChecked(self._config.ui.auto_scroll)
        self._autoscroll_check.toggled.connect(self._log_table.set_auto_scroll)
        layout.addWidget(self._autoscroll_check)

        layout.addStretch(1)

        self._count_label = QLabel("0 / 0 rows")
        self._count_label.setObjectName("MetricSub")
        layout.addWidget(self._count_label)
        layout.addSpacing(10)

        copy_btn = QPushButton("  Copy Rows")
        copy_btn.setIcon(icons.icon("copy", Palette.TEXT_SECONDARY, 15))
        copy_btn.clicked.connect(self._copy_selected)
        layout.addWidget(copy_btn)

        clear_btn = QPushButton("  Clear Log")
        clear_btn.setIcon(icons.icon("trash", Palette.TEXT_SECONDARY, 15))
        clear_btn.clicked.connect(self._clear_logs)
        layout.addWidget(clear_btn)

        csv_btn = QPushButton("  CSV")
        csv_btn.setIcon(icons.icon("file", Palette.TEXT_SECONDARY, 15))
        csv_btn.clicked.connect(lambda: self._export("csv"))
        layout.addWidget(csv_btn)

        jsonl_btn = QPushButton("  JSONL")
        jsonl_btn.setIcon(icons.icon("braces", Palette.TEXT_SECONDARY, 15))
        jsonl_btn.clicked.connect(lambda: self._export("jsonl"))
        layout.addWidget(jsonl_btn)

        return bar

    def _build_statusbar(self) -> None:
        status = QStatusBar()
        status.setSizeGripEnabled(False)
        self.setStatusBar(status)

        self._status_message = QLabel("Ready")
        self._status_message.setObjectName("StatusMessage")
        status.addWidget(self._status_message)

        # Bottom brand text
        brand_wrap = QFrame()
        brand_layout = QHBoxLayout(brand_wrap)
        brand_layout.setContentsMargins(0, 0, 6, 0)
        brand_layout.setSpacing(6)
        brand_logo = QLabel()
        brand_logo.setPixmap(icons.app_pixmap(16))
        brand = QLabel(_BRAND)
        brand.setObjectName("BrandLabel")
        brand_layout.addWidget(brand_logo)
        brand_layout.addWidget(brand)
        status.addPermanentWidget(brand_wrap)

    # ---------- Controller wiring ----------
    def _connect_controller(self) -> None:
        c = self._controller
        c.records_ready.connect(self._on_records)
        c.snapshot_ready.connect(self._on_snapshot)
        c.chart_ready.connect(self._summary_panel.update_chart)
        c.alert_raised.connect(self._on_alert)
        c.status_changed.connect(self._on_status)
        c.error_occurred.connect(self._on_error)

    def _populate_interfaces(self) -> None:
        self._interface_combo.clear()
        interfaces = self._controller.list_interfaces()
        for iface in interfaces:
            self._interface_combo.addItem(iface.display_name, iface.name)
        default = self._controller.default_interface()
        if default is not None:
            index = self._interface_combo.findData(default.name)
            if index >= 0:
                self._interface_combo.setCurrentIndex(index)
        if not interfaces:
            self._status_message.setText("No interfaces found.")

    # ---------- Button handlers ----------
    def _start(self) -> None:
        if self._demo:
            self._controller.start_demo()
            return
        iface_name = self._interface_combo.currentData()
        if not iface_name:
            self._on_error("Please select an interface to capture.")
            return
        ok = self._controller.start_capture(
            iface_name,
            self._config.capture.bpf_filter,
            enable_sqlite=self._sqlite_check.isChecked(),
            store_raw=self._config.capture.store_raw_payload,
        )
        if not ok:
            logger.warning("Failed to start capture")

    def _stop(self) -> None:
        self._controller.stop()

    def _on_pause(self, checked: bool) -> None:
        self._controller.set_paused(checked)
        if checked:
            self._pause_button.setText("  Resume")
            self._pause_button.setIcon(icons.icon("play", Palette.ACCENT, 16))
        else:
            self._pause_button.setText("  Pause")
            self._pause_button.setIcon(icons.icon("pause", Palette.TEXT_PRIMARY, 16))

    def _clear_logs(self) -> None:
        self._log_table.clear()
        self._controller.clear()
        self._update_counts()

    def _copy_selected(self) -> None:
        records = self._log_table.selected_records()
        if not records:
            return
        lines = [
            f"{r.timestamp.isoformat()}\t{r.direction}\t{r.protocol}\t"
            f"{r.source_ip}:{r.source_port}\t{r.destination_ip}:{r.destination_port}\t"
            f"{r.length}\t{r.summary}"
            for r in records
        ]
        QGuiApplication.clipboard().setText("\n".join(lines))
        self._status_message.setText(f"Copied {len(records)} rows to the clipboard.")

    def _export(self, fmt: str) -> None:
        records = self._log_table.all_records()
        if not records:
            self._status_message.setText("There are no logs to export.")
            return
        if fmt == "csv":
            path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "traffic.csv", "CSV (*.csv)")
            if not path:
                return
            count = export_service.export_csv(records, path)
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "Export JSON Lines", "traffic.jsonl", "JSON Lines (*.jsonl)"
            )
            if not path:
                return
            count = export_service.export_jsonl(records, path)
        self._status_message.setText(f"Saved {count} records → {path}")

    def _show_detail(self, record: PacketRecord) -> None:
        dialog = PacketDetailDialog(record, self)
        dialog.exec()

    # ---------- Controller signal handlers ----------
    def _on_records(self, records: list[PacketRecord]) -> None:
        self._log_table.append_records(records)
        self._update_counts()

    def _on_snapshot(self, snapshot: TrafficSnapshot) -> None:
        self._summary_panel.update_snapshot(snapshot)

    def _on_alert(self, alert: Alert) -> None:
        self._summary_panel.add_alert(alert)

    def _on_status(self, message: str, running: bool) -> None:
        self._status_text.setText(message)
        color = "#34d399" if running else "#5c6773"
        self._status_dot.setStyleSheet(f"color:{color};")
        self._status_message.setText(message)
        self._update_button_states(running)

    def _on_error(self, message: str) -> None:
        logger.error("Displaying UI error: %s", message)
        QMessageBox.warning(self, "Error", message)
        self._status_message.setText(message)

    def _update_counts(self) -> None:
        self._count_label.setText(
            f"{self._log_table.visible_count():,} / {self._log_table.total_count():,} rows"
        )

    def _update_button_states(self, running: bool) -> None:
        self._start_button.setEnabled(not running)
        self._stop_button.setEnabled(running)
        self._pause_button.setEnabled(running)
        self._interface_combo.setEnabled(not running)
        self._sqlite_check.setEnabled(not running)
        self._refresh_button.setEnabled(not running)
        if not running:
            self._pause_button.setChecked(False)

    # ---------- Shutdown ----------
    def closeEvent(self, event: object) -> None:
        self._controller.shutdown()
        super().closeEvent(event)  # type: ignore[arg-type]


def config_default_sqlite(config: AppConfig) -> bool:
    return config.storage.enable_sqlite
