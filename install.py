"""Explicit user-run installation; no root access or sensor permission changes."""
from pathlib import Path
import argparse
import os
import shlex
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--autostart', action='store_true', help='Start at each graphical login')
parser.add_argument('--remove', action='store_true', help='Remove launchers, preserving session data')
args = parser.parse_args()
root = Path(__file__).resolve().parent
applications = Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share'))) / 'applications'
autostart = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config'))) / 'autostart'
targets = [applications/'powerglass.desktop']
if args.autostart or args.remove:
    targets.append(autostart/'powerglass.desktop')
# Desktop Exec quoting is not shell quoting.
def quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'
content = f'''[Desktop Entry]
Type=Application
Name=Wattpin
Comment=Desktop power and session energy monitor
Exec={quote(root/'.venv/bin/python')} -m powerglass.launcher
Path={root}
Icon={root/'powerglass/assets/wattpin.svg'}
Terminal=false
Categories=System;Monitor;
X-GNOME-Autostart-enabled=true
'''
for path in targets:
    if args.remove:
        path.unlink(missing_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    print(('Removed ' if args.remove else 'Installed ') + str(path))
