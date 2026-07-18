"""Key metric card widget."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class MetricCard(QFrame):
    """Metric card with a label (+icon), a large value, and supporting text."""

    def __init__(
        self,
        label: str,
        value_object_name: str = "MetricValue",
        icon: QIcon | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("MetricCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(3)

        header = QHBoxLayout()
        header.setSpacing(6)
        if icon is not None:
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(15, 15))
            header.addWidget(icon_label)
        self._label = QLabel(label.upper())
        self._label.setObjectName("MetricLabel")
        header.addWidget(self._label)
        header.addStretch(1)

        self._value = QLabel("—")
        self._value.setObjectName(value_object_name)

        self._sub = QLabel("")
        self._sub.setObjectName("MetricSub")

        layout.addLayout(header)
        layout.addWidget(self._value)
        layout.addWidget(self._sub)

    def set_value(self, value: str, sub: str = "") -> None:
        self._value.setText(value)
        self._sub.setText(sub)
        self._sub.setVisible(bool(sub))


class StatChip(QFrame):
    """Small stat chip (protocol counts, etc.)."""

    def __init__(self, label: str) -> None:
        super().__init__()
        self.setObjectName("StatChip")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(1)

        self._value = QLabel("0")
        self._value.setObjectName("StatChipValue")
        self._value.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._label = QLabel(label)
        self._label.setObjectName("StatChipLabel")

        layout.addWidget(self._value)
        layout.addWidget(self._label)

    def set_value(self, value: str) -> None:
        self._value.setText(value)
