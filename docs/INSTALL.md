# Install and remove Wattpin

## Linux — one step

Run the supplied executable `Wattpin-0.4.4-Linux-x86_64.run` (or run
`bash Wattpin-0.4.4-Linux-x86_64.run` from a terminal). Python and pip are not needed.
No administrator password is required. The installer checks the bundled UI, creates
application-menu entries, enables login startup, and opens the widget when a desktop
connection is available. Quit an old pre-0.4 prototype from its tray before upgrading.

Open **Uninstall Wattpin** from the application menu and confirm removal. Your history
and preferences are kept. For a complete removal including personal history, use:

```bash
bash Wattpin-0.4.4-Linux-x86_64.run --uninstall --purge-data
```

The managed application lives in `~/.local/share/wattpin/application`. Data remains in
`~/.local/share/powerglass` for compatibility with earlier versions. XDG directory
overrides are respected. Installing a new version replaces the managed application
files and keeps data. Do not move the installed application folder.

Target: Linux x86-64 with a graphical desktop, tested on Linux Mint 22 / Ubuntu 24.04
family. This build requires glibc 2.39 or newer. Wayland placement/input pass through
still depends on the compositor. X11 remains the best-tested overlay target.

## Windows — setup wizard

Double-click **Wattpin-0.4.4-Windows-x64-Setup.exe**, accept the license, choose the
startup/shortcut options and install. Python, pip and a separate .NET runtime are not
needed. The app is installed for the current user, so setup does not need administrator
rights. The default destination is `%LOCALAPPDATA%\Programs\Wattpin`.

Remove it using **Windows Settings → Apps → Installed apps → Wattpin → Uninstall**, or
**Start → Wattpin → Uninstall Wattpin**. The uninstaller closes the app and removes
application files, shortcuts, registry entries and login startup. The wizard offers an
unchecked option to also delete power history and preferences; otherwise data is kept
at `%LOCALAPPDATA%\Wattpin`.

Silent deployment: `Wattpin-0.4.4-Windows-x64-Setup.exe /S`. Silent uninstall preserves
personal data. Install location may be supplied as the final argument, for example
`/D=C:\Tools\Wattpin` (do not wrap this NSIS argument in quotes).

Target: Windows 10 64-bit (1809 or newer), or Windows 11 64-bit. ARM64 is not a native
target. Installers are unsigned; this project has no code-signing certificate.

### Windows hardware access

The bundled read-only helper uses LibreHardwareMonitor 0.9.6. The UI starts as a normal
user. If CPU readings are unavailable, open Preferences → Sensors and choose **Enable
privileged hardware sensors**. Windows asks permission to elevate only the helper.
The widget itself remains unprivileged. An optional saved setting requests the helper
at login; this produces a Windows permission prompt, not a silent elevated task.

The helper sends readings through a private named pipe for the same Windows account.
It accepts no sensor-control commands, creates no network listener, and exits when
the widget exits. Denied permission, unsupported hardware, unavailable drivers, or a
blocked hardware-access driver can prevent readings. Standard-user accounts requiring
different administrator credentials may not connect to that administrator's private pipe.
The software does not bypass Windows driver protections.

Power domains are selected conservatively: CPU package and exposed DRAM, plus independent
GPU readings. Intel/AMD GPU readings are excluded from totals when CPU package power is
available unless you enable **Count AMD/Intel GPU separately** for a discrete GPU. This
avoids counting an integrated GPU twice. Unclassified rails remain informational.

The same design, four modes, transparency, font settings, W/derived A, position storage,
click through, session tracking, CSV exports, retention and batching are shared by both
platforms. Linux CPU counters measure elapsed energy; Windows helper power readings use
elapsed-time integration. Neither backend provides universal whole-PC wall measurement.

## What has been tested

* Automated calculation, domain selection, stale reading, settings, UI-mode, transparency,
  single-instance and shutdown tests on Linux.
* Linux frozen app startup, isolated install, live session write, removal and history retention.
* Windows PE executable built using Windows Python under Wine, bundled Qt/logo self-test,
  setup installation, application/preference rendering, uninstall and history retention in
  an isolated Wine prefix.
* Windows sensor-host cross-compiled successfully as a self-contained x64 executable.

Wine does not validate physical Windows drivers or sensor accuracy. A real Windows 10/11
hardware test is still required for sensor permissions, CPU/GPU readings, Explorer stacking,
click through and shutdown behavior. No Windows power-accuracy claim is inferred from Wine.

## Build installers from source

Linux: install `.[dev]` and PyInstaller; run `python packaging/build_app.py`, then
`python packaging/build_linux_installer.py`.

Windows: use `packaging/windows/build.ps1` on a Windows x64 machine with Python 3.11,
.NET SDK 8 and NSIS installed. It builds the app and helper, collects license materials,
and compiles setup. The GitHub Windows workflow performs these steps and smoke tests.
Release builds use one-folder payloads for low-overhead startup; only installation
decompresses the installer. Code signing can be added later using the maintainer's certificate.
