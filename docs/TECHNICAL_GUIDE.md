# Wattpin technical guide

Detailed measurement semantics, desktop behavior, storage, and development notes.

[Back to the project](../README.md) · [Install and remove](INSTALL.md)

## Run from source

```bash
cd Wattpin
python3 -m venv .venv
.venv/bin/pip install -e .
bash run.sh
```

Use Python 3.10+ and a Linux graphical session. On Ubuntu/Mint x86-64 the source release
includes the cursor compatibility library that fixed startup on the development computer.
On other distributions install Qt/XCB runtime dependencies from your package manager.
The Python wheel excludes the Ubuntu-specific binary; Ubuntu/Mint users installing the
wheel should install `libxcb-cursor0` with their package manager. X11 is the best-tested
desktop target; see the Wayland limits below.

The desktop launcher and `run.sh` load the bundled Ubuntu x86-64 cursor library before
starting Qt. This fixes silent startup failures when `libxcb-cursor0` is missing. Other
distributions should install their Qt/XCB runtime dependencies with their package manager.
Startup diagnostics are saved to `~/.local/share/powerglass/startup.log`. Opening the app
again brings up preferences for the existing instance instead of silently doing nothing.

Right-click the unlocked widget or use its tray menu to change detail, open preferences,
export sessions, lock placement or quit. Preferences allow font, size, opacity, transparent
background, light/dark transparent text, W/A, supply voltage, power factor and optional
wall estimation. Medium adds a 90-sample graph; High adds sources and child domains.
Unlock to drag, then lock to pass clicks through to the desktop. Without a system tray,
locking is disabled so the controls remain reachable. Position and settings persist.

### Start at login

After installing dependencies, run:

```bash
.venv/bin/python install.py --autostart
```

This installs a user application launcher and graphical-login autostart entry. No root
required. Keep this project folder in place. The app starts when your graphical desktop
starts and ends at logout/shutdown. It cannot capture boot, firmware, or prelaunch energy.
Remove the launchers using `.venv/bin/python install.py --remove`; data is preserved.

## Measurement and accuracy

* Linux RAPL: power = change in energy / actual monotonic elapsed seconds. Energy counters
  retain energy between samples, including activity too brief to see on the display.
  Package and DRAM domains enter totals; core/uncore child domains are informational.
  MMIO mirrors and sysfs aliases are excluded. Counter rollover is handled.
* GPU: NVIDIA `nvidia-smi` board draw or AMD/Nouveau hwmon power, if supported.
  GPU direct power is integrated with the trapezoid rule; subinterval spikes can be missed.
* No TDP/load guesses, fixed hardware tables, mandatory calibration, or invented disk/fan
  wattages. RAPL and board power themselves have hardware-specific accuracy limits.
* **Monitored components is a partial PC total**, not total electricity from the outlet.
  Unmetered motherboard, storage, RAM, peripherals and PSU losses can be substantial.
  RAM appears only if a DRAM energy domain exists. A true total requires a suitable
  external wall power meter that measures only this PC.
* Optional estimated wall draw = (monitored W + user-entered unmetered W) / PSU efficiency.
  This is explicitly labeled estimated and does not alter recorded sensor energy.
* AC current is derived using **I = W / (V × power factor)**; it is not a measured rail
  current. Configure your actual supply voltage and PF. Without measured PF it is approximate.
  Voltage is a conversion setting, not a selectable consumption unit.
* One-second sampling runs in a background thread, independently of display mode. There
  is no software measurement without a sampling interval; counters minimize lost CPU
  energy between samples. Hardware topology is cached for 60 seconds; live counters are
  still read each second. NVIDIA failures back off for 60 seconds. No polling on the UI thread.
* Gaps longer than 10 seconds, missing readings and changes in sensor coverage are not
  interpolated. The measured-time count excludes them. Sleep/suspend is not counted as
  active measured time. Session energy can contain both partial-component and whole-PC
  intervals if the meter becomes unavailable; CSV preserves each interval's scope.

### Optional external meter bridge

Configure a local JSON file in Preferences → Sensors. Have a bridge for your own meter
atomically update it at least every five seconds:

