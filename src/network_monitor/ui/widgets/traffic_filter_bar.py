"""Display filter bar."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QWidget,
)

_PROTOCOLS = ("All", "TCP", "UDP", "DNS", "ICMP", "ARP")
_DIRECTIONS = ("All", "IN", "OUT", "LOCAL")


@dataclass(slots=True)
class FilterCriteria:
    """Display filter conditions."""

    protocol: str = "All"
    direction: str = "All"
    ip: str = ""
    port: str = ""
    process: str = ""
    text: str = ""

    def is_empty(self) -> bool:
        return (
            self.protocol == "All"
            and self.direction == "All"
            and not self.ip
            and not self.port
            and not self.process
            and not self.text
        )


class TrafficFilterBar(QWidget):
    """Display filter by protocol/direction/IP/port/process/text."""

    filter_changed = Signal(object)  # FilterCriteria

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("FilterBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self._protocol = QComboBox()
        self._protocol.addItems(_PROTOCOLS)
        self._protocol.setMinimumWidth(90)

        self._direction = QComboBox()
        self._direction.addItems(_DIRECTIONS)
        self._direction.setMinimumWidth(90)

        self._ip = _make_search("IP address")
        self._port = _make_search("Port")
        self._port.setMaximumWidth(90)
        self._process = _make_search("Process")
        self._text = _make_search("Search…")

        layout.addWidget(_tag("Proto"))
        layout.addWidget(self._protocol)
        layout.addWidget(_tag("Dir"))
        layout.addWidget(self._direction)
        layout.addWidget(self._ip, 2)
        layout.addWidget(self._port)
        layout.addWidget(self._process, 1)
        layout.addWidget(self._text, 2)

        self._protocol.currentTextChanged.connect(self._emit)
        self._direction.currentTextChanged.connect(self._emit)
        for field in (self._ip, self._port, self._process, self._text):
            field.textChanged.connect(self._emit)

    def _emit(self) -> None:
        self.filter_changed.emit(self.criteria())

    def criteria(self) -> FilterCriteria:
        return FilterCriteria(
            protocol=self._protocol.currentText(),
            direction=self._direction.currentText(),
            ip=self._ip.text().strip(),
            port=self._port.text().strip(),
            process=self._process.text().strip(),
            text=self._text.text().strip(),
        )


def _make_search(placeholder: str) -> QLineEdit:
    field = QLineEdit()
    field.setPlaceholderText(placeholder)
    field.setClearButtonEnabled(True)
    return field


def _tag(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("SectionTitle")
    return label
