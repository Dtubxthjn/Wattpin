import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from powerglass.sensors import LinuxSensors, Reading, Snapshot, number
from powerglass.storage import Session


def test_energy_counter_and_overlapping_children(tmp_path):
    root = tmp_path / 'sys'
    package = root / 'class/powercap/intel-rapl:0'
    package.mkdir(parents=True)
    child = package / 'intel-rapl:0:0'
    child.mkdir()
    for directory, label in [(package, 'package-0'), (child, 'core')]:
        (directory / 'name').write_text(label)
        (directory / 'energy_uj').write_text('10000000')
        (directory / 'max_energy_range_uj').write_text('1000000000')
    sensors = LinuxSensors(root)
    with patch('powerglass.sensors.time.monotonic', return_value=1), patch('powerglass.sensors.time.time', return_value=1):
        assert sensors.sample().watts is None
    for directory in [package, child]:
        (directory / 'energy_uj').write_text('50000000')
    with patch('powerglass.sensors.time.monotonic', return_value=3), patch('powerglass.sensors.time.time', return_value=3):
        snapshot = sensors.sample()
    assert snapshot.watts == 20
    assert len(snapshot.readings) == 2
    assert sum(r.joules for r in snapshot.readings if r.included) == 40


def test_rollover_and_sleep(tmp_path):
    zone = tmp_path / 'class/powercap/intel-rapl:0'
    zone.mkdir(parents=True)
    for name, value in [('name', 'package-0'), ('energy_uj', '90000000'), ('max_energy_range_uj', '100000000')]:
        (zone / name).write_text(value)
    sensor = LinuxSensors(tmp_path)
    with patch('powerglass.sensors.time.monotonic', return_value=1), patch('powerglass.sensors.time.time', return_value=1):
        sensor.sample()
    (zone / 'energy_uj').write_text('10000000')
    with patch('powerglass.sensors.time.monotonic', return_value=2), patch('powerglass.sensors.time.time', return_value=2):
        assert sensor.sample().watts == 20
    with patch('powerglass.sensors.time.monotonic', return_value=100), patch('powerglass.sensors.time.time', return_value=100):
        assert sensor.sample().watts is None


def test_fresh_meter_supersedes_components_and_rejects_stale(tmp_path):
    path = tmp_path / 'meter.json'
    path.write_text(json.dumps(dict(timestamp=100, watts=210)))
    sensors = LinuxSensors(tmp_path, str(path))
    with patch('powerglass.sensors.time.time', return_value=101):
        result = sensors.sample()
    assert result.wall and result.watts == 210
    with patch('powerglass.sensors.time.time', return_value=110):
        result = sensors.sample()
    assert not result.wall and result.watts is None
    assert any('older than' in i for i in result.issues)


def test_session_integrates_counters_and_power_without_bridging_gaps(tmp_path):
    session = Session(tmp_path)
    def sample(t, cpu=40, gpu=60):
        return Snapshot(t, t, [Reading('cpu', 'CPU', cpu, 'RAPL', 40),
                               Reading('gpu', 'GPU', gpu, 'board')])
    session.add(sample(1))
    session.add(sample(2, cpu=999))  # counter delta is authoritative, not displayed watts
    assert session.wh == pytest.approx(100 / 3600)
    session.add(sample(100))
    assert session.covered == 1
    session.add(Snapshot(101, 101))
    session.add(sample(102))
    assert session.covered == 1
    session.export(tmp_path / 'export.csv')
    assert 'components' in (tmp_path / 'export.csv').read_text()
    session.close()
    db = sqlite3.connect(tmp_path / 'sessions.sqlite3')
    assert db.execute('SELECT COUNT(*) FROM samples').fetchone()[0] == 5
    assert db.execute('SELECT ended FROM sessions').fetchone()[0] is not None


@pytest.mark.parametrize('value', ['NaN', '-1', 'inf'])
def test_invalid_power(value):
    with pytest.raises(ValueError):
        number(value)


def test_suspend_with_monotonic_clock_paused(tmp_path):
    session = Session(tmp_path)
    session.add(Snapshot(1, 1, [Reading('cpu', 'CPU', 10, 'RAPL', 10)]))
    session.add(Snapshot(1001, 2, [Reading('cpu', 'CPU', 10, 'RAPL', 10)]))
    assert session.wh == 0
    assert session.covered == 0
    session.close()
