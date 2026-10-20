<p align="center">
  <img src="docs/images/cover.svg" width="100%" alt="Wattpin — Your PC's power. In plain sight. A quiet desktop widget with real sensors and local history." />
</p>

<p align="center">
  <a href="#get-started">Get started</a> ·
  <a href="#a-widget-that-knows-when-to-get-out-of-the-way">Preview</a> ·
  <a href="docs/INSTALL.md">Installation guide</a> ·
  <a href="docs/TECHNICAL_GUIDE.md">How it works</a> ·
  <a href="CONTRIBUTING.md">Contribute</a>
</p>

<p align="center">
  <a href="https://github.com/Dtubxthjn/Wattpin/actions/workflows/checks.yml"><img src="https://github.com/Dtubxthjn/Wattpin/actions/workflows/checks.yml/badge.svg" alt="Checks" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-d4ad46?style=flat-square&amp;labelColor=151515" alt="MIT license" /></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-d4ad46?style=flat-square&amp;labelColor=151515" alt="Python 3.10 or newer" />
</p>

**Wattpin keeps power consumption visible without turning your desktop into a dashboard.**
Pin a tiny watt readout to your wallpaper, or expand it to reveal a live graph, component
readings, and session energy. Collection continues in the background, whichever view you choose.

No account. No cloud service. No telemetry. Your history stays on your computer.

> **Know what the number means.** Component sensors provide a partial PC total.
> Whole-PC wall power requires a suitable external meter. Wattpin shows unavailable
> readings honestly and labels estimates explicitly.

---

## A widget that knows when to get out of the way

<p align="center">
  <img src="docs/images/medium.png" width="420" alt="Actual Wattpin Medium view with live watts, a power graph, CPU readings, and session energy" />
</p>

<p align="center"><sub>Actual application capture on Linux. Readings and sensor coverage depend on your hardware.</sub></p>

| Quiet on the desktop | Useful under the surface |
| :--- | :--- |
| **Four detail levels** — from a floating number to a sensor breakdown | **Session energy** — local SQLite history and CSV exports |
| **Transparent mode** — light or dark text, adjustable font and opacity | **Sensor-aware totals** — overlapping domains excluded conservatively |
| **Drag, place, lock** — click through after locking where supported | **Independent collection** — one-second samples across all display modes |
| **Start at login** — optional desktop integration | **External meter input** — a local JSON bridge for whole-PC readings |

### Four views. One collector.

| Ultra Low | Low | Medium | High |
| :--- | :--- | :--- | :--- |
| Live watts only | Draw, derived current, session energy | Graph and component readings | Sources and nested sensor domains |

<table>
  <tr>
    <td align="center" width="50%"><strong>Low / stay focused</strong><br /><br /><img src="docs/images/low.png" width="384" alt="Wattpin Low mode" /></td>
    <td align="center" width="50%"><strong>High / inspect the details</strong><br /><br /><img src="docs/images/high.png" width="390" alt="Wattpin High mode with sensor sources" /></td>
  </tr>
</table>

<details>
<summary><strong>Appearance, sensors, and session preferences</strong></summary>
<br />
<p align="center"><img src="docs/images/preferences.png" width="620" alt="Wattpin preferences: detail level, units, text color, font, opacity, transparency, and placement controls" /></p>
Right-click the unlocked widget or use the tray menu to open Preferences. If the app is
already running, launching it again brings up its preferences.
</details>

---

## Get started

**Version 0.4.3 is beta.** Linux X11 is the best-tested desktop target.
Windows support is included; native Windows hardware validation remains pending.

### Run from source

Use **Python 3.10+** and a graphical desktop. On Linux:

```bash
git clone https://github.com/Dtubxthjn/Wattpin.git
cd Wattpin
python3 -m venv .venv
.venv/bin/python -m pip install -e .
bash run.sh
```

The source checkout includes an Ubuntu/Mint x86-64 cursor compatibility library.
Other distributions may need their Qt/XCB runtime packages. X11 is recommended for
predictable placement and click through; Wayland behavior depends on the compositor.

