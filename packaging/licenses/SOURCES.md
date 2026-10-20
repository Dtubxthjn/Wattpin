# Binary dependency source locations

The Windows application bundles Python 3.11.9 and Qt/PySide6 6.8.3. The Linux application
was built with Python 3.12 and Qt/PySide6 6.12.0. Qt and PySide libraries are dynamically
loaded and may be replaced with compatible builds. This project does not prohibit
reverse engineering for debugging modifications to those libraries.

* Python: https://www.python.org/downloads/source/
* Qt 6.8.3 source: https://download.qt.io/archive/qt/6.8/6.8.3/single/
* Qt 6.12.0 source: https://download.qt.io/archive/qt/6.12/6.12.0/single/
* Qt for Python: https://code.qt.io/cgit/pyside/pyside-setup.git/ (tags v6.8.3, v6.12.0)
* LibreHardwareMonitor 0.9.6, unmodified:
  https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/tree/v0.9.6
  commit 3d331e3370efb858411f19511373eff65a218701
* .NET runtime 8.0: https://github.com/dotnet/runtime
* XCB cursor 0.1.4: https://xcb.freedesktop.org/
* DejaVu fonts: https://dejavu-fonts.github.io/

The sensor-host application source is included in packaging/sensor-host. Dependency
licenses and the hardware library's third-party notices accompany the binary installer.
