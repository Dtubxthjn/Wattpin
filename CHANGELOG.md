# Changelog

## 0.4.4

* Retry temporary Windows file-sharing conflicts during concurrent launch requests,
  with a bounded wait and cleanup on failure.
* Replace the X11 desktop window type with a lowered dock: above wallpaper, below
  ordinary applications, immune to Show Desktop, without reserving screen space.
* Retain direct dragging and click-through locking for background placement.
* Add a real X11 integration check with repeated wallpaper raise/remap and Show
  Desktop cycles, including an option to check frozen builds with isolated data.

## 0.4.3

* Avoid combining the X11 desktop window type with BELOW, which can place the
  widget behind the wallpaper and prevent it from receiving pointer input.
* Fix dragging on X11 desktop-layer widgets: move directly instead of asking the
  window manager to move a desktop window. Keep native dragging for other windows.
* Test saved drag position and locked placement; verify transparent dragging with
  native X11 pointer events. No new runtime dependencies or repeating timers.

## 0.4.2

* Keep the X11 background widget visible during Show Desktop using the desktop window type.
* Recover widgets moved outside the visible display after movement, resizing,
  monitor layout or scale changes, and save the corrected position.
* Avoid competing manual and window-manager drag operations.
* Keep intentional hiding and desktop layering; recovery uses existing events,
  with no repeating visibility timer.

## 0.4.1

* Fix widget position restoration near screen edges using its actual dimensions.
* Preserve Ultra Low width constraints when applying appearance preferences again.
* Use unique atomic request files for concurrent app launches and process pending
  startup requests after the Qt event loop starts.
* Wait for sensor cleanup before destroying its worker thread during shutdown.
* Clear cached readings immediately when the Windows sensor pipe disconnects.
* Reject boolean watt values and bound external-meter reads to 64 KiB.
* Guard database rollback failures, add regression tests and Windows CI test execution.
* Expand ignore rules and add a clean GitHub source export and release audit report.

## 0.4.0

* Self-contained Linux one-step installer and application-menu uninstaller.
* Windows x64 application with the same Qt design, modes, transparent display and tracking.
* Modern setup/uninstall wizard, shortcuts, optional sign-in startup and data-retention choice.
* Bundled self-contained LibreHardwareMonitor sensor helper, private read-only named pipe,
  explicit privileged-sensor option and conservative integrated-GPU accounting.
* Windows data in LocalAppData, shared font, frozen executable self-test, graceful quit IPC,
  Windows session-end flush, packaging workflows and cross-platform backend tests.
* Installer tests on Linux and in isolated Wine; real Windows hardware validation remains.

## 0.3.0

* Rename the application to Wattpin and introduce a meter-and-pin app/tray logo.
* Remove the name/live heading and coverage heading from the overlay. Measurement
  scope remains accessible in its tooltip and sensor preferences.
* Preserve the existing storage location, session history, desktop launcher identity
  and legacy command so upgrades keep user preferences and autostart behavior.

## 0.2.1

* Cache sensor topology and static metadata for 60 seconds while reading live counters
  every second. Back off failed NVIDIA queries for 60 seconds.
* Replace frequent thread wakeups with an interruptible wait and app-menu polling with
  filesystem notifications. Skip rendering hidden content and release closed preferences.
* Batch disk commits every five seconds by default, configurable from 1–15 seconds, with
  a final flush at normal shutdown. Abrupt power loss can lose the uncommitted interval.
* Add resource comparisons and regression coverage for caching, batching, shutdown,
  and immediate collector interruption.

## 0.2.0

* Fieldnote visual design: warm paper, graphite text, vermilion instrument marks.
* Ultra Low mode displays only live watts and the W unit.
* True transparent backgrounds with light/dark text for different wallpapers.
* Settings validation, sensor-worker recovery, durable SQLite WAL storage and bounded
  detailed-history retention; session totals remain available for separate CSV export.
* MIT license, dependency notices, contribution guide, tests and release packaging.

## 0.1.0

* Initial native Linux widget, RAPL/GPU discovery, preferences and session tracking.
* Bundled source-checkout cursor library and launcher diagnostics.
