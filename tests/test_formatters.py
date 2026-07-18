"""Unit conversion and formatting tests."""

from network_monitor.utils.formatters import format_port, format_rate, format_size


def test_format_rate_bytes() -> None:
    assert format_rate(512) == "512 B/s"


def test_format_rate_kilobytes() -> None:
    assert format_rate(1536) == "1.5 KB/s"


def test_format_rate_megabytes() -> None:
    assert format_rate(12.4 * 1024 * 1024) == "12.4 MB/s"


def test_format_rate_negative_clamped() -> None:
    assert format_rate(-100) == "0 B/s"


def test_format_size_gigabytes() -> None:
    assert format_size(2 * 1024**3) == "2.0 GB"


def test_format_port_none() -> None:
    assert format_port(None) == ""
    assert format_port(443) == "443"
