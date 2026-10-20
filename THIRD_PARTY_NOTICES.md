# Third-party software

Wattpin source is MIT licensed. Dependency licenses remain their own.

* Source installations load PySide6 / Qt for Python as a separate dependency. Standalone
  installers bundle dynamically loaded Qt/PySide6 libraries, LGPL/GPL texts and dependency
  license materials. Compatible libraries can be replaced; there is no restriction on
  reverse engineering to debug library modifications. Source locations and build versions
  are listed in `packaging/licenses/SOURCES.md`, also copied to binary `licenses/` folders.
  Upstream: https://doc.qt.io/qtforpython-6/licenses.html
* The source checkout includes Ubuntu Noble amd64 `libxcb-cursor0` 0.1.4-1build1, an
  MIT/X-licensed compatibility library. Its complete attribution and license are at
  `vendor/usr/share/doc/libxcb-cursor0/copyright`. Source:
  https://xcb.freedesktop.org and Ubuntu's xcb-util-cursor source package.
  The packaged wheel does not contain this platform-specific library; install the
  distribution's runtime dependency when using the wheel on another computer.
* Windows sensor helper: LibreHardwareMonitorLib 0.9.6 (unmodified), MPL-2.0, with its
  dependency notices and source location included. The helper's own source is MIT and is
  included under `packaging/sensor-host`. It uses a self-contained .NET 8 runtime and
  NuGet dependencies whose available license notices and package manifests are copied
  into the binary distribution. Source: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/tree/v0.9.6
* DejaVu Sans Mono is bundled for consistent appearance. Its complete attribution and
  font license are in `powerglass/assets/FONT-LICENSE.txt`.
* Standalone applications bundle Python. The binary license folder includes the Python
  license; source installation uses the user's existing Python. PyInstaller's bootloader
  is distributed under its GPL exception permitting application bundling.

No third-party reference image is included in the source release.
