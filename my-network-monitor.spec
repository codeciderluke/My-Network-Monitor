# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for My Network Monitor (single-file Windows exe)."""

import re
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

# Single source of truth: read __version__ from the package.
_init = Path("src/my_network_monitor/__init__.py").read_text(encoding="utf-8")
_version = re.search(r'__version__\s*=\s*"([^"]+)"', _init).group(1)
_parts = [int(p) for p in _version.split(".")]
while len(_parts) < 4:
    _parts.append(0)
_ver_tuple = tuple(_parts[:4])

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=_ver_tuple,
        prodvers=_ver_tuple,
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct("CompanyName", "Codecider Lab"),
                        StringStruct("FileDescription", "My Network Monitor"),
                        StringStruct("FileVersion", _version),
                        StringStruct("InternalName", "MyNetworkMonitor"),
                        StringStruct(
                            "LegalCopyright", "© 2026 Codecider Lab. MIT License."
                        ),
                        StringStruct("OriginalFilename", "MyNetworkMonitor.exe"),
                        StringStruct("ProductName", "My Network Monitor"),
                        StringStruct("ProductVersion", _version),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [0x0409, 0x04B0])]),
    ],
)

# Scapy imports its protocol layers dynamically; collect them explicitly.
hiddenimports = collect_submodules("scapy")

a = Analysis(
    ["src/my_network_monitor/main.py"],
    pathex=["src"],
    binaries=[],
    datas=[("assets/styles/dark.qss", "assets/styles")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PySide6.QtQml", "PySide6.Qt3DCore"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MyNetworkMonitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon="assets/icons/app.ico",
    version=version_info,
)
