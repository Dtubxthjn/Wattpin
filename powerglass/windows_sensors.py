"""Windows power readings via a bundled, read-only LibreHardwareMonitor pipe helper."""
import ctypes
from ctypes import wintypes as w
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import threading
import time

from .sensors import Reading, Snapshot, number, meter_watts


def select_readings(rows, discrete_gpu=False):
    """Only independent package domains enter totals; child rails remain informational."""
    groups = {}
    for row in rows:
        try:
            watts = number(row['watts'])
            key, name, kind, hardware = [str(row[k]) for k in ('key','name','type','hardware')]
            groups.setdefault((hardware,kind), {})[key] = Reading(key,name,watts,'LibreHardwareMonitor',included=False)
        except (ValueError, TypeError, KeyError):
            continue
    has_cpu = any(kind == 'Cpu' and any('package' in r.name.lower() for r in items.values())
                  for (_,kind),items in groups.items())
    result = []
    for (_,kind), items in groups.items():
        readings = list(items.values())
        if kind == 'Cpu':
            package = next((r for r in readings if 'package' in r.name.lower()),None)
            if package:
                package.included = True
                for r in readings:
                    if r.name.lower() in ('cpu memory','dram'):
                        r.included = True
        elif kind.startswith('Gpu') and (not has_cpu or kind == 'GpuNvidia' or discrete_gpu):
            for label in ('gpu board','gpu total','gpu package','gpu power','gpu core','gpu ppt'):
                selected = next((r for r in readings if r.name.lower() == label),None)
                if selected:
                    selected.included = True
                    break
        result.extend(readings)
    return result


