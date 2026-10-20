"""Validate the expected release assets and generate their SHA-256 checksums."""
from pathlib import Path
import hashlib
import struct
import sys
import tarfile
import zipfile

from tools.privacy_check import findings


def main():
    directory = Path(sys.argv[1])
    names = {
        'Wattpin-0.4.4-Linux-x86_64.run',
        'Wattpin-0.4.4-Windows-x64-Setup.exe',
        'wattpin-0.4.4-py3-none-any.whl',
        'wattpin-0.4.4.tar.gz',
        'wattpin-0.4.4-github-source.zip',
    }
    actual = {p.name for p in directory.iterdir() if p.is_file() and p.name != 'SHA256SUMS'}
    if actual != names:
        raise ValueError(f'Release assets differ: missing {names - actual}, unexpected {actual - names}')
    windows = (directory / 'Wattpin-0.4.4-Windows-x64-Setup.exe').read_bytes()
    if len(windows) < 10 * 1024 * 1024 or windows[:2] != b'MZ':
        raise ValueError('Invalid Windows installer')
    offset = struct.unpack_from('<I', windows, 0x3c)[0]
    if windows[offset:offset + 4] != b'PE\0\0':
        raise ValueError('Missing Windows PE signature')
    with (directory / 'Wattpin-0.4.4-Linux-x86_64.run').open('rb') as stream:
        if stream.readline() != b'#!/usr/bin/env bash\n':
            raise ValueError('Invalid Linux installer')
        for _ in range(200):
            if stream.readline().strip() == b'__WATTPIN_PAYLOAD__':
                break
        else:
            raise ValueError('Missing Linux installer payload')
        if stream.read(2) != b'\x1f\x8b':
            raise ValueError('Invalid compressed Linux payload')
    for filename in names:
        if filename.endswith(('.zip', '.whl')):
            with zipfile.ZipFile(directory / filename) as archive:
                if archive.testzip():
                    raise ValueError('Invalid ZIP archive')
                for entry in archive.infolist():
                    issues = findings(entry.filename, archive.read(entry))
                    if issues:
                        raise ValueError(f'Private data pattern in {entry.filename}: {issues}')
        elif filename.endswith('.tar.gz'):
            with tarfile.open(directory / filename) as archive:
                for entry in archive.getmembers():
                    if entry.isfile():
                        issues = findings(entry.name, archive.extractfile(entry).read())
                        if issues:
                            raise ValueError(f'Private data pattern in {entry.name}: {issues}')
    (directory / 'SHA256SUMS').write_text(''.join(
        hashlib.sha256((directory / name).read_bytes()).hexdigest() + '  ' + name + '\n'
        for name in sorted(names)
    ))
    print('PASS: release asset set, installer formats, archive privacy checks, SHA-256 checksums')


if __name__ == '__main__':
    main()
