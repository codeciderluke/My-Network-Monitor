# Third-Party Licenses

Network Traffic Monitor is released under the MIT License (see `LICENSE`).
It depends on the following third-party packages, each under its own license.

| Package | License | Notes |
|---|---|---|
| [PySide6](https://www.qt.io/qt-for-python) | LGPL v3 (also GPL / commercial) | Qt for Python; used via dynamic linking. |
| [pyqtgraph](https://www.pyqtgraph.org/) | MIT | Real-time plotting. |
| [Scapy](https://scapy.net/) | **GPL v2** | Packet capture/parsing (strong copyleft). |
| [psutil](https://github.com/giampaolo/psutil) | BSD 3-Clause | Process / connection lookup. |

## Important: distribution notes

- **Source distribution.** This repository contains only Codecider Lab's own
  code under the MIT License. Users install the dependencies themselves via
  `pip`, so each dependency remains under its own license.

- **Bundled binary distribution (e.g. a PyInstaller `.exe`).** A single
  executable that bundles Scapy (GPL v2) constitutes a combined work. When you
  distribute such a binary you must comply with the GPL v2 obligations for the
  combined work — in particular, making the corresponding source available.
  PySide6's LGPL v3 additionally requires that users be able to relink against
  a modified Qt. If you plan to publish a prebuilt binary, review these
  obligations or replace Scapy with a permissively licensed capture backend.

Full license texts are available in each package's distribution and at the
links above.
