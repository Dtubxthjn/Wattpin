# Publication audit — Wattpin 0.4.4 beta

Updated on 20 October 2026. This report records the checks and remaining limits; it is
not a claim that the application is free of all bugs or a substitute for Windows hardware testing.

## Confirmed fixes

* **Superseding the earlier X11 layering fixes:** background placement uses a lowered
  dock instead of the wallpaper window type. This separates it from wallpaper
  stacking while keeping it below normal apps and visible during Show Desktop.
  `tools/check_x11_layer.py` checks six wallpaper raise/remap and Show Desktop
  cycles on Cinnamon, including normal-window ordering and absence of screen struts.
  No repeating recovery polling is added. Earlier desktop-type checks did not
  exercise wallpaper restacking and were insufficient to confirm a lasting fix.

* X11 background placement no longer combines the desktop type with the BELOW
  flag. Cinnamon could stack it below the wallpaper and deliver clicks there.
* Desktop-layer X11 dragging now moves the widget directly. Cinnamon could ignore
  a native move request even when Qt accepted it. A transparent widget was dragged
  using real X11 pointer events, and its final position was verified on disk.

* Cinnamon's Show Desktop hid the widget because it used the utility window type.
  Background placement now advertises the X11 desktop window type. Native testing
  confirmed it stays in Normal state during Show Desktop instead of becoming Iconic.
* Movement, resize and screen-layout events now trigger a debounced bounds check and
  save the corrected position. Recovery does not unhide intentionally hidden widgets
  or poll while idle. Native X11 testing recovered an intentionally off-screen move.
  Direct X server geometry is used for validation: wmctrl's coordinates were doubled
  for this undecorated window and were not reliable for diagnosing its real position.
* Native system dragging and manual dragging no longer compete for the same movement.
* Position restoration used fixed 340×180 bounds, causing a compact widget to move away
  from a saved screen edge. Bounds now use the actual widget size.
* Reapplying Ultra Low preferences could release its fixed width and expand the widget.
  Its width constraints are reapplied correctly.
* Simultaneous launches shared `show-request.tmp` and could race during rename. Requests
  now use unique temporary files and atomic replacement; a 100-request concurrency test covers this.
* A pending startup quit request could run before the Qt event loop started. Initial
  request processing is now queued through the event loop.
* Shutdown waited only 3.5 seconds although sensor work and helper cleanup can exceed
  that combined limit. Shutdown now waits for the worker to finish before destroying it.
* A broken Windows sensor pipe retained its last packet until the freshness timeout.
  Disconnection now clears the cached readings immediately.
* Boolean watt readings were accepted as 0/1, and external meter files had no read limit.
  Boolean power is rejected; meter packets are limited to 64 KiB.
* A failed database rollback could raise another unhandled exception in the UI callback.
  Rollback failure is now caught and logged.

## Verification

* 34 automated tests pass locally on Python 3.12, including calculation, counter rollover,
  duplicate-domain exclusion, sleep gaps, retention, persistence, transparent rendering,
  display modes, screen-edge placement, concurrency and single-instance quit handling.
* The Windows named-pipe path was checked against the exact Win32 character sequence.
  Its spelling was correct; the new test protects it from accidental escaping changes.
* Windows CI now executes regression tests in addition to building and smoke testing setup.
* Source and wheel builds are checked for icons, licenses and accidental runtime data.
* The 0.4.1 source ZIP passed all 28 tests after extraction into a separate folder.
* The 0.4.1 Linux and Windows installers completed installation and removal in isolated
  test locations. Installed applications pass startup checks and render a preview.
  Removal preserves a valid history database. Windows checks use Wine, not native Windows.
* The GitHub source ZIP is exported from the source package, excluding generated metadata,
  environments, binaries built during development and personal runtime data. It is scanned
  for common AWS/GitHub token and private-key patterns. This is a targeted pattern scan,
  not a guarantee that every possible secret format can be detected.

The Linux installer is rebuilt for 0.4.4. The last locally tested Windows binary is 0.4.1;
the 0.4.4 Windows build must run through the included Windows workflow. The sensor-host
source is unchanged from 0.4.0.

## Remaining publication limits

* Publish as **beta**. Actual Windows CPU/GPU sensors, driver permissions, Explorer
  layering and shutdown require testing on real Windows 10/11 hardware.
* Wine checks Windows executable loading and installer behavior; it cannot validate
  Windows hardware sensor accuracy. The hosted Windows workflow must run after upload.
* Wayland placement and click through depend on the compositor; X11 is better tested.
* Software component readings do not equal whole-PC wall power. Use a suitable external
  meter for a true whole-PC total. AC current remains derived from voltage and power factor.
* Installers are unsigned. No code-signing certificate is bundled.
* The public security-reporting contact must be configured by the repository owner.

## Publish the right files

Extract `dist/wattpin-0.4.4-github-source.zip` and upload the contents of its top-level
folder to the repository, including `.github` and `.gitignore`. Keep `dist`, `.venv`,
`build-output`, `build-work`, caches and personal session databases out of Git.
Attach the Windows setup executable, Linux `.run`, and `SHA256SUMS` as Release assets.

## Public-data hygiene

Published preview images use synthetic demo data. Local benchmark numbers are not
distributed. Source exports reject common credential formats, personal home paths,
private keys, environment files, settings, logs, and session databases. These checks
reduce accidental disclosure; they are not a guarantee against every secret format.

The layer choice follows the [EWMH stacking guidance](https://specifications.freedesktop.org/wm/latest-single/#STACKINGORDER) and is verified against the local window manager.
