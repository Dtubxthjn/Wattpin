"""Check release contents and produce checksums without including private runtime data."""
from pathlib import Path
import hashlib
import re
import tarfile
import zipfile

root = Path(__file__).resolve().parent.parent
directory = root / 'dist'
version = re.search(r'^version = "([^"]+)"', (root/'pyproject.toml').read_text(), re.M).group(1)
project = re.search(r'^name = "([^"]+)"', (root/'pyproject.toml').read_text(), re.M).group(1)
wheel = directory / f'{project}-{version}-py3-none-any.whl'
source = directory / f'{project}-{version}.tar.gz'

with zipfile.ZipFile(wheel) as archive:
    wheels = archive.namelist()
    assert 'powerglass/assets/wattpin.svg' in wheels
    assert 'powerglass/assets/wattpin-tray.svg' in wheels
    assert any(name.endswith('/licenses/LICENSE') for name in wheels)
    assert any(name.endswith('/licenses/THIRD_PARTY_NOTICES.md') for name in wheels)
    assert not any('vendor/' in name for name in wheels)
with tarfile.open(source) as archive:
    names = archive.getnames()
    paths = {name.partition('/')[2] for name in names}
    for required in ['LICENSE', 'install.py', 'run.sh', 'CONTRIBUTING.md',
                     'SECURITY.md', 'tools/preview.py', 'tests/test_ui.py',
                     '.github/workflows/checks.yml',
                     'vendor/usr/share/doc/libxcb-cursor0/copyright',
                     'vendor/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0']:
        assert required in paths, required
    for path in paths:
        assert not any(part in ('.venv', '__pycache__', '.git') for part in Path(path).parts)
        assert not path.endswith(('.sqlite3', '.sqlite3-wal', '.deb', 'settings.json', '.log'))

lines = []
for path in [wheel, source]:
    lines.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name)
(directory / 'SHA256SUMS').write_text('\n'.join(lines)+'\n')
print('PASS: source and wheel contents, icon, licenses, no private data; checksums written')
