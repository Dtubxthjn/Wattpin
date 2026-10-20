import sys
import sqlite3
import threading
import time
import pytest
from unittest.mock import patch

from powerglass.app import Collector
from powerglass.sensors import LinuxSensors, Snapshot, Reading
from powerglass.storage import Session


@pytest.mark.skipif(sys.platform != "linux", reason="Linux sysfs fixture names require a POSIX filesystem")
def test_cached_discovery_keeps_live_counters_and_rediscovers(tmp_path):
    zone = tmp_path/'class/powercap/intel-rapl:0'
    zone.mkdir(parents=True)
    for name, value in [('name','package-0'), ('max_energy_range_uj','1000000000'), ('energy_uj','0')]:
        (zone/name).write_text(value)
    sensor = LinuxSensors(tmp_path)
    with patch.object(sensor, 'discover', wraps=sensor.discover) as discover:
        for tick in [1,2,3,62]:
            (zone/'energy_uj').write_text(str(tick*1000000))
            with patch('powerglass.sensors.time.monotonic', return_value=tick), patch('powerglass.sensors.time.time', return_value=tick):
                result = sensor.sample()
            if tick in [2,3]:
                assert result.watts == 1
        assert discover.call_count == 2


def test_batched_persistence_and_final_shutdown_flush(tmp_path):
    session = Session(tmp_path, flush_seconds=5)
    session.last_flush = 0
    observer = sqlite3.connect(tmp_path/'sessions.sqlite3')
    for tick in range(1,7):
        with patch('powerglass.storage.time.monotonic', return_value=tick):
            session.add(Snapshot(tick,tick,[Reading('cpu','CPU',10,'RAPL',10)]))
        if tick == 4:
            assert observer.execute('SELECT COUNT(*) FROM samples').fetchone()[0] == 0
    assert observer.execute('SELECT COUNT(*) FROM samples').fetchone()[0] == 5
    assert session.wh == pytest.approx(50/3600)
    session.close()
    assert observer.execute('SELECT COUNT(*) FROM samples').fetchone()[0] == 6
    observer.close()


def test_collector_wait_can_be_interrupted_immediately():
    sampled = threading.Event()
    class Sensors:
        def sample(self):
            sampled.set()
            return Snapshot(time.time(),time.monotonic())
    collector = Collector(Sensors())
    collector.start()
    assert sampled.wait(2)
    start = time.monotonic()
    collector.requestInterruption()
    assert collector.wait(500)
    assert time.monotonic()-start < .5
