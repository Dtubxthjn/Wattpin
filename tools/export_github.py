"""Export publication source from the verified sdist, never from the working folder."""
from pathlib import Path
import hashlib
import re
import tarfile
import zipfile

from tools.privacy_check import findings

root=Path(__file__).resolve().parent.parent
version=re.search(r'^version = "([^"]+)"',(root/'pyproject.toml').read_text(),re.M).group(1)
archive=root/f'dist/wattpin-{version}.tar.gz'
output=root/f'dist/wattpin-{version}-github-source.zip'
patterns=[rb'AKIA[A-Z0-9]{16}',rb'gh[pousr]_[A-Za-z0-9]{30,}',
          b'-----BEGIN '+rb'(?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
count=0
with tarfile.open(archive) as source,zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as destination:
    for item in source.getmembers():
        relative=Path(item.name).parts[1:]
        if not item.isfile() or not relative or any(part.endswith('.egg-info') for part in relative):
            continue
        if relative == ('PKG-INFO',) or relative == ('setup.cfg',):
            continue
        assert not any(part in ('.venv','.git','dist','build','build-output','build-work','__pycache__','bin','obj') for part in relative)
        assert not relative[-1].endswith(('.sqlite3','.sqlite3-wal','.log','.deb','.pem','.key'))
        assert relative[-1] not in ('.env','settings.json')
        data=source.extractfile(item).read()
        issues = findings("/".join(relative), data)
        if issues:
            raise ValueError(f"Publication privacy check failed in {item.name}: {issues}")
        for pattern in patterns:
            assert not re.search(pattern,data),f'Credential pattern in {item.name}'
        info=zipfile.ZipInfo('/'.join((f'wattpin-{version}',*relative)))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=(item.mode | 0o100000)<<16
        destination.writestr(info,data)
        count+=1
print(f'Exported {count} source files; excluded generated metadata and checked credential patterns')
print(output)
print('SHA256',hashlib.sha256(output.read_bytes()).hexdigest())
