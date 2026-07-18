"""Main controller: coordinates the capture pipeline and UI refresh timers."""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal

from my_network_monitor.analysis.alert_detector import AlertDetector
from my_network_monitor.analysis.connection_tracker import ConnectionTracker
from my_network_monitor.analysis.packet_parser import PacketParser
from my_network_monitor.analysis.process_resolver import ProcessResolver
from my_network_monitor.analysis.traffic_aggregator import TrafficAggregator
from my_network_monitor.capture.capture_worker import PacketPipeline
from my_network_monitor.capture.interface_service import InterfaceService
from my_network_monitor.capture.scapy_capture_service import CaptureError, ScapyCaptureService
from my_network_monitor.config import (
    MAX_LOGS_PER_UI_TICK,
    PROCESS_CACHE_INTERVAL_MS,
    AppConfig,
)
from my_network_monitor.domain.alert import Alert
from my_network_monitor.domain.network_interface import NetworkInterface
from my_network_monitor.domain.packet_record import PacketRecord
from my_network_monitor.domain.traffic_snapshot import TrafficSnapshot
from my_network_monitor.storage.traffic_repository import TrafficRepository
from my_network_monitor.ui.controllers.demo_source import DemoSource

logger = logging.getLogger(__name__)


class MainController(QObject):
    """Mediator between the capture/analysis/storage pipeline and the UI timers."""

    records_ready = Signal(list)  # list[PacketRecord]
    snapshot_ready = Signal(object)  # TrafficSnapshot
    chart_ready = Signal(list, list)  # download, upload
    alert_raised = Signal(object)  # Alert
    status_changed = Signal(str, bool)  # message, is_running
    error_occurred = Signal(str)

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config

        self._capture_service = ScapyCaptureService()
        self._interface_service = InterfaceService(self._capture_service)
        self._aggregator = TrafficAggregator()
        self._resolver = ProcessResolver()
        self._tracker = ConnectionTracker()
        self._parser = PacketParser("", self._interface_service.local_ips())
        self._alert_detector = AlertDetector()
        self._pipeline = PacketPipeline(
            self._parser, self._aggregator, self._resolver, self._tracker
        )
        self._repository: TrafficRepository | None = None
        self._demo_source: DemoSource | None = None

        self._running = False
        self._paused = False
        self._last_snapshot_time = time.monotonic()

        # --- Timers (UI thread) ---
        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(config.ui.refresh_interval_ms)
        self._ui_timer.timeout.connect(self._flush_ui)

        self._snapshot_timer = QTimer(self)
        self._snapshot_timer.setInterval(config.ui.chart_interval_ms)
        self._snapshot_timer.timeout.connect(self._emit_snapshot)

        self._demo_timer = QTimer(self)
        self._demo_timer.setInterval(200)
        self._demo_timer.timeout.connect(self._generate_demo)

        # --- Background maintenance thread ---
        self._maintenance_stop = threading.Event()
        self._maintenance_thread: threading.Thread | None = None

    # --- Interfaces ---
    def list_interfaces(self) -> list[NetworkInterface]:
        return self._interface_service.list_interfaces()

    def default_interface(self) -> NetworkInterface | None:
        return self._interface_service.default_interface()

    # --- Capture control ---
    def start_capture(
        self,
        interface_name: str,
        bpf_filter: str,
        enable_sqlite: bool,
        store_raw: bool,
    ) -> bool:
        if self._running:
            return False
        self._parser.set_interface(interface_name)
        self._parser.update_local_ips(self._interface_service.local_ips())
        self._pipeline._store_raw = store_raw

        if enable_sqlite:
            self._start_repository()

        self._pipeline.reset_dropped()
        self._pipeline.start()
        try:
            self._capture_service.start(
                interface_name, self._pipeline.enqueue_packet, bpf_filter or None
            )
        except CaptureError as exc:
            self._pipeline.stop()
            self._stop_repository()
            logger.error("Failed to start capture: %s", exc)
            self.error_occurred.emit(str(exc))
            return False

        self._begin_running(f"Capturing · {interface_name}")
        return True

    def start_demo(self) -> None:
        if self._running:
            return
        self._demo_source = DemoSource()
        self._pipeline.start()
        self._demo_timer.start()
        self._begin_running("Demo mode (synthetic traffic)")

    def _begin_running(self, status: str) -> None:
        self._running = True
        self._paused = False
        self._last_snapshot_time = time.monotonic()
        self._ui_timer.start()
        self._snapshot_timer.start()
        self._start_maintenance()
        self.status_changed.emit(status, True)

    def stop(self) -> None:
        if not self._running:
            return
        self._demo_timer.stop()
        self._ui_timer.stop()
        self._snapshot_timer.stop()
        self._stop_maintenance()

        if self._capture_service.is_running:
            self._capture_service.stop()
        self._pipeline.stop()
        self._stop_repository()

        self._running = False
        self._demo_source = None
        self.status_changed.emit("Stopped", False)

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        status = "Paused" if paused else "Capturing"
        self.status_changed.emit(status, self._running)

    def clear(self) -> None:
        self._aggregator.reset()
        self._tracker.clear()
        self._pipeline.reset_dropped()

    def shutdown(self) -> None:
        """Release all resources when the app shuts down."""
        self.stop()
        logger.info("Controller shutdown complete")

    # --- Storage ---
    def _start_repository(self) -> None:
        self._repository = TrafficRepository(
            self._config.storage.database_path,
            batch_size=self._config.storage.batch_size,
            flush_interval_s=self._config.storage.flush_interval_ms / 1000,
        )
        self._repository.start()
        self._pipeline.set_storage_sink(self._repository.submit)

    def _stop_repository(self) -> None:
        if self._repository is not None:
            self._pipeline.set_storage_sink(None)
            self._repository.stop()
            if self._repository.last_error:
                self.error_occurred.emit(self._repository.last_error)
            self._repository = None

    # --- Timer callbacks ---
    def _flush_ui(self) -> None:
        if self._paused:
            return
        records = self._pipeline.drain_ui(MAX_LOGS_PER_UI_TICK)
        if records:
            self.records_ready.emit(records)

    def _emit_snapshot(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_snapshot_time
        self._last_snapshot_time = now

        self._aggregator.set_active_connections(self._tracker.active_count())
        snapshot = self._aggregator.snapshot(elapsed)
        self.snapshot_ready.emit(snapshot)

        download, upload = self._aggregator.history()
        self.chart_ready.emit(download, upload)

        for alert in self._alert_detector.evaluate(snapshot, datetime.now()):
            self.alert_raised.emit(alert)

    def _generate_demo(self) -> None:
        if self._demo_source is None or self._paused:
            return
        for record in self._demo_source.generate_batch(12):
            self._pipeline.inject_record(record)

    # --- Maintenance thread ---
    def _start_maintenance(self) -> None:
        self._maintenance_stop.clear()
        self._maintenance_thread = threading.Thread(
            target=self._maintenance_loop, name="maintenance", daemon=True
        )
        self._maintenance_thread.start()

    def _stop_maintenance(self) -> None:
        self._maintenance_stop.set()
        if self._maintenance_thread is not None:
            self._maintenance_thread.join(timeout=2.0)
            self._maintenance_thread = None

    def _maintenance_loop(self) -> None:
        interval = PROCESS_CACHE_INTERVAL_MS / 1000
        while not self._maintenance_stop.is_set():
            if self._demo_source is None:
                self._resolver.refresh()
            self._tracker.expire(time.monotonic())
            self._maintenance_stop.wait(interval)


# Re-export type hints (for import convenience)
__all__ = ["Alert", "MainController", "PacketRecord", "TrafficSnapshot"]
