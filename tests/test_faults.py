from unittest.mock import Mock
import ctypes
import pytest
from powerglass.sensors import meter_watts, number
from powerglass.windows_sensors import WindowsSensors


def test_boolean_is_not_a_power_reading():
    with pytest.raises(ValueError):number(True)


def test_meter_rejects_oversized_input(tmp_path):
    path=tmp_path/'meter.json'
    path.write_text(' '*65537)
    with pytest.raises(ValueError,match='64 KiB'):
        meter_watts(path,100)


def test_windows_pipe_uses_exact_local_win32_name():
    sensor=WindowsSensors.__new__(WindowsSensors)
    sensor.handle=None
    sensor.pipe='Wattpin-123-0123456789abcdef'
    sensor.kernel=Mock()
    sensor.kernel.CreateFileW.return_value=ctypes.c_void_p(-1).value
    sensor.read_pipe()
    actual=sensor.kernel.CreateFileW.call_args.args[0]
    assert [ord(c) for c in actual[:9]]==[92,92,46,92,112,105,112,101,92]
    assert actual[9:]==sensor.pipe


def test_broken_pipe_discards_last_good_reading():
    sensor=WindowsSensors.__new__(WindowsSensors)
    sensor.handle=123
    sensor.kernel=Mock()
    sensor.kernel.PeekNamedPipe.return_value=False
    sensor.packet={'timestamp':100,'sensors':[]}
    sensor.buffer=b'partial message'
    sensor.read_pipe()
    assert sensor.packet is None
    assert sensor.handle is None
    assert sensor.buffer==b''
