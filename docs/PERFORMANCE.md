# Resource measurement methodology

This document describes how to benchmark Wattpin without publishing a developer's
hardware readings, session history, or local resource measurements.

## Run a local comparison

The optional benchmark utility uses `psutil` and is separate from the application runtime:

```bash
python -m tools.benchmark /path/to/previous-source /path/to/current-source
```

Use the same desktop backend, font, display mode, sensor permissions, warmup period,
and measurement duration for each run. Keep the resulting measurements local unless
you explicitly choose to share them.

Check process CPU, resident memory, disk bytes written, and write syscalls. RSS includes
shared Qt pages and is not wholly private memory. Process resource measurements do not
prove a reduction in whole-PC wall electricity. Compatible NVIDIA systems invoke the
vendor command, whose cost depends on the driver.

## Design choices

- Live counters are read every second; hardware topology is cached for 60 seconds.
- The collector sleeps between readings.
- Hidden graphs and labels avoid repainting.
- Disk commits are batched, with a normal-shutdown flush.
- Closed preferences windows release their controls.

Every sample still contributes to energy integration. Display mode does not change the
sampling interval. Forced termination may lose uncommitted readings; the commit interval
is configurable from one to fifteen seconds.

No personal benchmark dataset is distributed with this project.
