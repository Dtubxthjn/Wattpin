## Wattpin 0.4.4 Beta

A quiet desktop power monitor for Linux and Windows, with four detail levels,
transparent placement, session energy history, and CSV exports.

### Downloads

| File | Use |
| --- | --- |
| `Wattpin-0.4.4-Linux-x86_64.run` | Self-contained Linux x86-64 installer; Ubuntu 24.04 / glibc 2.39 or newer |
| `Wattpin-0.4.4-Windows-x64-Setup.exe` | Windows 10 1809+ / Windows 11 x64 setup wizard |
| `wattpin-0.4.4-py3-none-any.whl` | Python package; Python 3.10+ and platform runtime dependencies required |
| `wattpin-0.4.4.tar.gz` | Python source distribution |
| `wattpin-0.4.4-github-source.zip` | Clean source checkout with tests and build tooling |
| `SHA256SUMS` | SHA-256 checksums for the five files above |

### Fixed in this release

The Linux X11 widget now uses a separate layer above wallpaper and below ordinary
applications. This fixes the recurring wallpaper-covering issue while preserving
Show Desktop, direct dragging, and click-through locking. No extra polling timer
is added.

The old build failed a real Cinnamon wallpaper-restacking check. The replacement
passed six wallpaper raise/remap and Show Desktop cycles, including the frozen
app with locked placement. All 34 automated tests passed locally.

### What's included

- Ultra Low, Low, Medium, and High detail modes with independent background collection.
- Transparent backgrounds, adjustable typography, drag placement, and click through where supported.
- Local session storage, retention settings, and separate CSV exports for readings and totals.
- Linux RAPL and supported GPU readings; Windows hardware access through a separate read-only helper.
- Optional local JSON bridge for an external wall-power meter.
- Placement, shutdown, concurrency, and invalid-reading fixes documented in the changelog.
- Synthetic public previews and publication checks for common credential and private-file patterns.

### Installation

Linux: run `bash Wattpin-0.4.4-Linux-x86_64.run` in your graphical desktop session.
Windows: open the setup executable. Existing settings and history are retained by default.

### Before using the beta

Component sensors are a **partial PC total**, not electricity measured at the outlet.
A true whole-PC reading requires a suitable external meter. Derived current and estimated
wall power are labeled accordingly.

Installers are unsigned. Wayland placement and click through depend on the compositor.
Windows CI checks installation and application startup, but physical Windows sensor
accuracy, driver permissions, and desktop behavior still need real-hardware validation.

These downloads are built on fresh GitHub-hosted runners. They do not include personal
settings, session databases, or local developer build artifacts. Public source previews
use synthetic data. Pattern scans cannot guarantee detection of every possible secret.

See the repository's installation guide, release audit, and third-party notices for details.
