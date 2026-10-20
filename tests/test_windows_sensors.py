import json
import threading
from unittest.mock import Mock, patch

import pytest

from powerglass.windows_sensors import WindowsSensors, select_readings
from powerglass.storage import data_dir


def row(key,name,watts,kind='Cpu',hardware='/intelcpu/0'):
    return dict(key=key,name=name,watts=watts,type=kind,hardware=hardware)


def test_windows_domain_selection_avoids_double_counting():
    rows=[row('/cpu/power/0','CPU Package',40),row('/cpu/power/1','CPU Cores',30),
          row('/cpu/power/2','CPU Memory',5),row('/gpu-nvidia/0/power/0','GPU Power',100,'GpuNvidia','gpu'),
          row('/gpu-nvidia/0/power/1','GPU Core',80,'GpuNvidia','gpu')]
    readings=select_readings(rows)
    assert sum(r.watts for r in readings if r.included)==145
    assert len(readings)==5


def test_integrated_gpu_is_conservative_and_invalid_values_rejected():
    rows=[row('/cpu','CPU Package',40),row('/gpu-amd/0/power/0','GPU Package',15,'GpuAmd','gpu'),
          row('/bad','CPU Package',float('nan'))]
    assert sum(r.watts for r in select_readings(rows) if r.included)==40
    assert sum(r.watts for r in select_readings(rows,True) if r.included)==55


def fake_sensor(packet):
    sensor=WindowsSensors.__new__(WindowsSensors)
    sensor.started=True
    sensor.elevate_requested=threading.Event()
    sensor.packet=packet
    sensor.discrete_gpu=False
    sensor.nvidia=None
    sensor.meter_file=''
    sensor.issue=''
    sensor.process=None
    sensor.read_pipe=Mock()
    return sensor


def test_stale_helper_cannot_be_displayed_as_live():
    sensor=fake_sensor(dict(timestamp=100,sensors=[row('/cpu','CPU Package',40)]))
    with patch('powerglass.windows_sensors.time.time',return_value=110):
        result=sensor.sample()
    assert result.watts is None
    assert result.issues


def test_windows_external_meter_supersedes_components(tmp_path):
    meter=tmp_path/'meter.json'
    meter.write_text(json.dumps(dict(timestamp=100,watts=120)))
    sensor=fake_sensor(dict(timestamp=100,sensors=[row('/cpu','CPU Package',40)]))
    sensor.meter_file=str(meter)
    with patch('powerglass.windows_sensors.time.time',return_value=101):
        result=sensor.sample()
    assert result.wall and result.watts==120
    assert len(result.readings)==2


def test_windows_data_stays_in_local_appdata(monkeypatch,tmp_path):
    monkeypatch.setattr('powerglass.storage.sys.platform','win32')
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path))
    assert data_dir()==tmp_path/'Wattpin'