For Windows source setup, use a virtual environment, install the project, and run `wattpin`.
The packaged Windows build also includes the separate hardware sensor helper.
See the [Windows hardware access and build guide](docs/INSTALL.md#windows-hardware-access).

### Installers and builds

The project includes build tooling for a Linux `.run` installer and a Windows setup wizard.
Downloadable installers, when published, belong in [GitHub Releases](https://github.com/Dtubxthjn/Wattpin/releases).
The Windows setup can also be built through the repository's **Windows installer** workflow.

The Linux 0.4.3 installer has been built locally. The last locally tested Windows
installer is 0.4.1; a Windows 0.4.3 binary requires the included Windows build workflow.
See the [release audit](docs/RELEASE_AUDIT.md) for tested platforms and remaining limits.

[Full installation and removal guide →](docs/INSTALL.md)

---

## Real sensors. Clear boundaries.

```mermaid
flowchart LR
    A[Linux: RAPL + GPU sensors] --> C[Background collector]
    B[Windows: sensor helper] --> C
    M[Optional local wall-meter JSON] --> C
    C --> D[Scope-aware readings]
    D --> E[Desktop widget]
    D --> F[Local SQLite history]
    F --> G[CSV export]
```

- **Linux CPU energy:** RAPL energy-counter changes divided by actual elapsed time.
- **GPU power:** supported NVIDIA, AMD, or Nouveau readings, depending on platform and hardware.
- **Whole-PC power:** a fresh external-meter reading supersedes component totals.
- **No invented watts:** no CPU-load/TDP guesses or fixed disk, fan, and motherboard allowances.
- **Current is derived:** `A = W / (V × power factor)`. It is not a measured rail current.
- **Gaps stay gaps:** suspend, missing sensors, or coverage changes are not silently interpolated.

Optional wall-power estimates use user-entered allowances and PSU efficiency. They are
labeled estimates and do not change recorded sensor energy.

[Measurement details, permissions, and persistence →](docs/TECHNICAL_GUIDE.md#measurement-and-accuracy)

## Built to stay local

Wattpin uses Python and Qt (PySide6), with SQLite session storage. The Windows hardware
helper uses .NET and LibreHardwareMonitor. The widget runs as your user; optional Windows
hardware access elevates only its read-only sensor helper with your permission.

History and settings remain in the legacy `powerglass` data location for upgrade
compatibility. The default database commit interval is five seconds; abrupt termination
can lose uncommitted readings. Retained detailed readings are pruned, while session totals
remain. [Storage behavior →](docs/TECHNICAL_GUIDE.md#storage-and-verification)

Previously **Powerglass**. The Python package and storage identity keep that name so
existing preferences and history continue to work.

---

## Develop and contribute

```bash
python -m pip install -e '.[dev]'
QT_QPA_PLATFORM=offscreen python -m pytest -q
python -m build
```

The existing suite covers energy integration, rollover, domain selection, storage,
UI modes, IPC, and sensor failure behavior. CI runs the Linux suite on Python 3.10,
3.12, and 3.13; the Windows installer workflow includes regression and installation checks.

Bug reports, desktop compatibility notes, and carefully scoped sensor contributions are welcome.

| Project resources | |
| :--- | :--- |
| [Contributing](CONTRIBUTING.md) | Development and validation expectations |
| [Technical guide](docs/TECHNICAL_GUIDE.md) | Measurement, desktop behavior, storage, and source use |
| [Performance notes](docs/PERFORMANCE.md) | Local benchmark methodology and its limits |
| [Release audit](docs/RELEASE_AUDIT.md) | Verification record and beta limitations |
| [Changelog](CHANGELOG.md) | Release history |
| [Security](SECURITY.md) · [Third-party notices](THIRD_PARTY_NOTICES.md) | Privacy, reporting, and dependencies |

<p align="center"><sub>MIT licensed. A small instrument for a more understandable desktop.</sub></p>
