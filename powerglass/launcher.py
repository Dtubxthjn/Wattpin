"""Desktop entry point: prepare bundled libraries before importing Qt."""
import os
from pathlib import Path
import sys
from .storage import data_dir


def environment(base=None):
    env = dict(os.environ if base is None else base)
    vendor = Path(__file__).resolve().parent.parent / 'vendor/usr/lib/x86_64-linux-gnu'
    if vendor.is_dir():
        env['LD_LIBRARY_PATH'] = str(vendor) + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    return env


def main():
    if getattr(sys,'frozen',False) or sys.platform == 'win32':
        from .app import main as run
        return run()
    env = environment()
    directory = data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    log = directory / 'startup.log'
    if log.exists() and log.stat().st_size > 1024 * 1024:
        log.replace(log.with_suffix('.previous.log'))
    with log.open('a', buffering=1) as stream:
        os.dup2(stream.fileno(), 1)
        os.dup2(stream.fileno(), 2)
        print('Starting Wattpin', flush=True)
        os.execve(sys.executable, [sys.executable, '-m', 'powerglass.app', *sys.argv[1:]], env)


if __name__ == '__main__':
    main()
