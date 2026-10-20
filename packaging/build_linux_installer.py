"""Make a self-contained one-step installer from the Linux one-folder build."""
from pathlib import Path
import io
import shutil
import tarfile

root = Path(__file__).resolve().parent.parent
payload = root/'build-output/linux/Wattpin'
shutil.copy2(root/'packaging/linux/uninstall.sh',payload/'uninstall.sh')
(payload/'uninstall.sh').chmod(0o755)
(payload/'.wattpin-managed').write_text('Wattpin 0.4.4\n')
for filename in ['LICENSE','README.md','THIRD_PARTY_NOTICES.md']:
    shutil.copy2(root/filename,payload/filename)
shutil.copytree(root/'packaging/licenses',payload/'licenses',dirs_exist_ok=True)
shutil.copy2(root/'vendor/usr/share/doc/libxcb-cursor0/copyright',payload/'licenses/XCB-cursor-LICENSE.txt')
destination = root/'dist/Wattpin-0.4.4-Linux-x86_64.run'
destination.parent.mkdir(exist_ok=True)
with destination.open('wb') as output:
    output.write((root/'packaging/linux/installer-header.sh').read_bytes())
    with tarfile.open(fileobj=output,mode='w:gz') as archive:
        for path in sorted(payload.iterdir()):
            archive.add(path,arcname=path.name)
destination.chmod(0o755)
print(destination)
