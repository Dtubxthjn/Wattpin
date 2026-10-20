import json
import time
from powerglass.storage import Settings, Session, DEFAULTS, validate_settings
from powerglass.sensors import Snapshot, Reading


def test_corrupt_settings_are_safe(tmp_path):
    (tmp_path/'settings.json').write_text('{bad json')
    assert Settings(tmp_path).values == DEFAULTS
    result = validate_settings(dict(mode='invalid', unit=None, voltage=0, power_factor=0,
                                   font_size=100000, efficiency=float('nan'), locked='false',
                                   transparent_ink=['invalid'], opacity=True))
    assert result['mode'] == 'Low'
    assert result['unit'] == 'W'
    assert result['voltage'] == 1
    assert result['power_factor'] == .1
    assert result['font_size'] == 28
    assert result['efficiency'] == 90
    assert result['locked'] is False
    assert result['opacity'] == DEFAULTS['opacity']


def test_old_settings_migrate_and_new_preferences_persist(tmp_path):
    (tmp_path/'settings.json').write_text(json.dumps(dict(mode='High', unit='A')))
    settings = Settings(tmp_path)
    assert settings.values['transparent'] is False
    settings.values.update(mode='Ultra Low', transparent=True, transparent_ink='Dark')
    settings.save()
    assert Settings(tmp_path).values['mode'] == 'Ultra Low'
    assert Settings(tmp_path).values['transparent'] is True


def test_retention_preserves_session_totals(tmp_path):
    session = Session(tmp_path, retention_days=7)
    now = time.time()
    session.db.execute('INSERT INTO samples VALUES (?, ?, 10, 1, 1, ?, ?)',
                       (session.id, now-8*86400, 'components', '[]'))
    session.add(Snapshot(now, 1, [Reading('cpu', 'CPU', 40, 'RAPL', 40)]))
    assert session.db.execute('SELECT COUNT(*) FROM samples').fetchone()[0] == 1
    assert session.db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0] == 1
    session.export_totals(tmp_path/'totals.csv')
    assert 'monitored_Wh' in (tmp_path/'totals.csv').read_text()
    session.close()
    session.close()  # shutdown is idempotent
