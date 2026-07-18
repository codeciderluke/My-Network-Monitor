# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for My Network Monitor (single-file Windows exe)."""

from PyInstaller.utils.hooks import collect_submodules

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
)
