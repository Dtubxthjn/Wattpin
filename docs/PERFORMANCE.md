# Resource measurements — 0.2.1

Local comparison on the development computer, Python 3.12, using actual Linux power
sensors. Each separate process used Ultra Low, transparent background, Qt offscreen,
three seconds of startup warmup and a 15-second measurement window. The before tree
was copied from version 0.2.0 before optimization. Both tests ran sequentially.

| Process metric | Before | After |
| --- | ---: | ---: |
| CPU, percentage of one logical core | 1.733% | 0.200% |
| Resident memory | 64.57 MiB | 64.66 MiB |
| Disk bytes written in measurement window | 274,432 | 73,728 |
| Write syscalls | 164 | 84 |
| Read syscalls | 420 | 118 |

This short local sample shows about 88% less process CPU and 73% fewer disk bytes written.
Memory is essentially unchanged. RSS includes shared Qt library pages and does not
represent wholly private memory. These are process measurements, not a measured reduction
in wall electricity. Results vary with fonts, desktop, detail mode, drivers and workload.
The NVIDIA power path was unavailable on the test environment; child-process CPU is not
included. Compatible NVIDIA systems still launch the vendor command for each reading.

Changes contributing to the savings:

* Discover hardware once per minute, cache sensor labels and ranges, read live counters
  each second. Hardware changes can take up to a minute to appear.
* Wait once between samples instead of waking every 50 ms.
* Use filesystem events for second-launch requests instead of a polling timer.
* Avoid hidden graph repaints and hidden-label formatting in Ultra Low.
* Resize the watt label only when it needs more room.
* Batch durable database commits at five-second intervals and flush on normal shutdown.
* Destroy closed preferences windows to release their controls and font lists.

Every sample still contributes to energy integration. Display mode does not affect
sampling. Abrupt power loss or forced termination may lose up to the uncommitted interval;
choose a one-second commit interval in Preferences → Sessions for stronger persistence.
The default interval is five seconds, configurable from 1–15 seconds.

Reproduce with the developer-only `psutil` dependency and `tools/benchmark.py`. Keep
the same sensor permissions and graphics backend for both runs. Longer or repeated
measurements are appropriate before making hardware-wide performance claims.
