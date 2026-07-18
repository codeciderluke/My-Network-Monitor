"""Application configuration constants and loader."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class CaptureConfig:
    default_interface: str = ""
    bpf_filter: str = "ip or ip6"
    queue_size: int = 50_000
    store_raw_payload: bool = False


@dataclass(slots=True)
class UiConfig:
    refresh_interval_ms: int = 250
    chart_interval_ms: int = 1000
    max_visible_rows: int = 10_000
    auto_scroll: bool = True
    max_logs_per_ui_tick: int = 300


@dataclass(slots=True)
class StorageConfig:
    enable_sqlite: bool = False
    database_path: str = "./data/traffic.db"
    batch_size: int = 100
    flush_interval_ms: int = 1000


@dataclass(slots=True)
class LoggingConfig:
    level: str = "INFO"
    file_path: str = "./logs/my-network-monitor.log"


@dataclass(slots=True)
class AppConfig:
    """Overall application configuration."""

    capture: CaptureConfig = field(default_factory=CaptureConfig)
    ui: UiConfig = field(default_factory=UiConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def load(cls, path: str | Path | None = None) -> AppConfig:
        """Load config from a TOML file, or defaults if absent."""
        config = cls()
        if path is None:
            return config
        file_path = Path(path)
        if not file_path.exists():
            return config
        with file_path.open("rb") as fp:
            data = tomllib.load(fp)
        _apply_section(config.capture, data.get("capture", {}))
        _apply_section(config.ui, data.get("ui", {}))
        _apply_section(config.storage, data.get("storage", {}))
        _apply_section(config.logging, data.get("logging", {}))
        return config


def _apply_section(target: object, values: dict[str, object]) -> None:
    for key, value in values.items():
        if hasattr(target, key):
            setattr(target, key, value)


# Threading / queue constants (spec 10.1, 14.3)
RAW_QUEUE_MAXSIZE = 50_000
PARSED_QUEUE_MAXSIZE = 20_000
UI_QUEUE_MAXSIZE = 10_000
STORAGE_QUEUE_MAXSIZE = 50_000

MAX_LOGS_PER_UI_TICK = 300
MAX_VISIBLE_LOG_ROWS = 10_000

HISTORY_SECONDS = 60
PROCESS_CACHE_INTERVAL_MS = 1500
