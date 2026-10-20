"""Linux sensors. Never substitute CPU load or rated TDP for measured power."""
from dataclasses import dataclass, field
from pathlib import Path
import json
import math
import shutil
import subprocess
import time


@dataclass
class Reading:
    key: str
    name: str
    watts: float
    source: str
    joules: float | None = None
    # Parent domains include child domains. Only independent domains enter totals.
    included: bool = True


@dataclass
class Snapshot:
    timestamp: float
    monotonic: float
    readings: list[Reading] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    wall: bool = False

    @property
    def watts(self):
        values = [r.watts for r in self.readings if r.included]
        return sum(values) if values else None


def number(value):
    if isinstance(value,bool):
        raise ValueError('Boolean is not a power measurement')
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("Power must be finite and nonnegative")
    return result


def meter_watts(path, now):
    with open(path,encoding='utf-8') as stream:
        text = stream.read(65537)
    if len(text)>65536:
        raise ValueError('Meter packet exceeds 64 KiB')
    meter=json.loads(text)
    stamp=float(meter['timestamp'])
    if not math.isfinite(stamp) or not -2<=now-stamp<=5:
        raise ValueError('Meter packet is stale')
    return number(meter['watts'])


class LinuxSensors:
    def __init__(self, root=Path('/sys'), meter_file=''):
        self.root = Path(root)
        self.meter_file = meter_file
        self.previous = {}
        self.nvidia = shutil.which('nvidia-smi') if str(root) == '/sys' else None
        self.nvidia_retry = 0
        self.nvidia_issue = ''
        self.next_discovery = 0
        self.cpu_sensors = []
        self.gpu_sensors = []
        self.discovery_issues = []

    def discover(self):
        # realpath removes class aliases; exclude MMIO mirrors of the same RAPL package.
        zones = {}
        paths = []
        for entry in (self.root / 'class/powercap').glob('*'):
            paths.extend(entry.resolve().glob('**/energy_uj'))
        for path in paths:
            real = path.resolve()
            if 'mmio' not in str(real):
                zones[str(real)] = path
        return list(zones.values())

    def sample(self):
        now, mono = time.time(), time.monotonic()
        out = Snapshot(now, mono)
        if mono >= self.next_discovery:
            self.refresh(mono)
        out.issues.extend(self.discovery_issues)
        for path, label, limit, key in self.cpu_sensors:
            try:
                energy = int(path.read_text())
                previous = self.previous.get(key)
                self.previous[key] = (mono, energy, now)
                if not previous:
                    continue
                elapsed = mono - previous[0]
                wall_elapsed = now - previous[2]
                if elapsed <= 0 or elapsed > 10 or wall_elapsed > 10 or abs(wall_elapsed-elapsed) > 2:
                    continue  # suspend/resume or stale sample; do not bridge the gap
                delta = energy - previous[1]
                if delta < 0:
                    delta += limit
                if delta < 0 or delta > limit:
                    continue
                # RAPL exposes package, core, uncore, and DRAM. Core/uncore overlap package.
                independent = label.startswith('package') or label == 'dram'
                name = 'CPU ' + label.replace('package-', 'package ')
                out.readings.append(Reading(key, name, delta / 1e6 / elapsed,
                                             'RAPL energy counter', delta / 1e6, independent))
            except PermissionError:
                out.issues.append('CPU energy counter needs read permission: ' + str(path))
            except (OSError, ValueError):
                out.issues.append('CPU sensor unavailable: ' + str(path))
        for path, driver, key in self.gpu_sensors:
            try:
                watts = number(path.read_text()) / 1e6
                out.readings.append(Reading(key, 'GPU · ' + driver, watts, 'Linux hwmon'))
            except (OSError, ValueError):
                out.issues.append('GPU power sensor unavailable')
        if self.nvidia and mono >= self.nvidia_retry:
            try:
                result = subprocess.run([self.nvidia, '--query-gpu=uuid,name,power.draw',
                                         '--format=csv,noheader,nounits'], capture_output=True,
                                        text=True, timeout=2, check=True)
                self.nvidia_issue = ''
                for line in result.stdout.strip().splitlines():
                    uuid, name, power = [p.strip() for p in line.split(',', 2)]
                    out.readings.append(Reading(uuid, name, number(power), 'NVIDIA board sensor'))
            except (OSError, ValueError, subprocess.SubprocessError):
                self.nvidia_retry = mono + 60
                self.nvidia_issue = 'NVIDIA driver or board power reading unavailable'
        if self.nvidia_issue:
            out.issues.append(self.nvidia_issue)
        if self.meter_file:
            try:
                watts = meter_watts(self.meter_file,now)
                for reading in out.readings:
                    reading.included = False
                out.readings.insert(0, Reading('wall', 'Whole PC · wall meter', watts, 'External meter'))
                out.wall = True
            except (OSError, ValueError, KeyError, TypeError):
                out.issues.append('Wall meter missing, invalid or older than 5 seconds')
        if not out.readings:
            out.issues.append('No readable power sensors yet. Open Preferences → Sensors for details.')
        return out

    def refresh(self, mono):
        """Cache topology and static attributes; continue reading live counters each second."""
        self.next_discovery = mono + 60
        self.cpu_sensors, self.gpu_sensors, self.discovery_issues = [], [], []
        for path in self.discover():
            try:
                label = (path.parent / 'name').read_text().strip()
                limit = int((path.parent / 'max_energy_range_uj').read_text())
                if limit > 0:
                    self.cpu_sensors.append((path, label, limit, str(path.resolve())))
            except (OSError, ValueError):
                self.discovery_issues.append('CPU sensor metadata unavailable: ' + str(path))
        for chip in (self.root / 'class/hwmon').glob('hwmon*'):
            try:
                driver = (chip / 'name').read_text().strip()
            except OSError:
                continue
            if driver not in ('amdgpu', 'nouveau'):
                continue
            inputs = list(chip.glob('power*_average')) or list(chip.glob('power*_input'))
            for path in sorted(inputs)[:1]:
                self.gpu_sensors.append((path, driver, str(path.resolve())))
        active = {key for _, _, _, key in self.cpu_sensors}
        self.previous = {key: value for key, value in self.previous.items() if key in active}

