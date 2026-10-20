"""Check installer signatures/formats and update release checksums."""
from pathlib import Path
import hashlib
import struct

root=Path(__file__).resolve().parent.parent
directory=root/'dist'
windows=directory/'Wattpin-0.4.3-Windows-x64-Setup.exe'
linux=directory/'Wattpin-0.4.3-Linux-x86_64.run'
data=windows.read_bytes()
assert data[:2]==b'MZ'
pe=struct.unpack_from('<I',data,0x3c)[0]
assert data[pe:pe+4]==b'PE\0\0'
assert windows.stat().st_size>10*1024*1024
with linux.open('rb') as stream:
    assert stream.readline()==b'#!/usr/bin/env bash\n'
    found=False
    for _ in range(200):
        if stream.readline().strip()==b'__WATTPIN_PAYLOAD__':
            found=True
            break
    assert found and stream.read(2)==b'\x1f\x8b'
paths=[windows,linux]
paths += sorted(directory.glob('wattpin-0.4.3*'))
(directory/'SHA256SUMS').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.name+'\n' for path in paths))
print('PASS: Windows PE installer, Linux compressed self-installer, release checksums')
