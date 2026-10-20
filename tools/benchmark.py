"""Compare two source trees with identical real-sensor, offscreen workloads."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import psutil  # developer-only measurement dependency, not required by the application


def measure(source, seconds=15):
    with tempfile.TemporaryDirectory(prefix='powerglass-benchmark-') as directory:
        data = Path(directory)
        (data/'settings.json').write_text(json.dumps(dict(mode='Ultra Low', transparent=True)))
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen', PYTHONPATH=str(source))
        process = subprocess.Popen([sys.executable, '-m', 'powerglass.app', '--data-dir', directory],
                                   cwd='/tmp', env=env, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        try:
            time.sleep(3)
            assert process.poll() is None, 'Benchmark app failed to start'
            observed = psutil.Process(process.pid)
            cpu = observed.cpu_times()
            io = observed.io_counters()
            begin = time.monotonic()
            time.sleep(seconds)
            end = observed.cpu_times()
            io_end = observed.io_counters()
            elapsed = time.monotonic()-begin
            return dict(seconds=round(elapsed, 2),
                        cpu_percent=round(100*((end.user+end.system)-(cpu.user+cpu.system))/elapsed, 3),
                        rss_mib=round(observed.memory_info().rss/1048576, 2),
                        disk_write_bytes=io_end.write_bytes-io.write_bytes,
                        write_syscalls=io_end.write_count-io.write_count,
                        read_syscalls=io_end.read_count-io.read_count)
        finally:
            process.terminate()
            process.wait(timeout=5)


if __name__ == '__main__':
    results = {name: measure(Path(source).resolve()) for name, source in
               [('before', sys.argv[1]), ('after', sys.argv[2])]}
    print(json.dumps(results, indent=2))
