# Contributing

Use Python 3.10 or newer on Linux. Create a virtual environment and install `.[dev]`.
Run `python -m pytest -q` with the Qt offscreen platform for automated checks.
Run `python -m build` to build wheel and source packages.

Before proposing UI changes, check all four detail modes, both transparent text colors,
and transparent/opaque backgrounds. Verify the tray recovery path and repeat application
launch. X11 and Wayland have different window-placement capabilities; document the
desktop and compositor used for any manual checks.

Sensor contributions must state the physical domain measured, units and whether the
domain overlaps an existing source. Include tests for missing permissions, invalid
readings, disconnects and suspend gaps. Do not infer watts from workload or CPU TDP.

Include reproduction steps, distribution, Python/Qt version and redacted startup errors
with bug reports. Do not upload your session database or full process environment.

Contributions are licensed under the repository's MIT license. Use the hosting platform's
pull requests for proposed changes and include the relevant test results.
