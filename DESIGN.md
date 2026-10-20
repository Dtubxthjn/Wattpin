# Implementation plan and boundaries

1. Use a native Qt desktop window, rather than a browser overlay, to support transparent
   backgrounds, window stacking and input pass through without running a local web server.
2. Discover sensors from the running kernel. Read energy counters where available, then
   direct board power. Explicitly exclude nested/duplicate domains from totals. Never
   guess total PC power from CPU usage, CPU model or TDP.
3. Keep collection in a dedicated thread, one second apart regardless of display mode.
   CPU power comes from elapsed energy, not a single instantaneous load observation.
   All polling necessarily has an interval; hardware counters retain intervening CPU energy.
4. Persist sample energy to SQLite independently of presentation, batching commits at a
   configurable interval (default five seconds) and flushing on normal shutdown. Use real elapsed time,
   detect sleep using wall and monotonic clocks, and record coverage gaps honestly.
5. Offer compact, summary and detailed presentation from the same stream. Recover control
   of locked windows through the tray; disable lock when a tray is unavailable.
6. Make full wall measurement an optional external input. Estimated overhead/PSU conversion
   is explicitly opt in, has no claim of universal accuracy and does not rewrite recorded
   component energy. Derived AC amps always depend on supply voltage and power factor.
7. Register user-level graphical autostart. Keep the application unprivileged and preserve
   session records on shutdown. Do not modify sensor permissions automatically.

Implemented checks cover energy counter deltas, wraparound, child-domain exclusion,
meter freshness, invalid data, energy integration, persistent export, suspend gaps,
mode changes and preference persistence. Offscreen screenshots use actual sensors.

Remaining physical acceptance checks require the user's graphical desktop and hardware:
drag and restore on the chosen window manager; click through over desktop icons; bottom
stacking behind apps; real login/shutdown cycle; comparison with a physical wall meter.
The development environment has no display connection. Wayland may require a compositor
extension for stronger desktop placement guarantees; this version uses portable Qt hints.
