"""Run on the target OS; also usable through Windows Python under Wine."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
os.chdir(root)
platform = 'windows' if sys.platform == 'win32' else 'linux'
command = [sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed',
           '--name','Wattpin','--distpath',str(root/'build-output'/platform),
           '--workpath',str(root/'build-work'/platform),'--specpath',str(root/'build-work'),
           '--paths',str(root),'--add-data',f'{root/"powerglass/assets"}{os.pathsep}powerglass/assets',
           '--hidden-import','PySide6.QtSvg',
           '--exclude-module','numpy','--exclude-module','tkinter','--exclude-module','matplotlib']
if platform == 'windows':
    command += ['--icon',str(root/'powerglass/assets/wattpin.ico')]
else:
    command += ['--add-binary',f'{root/"vendor/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0"}:.']
command.append(str(root/'packaging/entry.py'))
subprocess.run(command,check=True)
