"""Upload/download speed graph for the last 60 seconds (pyqtgraph)."""

from __future__ import annotations

import pyqtgraph as pg
from PySide6.QtWidgets import QVBoxLayout, QWidget

from network_monitor.config import HISTORY_SECONDS
from network_monitor.ui.theme import Palette
from network_monitor.utils.formatters import format_rate


class TrafficChart(QWidget):
    """Real-time line chart of download/upload speeds."""

    def __init__(self, history_seconds: int = HISTORY_SECONDS) -> None:
        super().__init__()
        self._history_seconds = history_seconds

        pg.setConfigOptions(antialias=True)
        self._plot = pg.PlotWidget()
        self._plot.setBackground(Palette.BG_SURFACE)
        self._plot.showGrid(x=False, y=True, alpha=0.12)
        self._plot.setMenuEnabled(False)
        self._plot.setMouseEnabled(x=False, y=False)
        self._plot.hideButtons()
        self._plot.setLabel("left", "", color=Palette.TEXT_MUTED)

        axis_left = self._plot.getAxis("left")
        axis_bottom = self._plot.getAxis("bottom")
        for axis in (axis_left, axis_bottom):
            axis.setPen(pg.mkPen(Palette.BORDER))
            axis.setTextPen(pg.mkPen(Palette.TEXT_MUTED))
        axis_bottom.setStyle(showValues=False)
        axis_left.setWidth(64)
        axis_left.tickStrings = self._tick_strings

        self._download_curve = self._plot.plot(
            pen=pg.mkPen(Palette.DOWNLOAD, width=2),
            fillLevel=0,
            brush=pg.mkBrush(52, 211, 153, 40),
            name="Download",
        )
        self._upload_curve = self._plot.plot(
            pen=pg.mkPen(Palette.UPLOAD, width=2),
            fillLevel=0,
            brush=pg.mkBrush(96, 165, 250, 35),
            name="Upload",
        )

        legend = self._plot.addLegend(offset=(10, 6), labelTextColor=Palette.TEXT_SECONDARY)
        legend.setBrush(pg.mkBrush(0, 0, 0, 0))
        legend.setPen(pg.mkPen(0, 0, 0, 0))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plot)

    @staticmethod
    def _tick_strings(values: list[float], scale: float, spacing: float) -> list[str]:
        return [format_rate(v) for v in values]

    def update_data(self, download: list[float], upload: list[float]) -> None:
        """Render the history data on the graph."""
        x_down = list(range(-len(download) + 1, 1)) if download else []
        x_up = list(range(-len(upload) + 1, 1)) if upload else []
        self._download_curve.setData(x_down, download)
        self._upload_curve.setData(x_up, upload)

    def clear(self) -> None:
        self._download_curve.setData([], [])
        self._upload_curve.setData([], [])
