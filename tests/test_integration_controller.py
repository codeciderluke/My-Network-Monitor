"""Controller lifecycle integration tests (demo pipeline + thread cleanup)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from network_monitor.config import AppConfig
from network_monitor.ui.controllers.main_controller import MainController


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app  # type: ignore[return-value]


def test_demo_lifecycle_and_thread_cleanup(qapp: QApplication) -> None:
    """Demo start -> data flow -> on shutdown all worker threads are cleaned up."""
    controller = MainController(AppConfig())
    received: list[int] = []
    controller.records_ready.connect(lambda recs: received.append(len(recs)))

    controller.start_demo()
    assert controller._running is True

    # Run event loop so the QTimer fires.
    QTest.qWait(900)

    maintenance = controller._maintenance_thread
    assert maintenance is not None and maintenance.is_alive()

    controller.shutdown()

    # After shutdown, threads and state are cleaned up.
    assert controller._running is False
    assert controller._maintenance_thread is None
    assert controller._pipeline._thread is None
    assert not maintenance.is_alive()
    # Demo traffic reached the UI queue.
    assert sum(received) > 0


def test_stop_is_idempotent(qapp: QApplication) -> None:
    """Calling stop() while not running raises no exception."""
    controller = MainController(AppConfig())
    controller.stop()  # never started
    controller.shutdown()
    assert controller._running is False
