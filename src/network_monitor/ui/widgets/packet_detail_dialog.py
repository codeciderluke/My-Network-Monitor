"""Packet detail dialog (header info + Hex/ASCII view)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)

from network_monitor.domain.packet_record import PacketRecord
from network_monitor.utils.formatters import format_port, format_size


class PacketDetailDialog(QDialog):
    """Display detailed metadata and raw bytes for the selected packet."""

    def __init__(self, record: PacketRecord, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setWindowTitle("Packet Details")
        self.setMinimumSize(560, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        layout.addWidget(_heading("Basic Information"))
        layout.addLayout(self._build_info(record))

        layout.addWidget(_heading("Raw Bytes (Hex / ASCII)"))
        hex_view = QPlainTextEdit()
        hex_view.setReadOnly(True)
        hex_view.setFont(QFont("Cascadia Mono, Consolas, monospace", 10))
        hex_view.setPlainText(_hex_dump(record.raw_bytes))
        layout.addWidget(hex_view, 1)

    @staticmethod
    def _build_info(record: PacketRecord) -> QFormLayout:
        form = QFormLayout()
        form.setSpacing(6)
        rows = {
            "Time": record.timestamp.isoformat(),
            "Direction": str(record.direction),
            "Interface": record.interface_name,
            "Protocol": record.protocol,
            "Process": f"{record.process_name or '—'} (PID {record.process_id or '—'})",
            "Source": f"{record.source_ip}:{format_port(record.source_port)}",
            "Destination": f"{record.destination_ip}:{format_port(record.destination_port)}",
            "Domain": record.domain_name or "—",
            "Length": format_size(record.length),
            "Summary": record.summary,
        }
        for key, value in rows.items():
            label = QLabel(key)
            label.setStyleSheet("color:#8b98a9; font-weight:600;")
            value_label = QLabel(str(value))
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_label.setWordWrap(True)
            form.addRow(label, value_label)
        return form


def _heading(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("SectionTitle")
    return label


def _hex_dump(raw: bytes | None) -> str:
    if not raw:
        return (
            "Raw bytes were not stored.\n"
            "Enable 'store_raw_payload' in the settings to display them."
        )
    lines: list[str] = []
    for offset in range(0, len(raw), 16):
        chunk = raw[offset : offset + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        hex_part = f"{hex_part:<47}"
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{offset:08x}  {hex_part}  {ascii_part}")
    return "\n".join(lines)