```json
{"timestamp": 1792060000.0, "watts": 123.4}
```

`timestamp` is current Unix time, not the example value. The app rejects stale/future,
negative and nonfinite readings. A fresh wall reading supersedes all component totals.
The bridge itself is meter-specific and is not included. No network ports are opened.

### Sensor permissions

Some distributions restrict `/sys/class/powercap/.../energy_uj` to root. The Sensors tab
shows the exact failed paths. The app never changes permissions or launches as root.
Ask your administrator for a narrowly scoped, read-only powercap policy appropriate to
your distribution. Without readable sensors it displays unavailable, not a false total.

### Desktop compatibility

Qt window flags request a frameless, nonfocusing, bottom-stacked, input-transparent
window. X11 window managers generally support this. Wayland compositors may prevent
absolute positioning, bottom stacking, or click through. On such desktops, use an X11
login session for predictable placement. This is a desktop widget, not a wallpaper engine
or a compositor extension. Appearance uses translucent color rather than compositor blur.

## Storage and verification

Data lives in `$XDG_DATA_HOME/powerglass` (default `~/.local/share/powerglass`). Settings
are validated and atomically replaced. All samples are integrated each second; SQLite WAL
commits batches every five seconds with full sync and always flushes on normal shutdown.
Preferences → Sessions allows a 1–15 second commit interval. Abrupt power loss or forced
termination may lose the uncommitted interval. Changing display mode never changes collection;
`ended` is null for interrupted sessions. Detailed readings are retained for seven days
by default (configurable from 1–365 days in Preferences → Sessions); pruning runs hourly
and freed database pages are reused. Session totals remain indefinitely. Export retained
readings or all session totals separately in Preferences. One instance per data directory
is enforced. Sensor errors produce unavailable readings and retry without stopping collection.

```bash
.venv/bin/pip install pytest
.venv/bin/python -m pytest -q
QT_QPA_PLATFORM=offscreen .venv/bin/python -m powerglass.app --data-dir /tmp/powerglass-preview --screenshot preview.png --preferences
```

The public preview generator uses synthetic demonstration readings and temporary settings. It never reads local hardware, personal settings, or session history.

## Open-source development and releases

```bash
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/python -m build
QT_QPA_PLATFORM=offscreen .venv/bin/python -m tools.preview
```

The wheel and source archive are produced in `dist/`. The source archive includes tests,
desktop installer, documentation, source-checkout compatibility library and its license.
The wheel includes the application, icon and project license notices. No session database,
user settings or virtual environment belongs in a release. CI checks Python 3.10, 3.12
and 3.13; local verification has been performed on Python 3.12 and the current Cinnamon X11
desktop. Other matrix versions require the hosted CI run after publication.

See [CONTRIBUTING](../CONTRIBUTING.md), [SECURITY](../SECURITY.md),
[CHANGELOG](../CHANGELOG.md) and [third-party notices](../THIRD_PARTY_NOTICES.md).
For publication, use the clean `wattpin-0.4.4-github-source.zip` archive. Upload its contents
to the repository and attach installers separately to a GitHub Release. Do not upload
the complete development folder. See [the release audit](RELEASE_AUDIT.md).

## Resource use

The collector sleeps until its next reading instead of waking 20 times a second. Hardware
discovery and static metadata are cached, the app-menu recovery signal uses filesystem
events instead of a polling timer, and hidden graphs/labels do not repaint. Ultra Low
updates only its watt label. Closed preferences windows are destroyed to release their
controls and font lists. See [the benchmark notes](PERFORMANCE.md) for measurements
and limits. NVIDIA still uses its driver command, so its cost depends on that driver.

Developer comparison (requires `psutil`, not needed to run the app):

```bash
.venv/bin/python -m tools.benchmark /path/to/previous-source /path/to/current-source
```

Design references: [Linux powercap](https://www.kernel.org/doc/html/latest/power/powercap/powercap.html),
[NVIDIA board monitoring](https://docs.nvidia.com/deploy/nvidia-smi/index.html),
[Qt window behavior](https://doc.qt.io/qt-6/qt.html).
