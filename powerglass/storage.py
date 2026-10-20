from pathlib import Path
import csv
import json
import math
import os
import sqlite3
import sys
import time
import uuid


def data_dir():
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData/Local'))) / 'Wattpin'
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'powerglass'


DEFAULTS = dict(mode='Low', unit='W', font='DejaVu Sans Mono', font_size=14, opacity=96,
                locked=False, bottom=True, x=80, y=100, voltage=230.0, power_factor=1.0,
                meter_file='', overhead=0.0, efficiency=90.0, estimate=False,
                transparent=False, transparent_ink='Light', retention_days=7, flush_seconds=5,
                windows_elevate=False, windows_discrete_gpu=False)


def validate_settings(loaded):
    """Treat a damaged or hand-edited preferences file as untrusted input."""
    result = DEFAULTS.copy()
    if not isinstance(loaded, dict):
        return result
    choices = dict(mode=['Ultra Low', 'Low', 'Medium', 'High'], unit=['W', 'A'],
                   transparent_ink=['Light', 'Dark'])
    bounds = dict(font_size=(10, 28), opacity=(25, 100), x=(-100000, 100000),
                  y=(-100000, 100000), voltage=(1, 500), power_factor=(.1, 1),
                  overhead=(0, 1000), efficiency=(30, 100), retention_days=(1, 365), flush_seconds=(1, 15))
    for key, value in loaded.items():
        if key not in result:
            continue
        if key in choices:
            if value in choices[key]:
                result[key] = value
        elif key in bounds:
            if type(value) in (int, float) and math.isfinite(value):
                value = max(bounds[key][0], min(value, bounds[key][1]))
                result[key] = int(value) if type(DEFAULTS[key]) is int else value
        elif type(DEFAULTS[key]) is bool:
            if type(value) is bool:
                result[key] = value
        elif isinstance(value, str) and len(value) <= 4096:
            result[key] = value
    return result


class Settings:
    def __init__(self, directory):
        self.path = Path(directory) / 'settings.json'
        self.values = DEFAULTS.copy()
        try:
            loaded = json.loads(self.path.read_text())
            self.values = validate_settings(loaded)
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def save(self):
        self.values = validate_settings(self.values)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix('.tmp')
        temp.write_text(json.dumps(self.values, indent=2))
        temp.replace(self.path)


class Session:
    def __init__(self, directory, retention_days=7, flush_seconds=5):
        Path(directory).mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(Path(directory) / 'sessions.sqlite3')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.retention_days = retention_days
        self.last_prune = 0
        self.closed = False
        self.flush_seconds = flush_seconds
        self.last_flush = time.monotonic()
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS sessions
            (id TEXT PRIMARY KEY, started REAL, ended REAL, wh REAL, covered REAL);
            CREATE TABLE IF NOT EXISTS samples
            (session TEXT, timestamp REAL, watts REAL, wh REAL, covered REAL, scope TEXT, detail TEXT);
            CREATE INDEX IF NOT EXISTS samples_timestamp ON samples(timestamp);
        ''')
        self.id = str(uuid.uuid4())
        self.started = time.time()
        self.wh = 0.0
        self.covered = 0.0
        self.previous = None
        self.db.execute('INSERT INTO sessions VALUES (?, ?, NULL, 0, 0)', (self.id, self.started))
        self.db.commit()

    def prune(self, now):
        if now - self.last_prune >= 3600:
            self.db.execute('DELETE FROM samples WHERE timestamp < ?',
                            (now-self.retention_days*86400,))
            self.last_prune = now

    def add(self, snapshot):
        self.prune(time.time())
        current = {r.key: r for r in snapshot.readings if r.included}
        if self.previous:
            last, prior, wall, last_wall = self.previous
            dt = snapshot.monotonic - last
            wall_dt = snapshot.timestamp - last_wall
            if (0 < dt <= 10 and 0 < wall_dt <= 10 and abs(wall_dt-dt) <= 2
                    and current and current.keys() == prior.keys() and wall == snapshot.wall):
                joules = sum(r.joules if r.joules is not None else
                             (r.watts + prior[key].watts) * .5 * dt for key, r in current.items())
                self.wh += joules / 3600
                self.covered += dt
        self.previous = (snapshot.monotonic, current, snapshot.wall, snapshot.timestamp)
        self.db.execute('INSERT INTO samples VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (self.id, snapshot.timestamp, snapshot.watts, self.wh, self.covered,
                         'wall' if snapshot.wall else 'components',
                         json.dumps([vars(r) for r in snapshot.readings], separators=(',', ':'))))
        self.db.execute('UPDATE sessions SET wh=?, covered=? WHERE id=?',
                        (self.wh, self.covered, self.id))
        if time.monotonic() - self.last_flush >= self.flush_seconds:
            self.flush()

    def flush(self):
        if self.closed:
            return
        self.db.commit()
        self.last_flush = time.monotonic()

    def export(self, path):
        with open(path, 'w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['session', 'timestamp_unix', 'watts', 'session_Wh', 'covered_seconds', 'scope', 'sensors_json'])
            writer.writerows(self.db.execute('SELECT * FROM samples ORDER BY timestamp'))

    def export_totals(self, path):
        with open(path, 'w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['session', 'started_unix', 'ended_unix', 'monitored_Wh', 'covered_seconds'])
            writer.writerows(self.db.execute('SELECT * FROM sessions ORDER BY started'))

    def close(self):
        if self.closed:
            return
        self.db.execute('UPDATE sessions SET ended=? WHERE id=?', (time.time(), self.id))
        self.db.commit()
        self.db.close()
        self.closed = True