class WindowsSensors:
    def __init__(self, meter_file='', discrete_gpu=False, elevate=False):
        self.meter_file = meter_file
        self.discrete_gpu = discrete_gpu
        self.elevate_requested = threading.Event()
        self.process = None
        self.handle = None
        self.buffer = b''
        self.packet = None
        self.pipe = ''
        self.started = False
        self.issue = ''
        if elevate:
            self.elevate_requested.set()
        root = Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).parent.parent
        self.executable = root/'sensors/Wattpin.SensorHost.exe'
        self.nvidia = shutil.which('nvidia-smi')
        if self.nvidia is None:
            candidate = Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/nvidia-smi.exe'
            self.nvidia = str(candidate) if candidate.exists() else None
        self.nvidia_retry = 0
        self.kernel = ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.CreateFileW.argtypes = [w.LPCWSTR,w.DWORD,w.DWORD,w.LPVOID,w.DWORD,w.DWORD,w.HANDLE]
        self.kernel.CreateFileW.restype = w.HANDLE
        self.kernel.PeekNamedPipe.argtypes = [w.HANDLE,w.LPVOID,w.DWORD,w.LPVOID,ctypes.POINTER(w.DWORD),w.LPVOID]
        self.kernel.ReadFile.argtypes = [w.HANDLE,w.LPVOID,w.DWORD,ctypes.POINTER(w.DWORD),w.LPVOID]
        self.kernel.CloseHandle.argtypes = [w.HANDLE]

    def start(self, elevated=False):
        self.disconnect()
        if self.process:
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.terminate()
            self.process = None
        self.started = True
        self.packet = None
        self.pipe = f'Wattpin-{os.getpid()}-{secrets.token_hex(8)}'
        if not self.executable.exists():
            self.issue = 'Windows sensor helper is missing. Reinstall using Wattpin Setup.'
            return
        args = ['--parent',str(os.getpid()),'--pipe',self.pipe]
        if elevated:
            shell = ctypes.WinDLL('shell32',use_last_error=True)
            shell.ShellExecuteW.argtypes = [w.HWND,w.LPCWSTR,w.LPCWSTR,w.LPCWSTR,w.LPCWSTR,ctypes.c_int]
            shell.ShellExecuteW.restype = ctypes.c_void_p
            code = shell.ShellExecuteW(None,'runas',str(self.executable),subprocess.list2cmdline(args),str(self.executable.parent),0)
            if not code or code <= 32:
                self.issue = 'Privileged sensors were not started. You can retry from Preferences.'
            else:
                self.issue = 'Waiting for privileged hardware sensors…'
        else:
            self.process = subprocess.Popen([str(self.executable),*args],creationflags=subprocess.CREATE_NO_WINDOW,
                                            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            self.issue = 'Waiting for Windows hardware sensors…'

    def disconnect(self):
        if self.handle is not None:
            self.kernel.CloseHandle(self.handle)
            self.handle = None
        self.buffer = b''
        self.packet = None

    def read_pipe(self):
        if self.handle is None:
            handle = self.kernel.CreateFileW('\\\\.\\pipe\\'+self.pipe,0x80000000,0,None,3,0,None)
            if handle == ctypes.c_void_p(-1).value:
                return
            self.handle = handle
        available = w.DWORD()
        if not self.kernel.PeekNamedPipe(self.handle,None,0,None,ctypes.byref(available),None):
            self.disconnect()
            return
        if available.value:
            size = min(available.value,1024*1024)
            buffer, count = ctypes.create_string_buffer(size), w.DWORD()
            if not self.kernel.ReadFile(self.handle,buffer,size,ctypes.byref(count),None):
                self.disconnect()
                return
            self.buffer += buffer.raw[:count.value]
            if len(self.buffer)>1024*1024:
                self.disconnect()
                return
            while b'\n' in self.buffer:
                line,self.buffer = self.buffer.split(b'\n',1)
                try:
                    self.packet = json.loads(line)
                except (ValueError,UnicodeDecodeError):
                    self.packet = None

    def sample(self):
        elevated = self.elevate_requested.is_set()
        if elevated or not self.started:
            self.elevate_requested.clear()
            self.start(elevated)
        self.read_pipe()
        if self.process is not None and self.process.poll() is not None:
            self.packet = None
            self.issue = 'Windows sensor helper stopped. Check hardware/driver support or enable privileged sensors in Preferences.'
        now, mono = time.time(),time.monotonic()
        out = Snapshot(now,mono)
        try:
            stamp = float(self.packet['timestamp'])
            if not math.isfinite(stamp) or not -2 <= now-stamp <= 5:
                raise ValueError('Stale helper')
            out.readings = select_readings(self.packet['sensors'],self.discrete_gpu)
            out.issues.extend(str(s) for s in self.packet.get('issues',[]))
            self.issue = ''
            if not self.discrete_gpu and any('/gpu-amd/' in r.key or '/gpu-intel/' in r.key for r in out.readings):
                out.issues.append('AMD/Intel GPU accounting is conservative to avoid APU double counting. Enable separate GPU accounting only for a discrete card.')
        except (TypeError,KeyError,ValueError):
            out.issues.append(self.issue or 'Windows hardware helper unavailable or stale. Open Preferences → Sensors.')
        # Driver-only fallback when the helper cannot expose GPU power.
        if self.nvidia and not any(r.included and '/gpu-nvidia/' in r.key for r in out.readings) and mono>=self.nvidia_retry:
            try:
                result = subprocess.run([self.nvidia,'--query-gpu=uuid,name,power.draw','--format=csv,noheader,nounits'],
                    capture_output=True,text=True,check=True,timeout=2,creationflags=subprocess.CREATE_NO_WINDOW)
                for line in result.stdout.strip().splitlines():
                    key,name,watts = line.split(',',2)
                    out.readings.append(Reading(key.strip(),name.strip(),number(watts),'NVIDIA board sensor'))
            except (OSError,ValueError,subprocess.SubprocessError):
                self.nvidia_retry = mono+60
                out.issues.append('NVIDIA board power unavailable')
        if self.meter_file:
            try:
                watts = meter_watts(self.meter_file,now)
                for r in out.readings:
                    r.included = False
                out.readings.insert(0,Reading('wall','Whole PC · wall meter',watts,'External meter'))
                out.wall = True
            except (OSError,ValueError,TypeError,KeyError):
                out.issues.append('Wall meter missing, invalid or older than 5 seconds')
        return out

    def close(self):
        self.disconnect()
        if self.process:
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.terminate()
