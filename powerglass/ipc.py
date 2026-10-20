"""Atomic, collision-free control requests for the single per-user instance."""
from pathlib import Path
import tempfile
import time


def _replace_request(source, target):
    # Windows can briefly deny replacement while another launcher or the
    # running widget opens/replaces the same file. Keep the atomic handoff and
    # retry only those Windows errors, with a bounded wait and no idle polling.
    for attempt in range(40):
        try:
            source.replace(target)
            return
        except PermissionError as error:
            if getattr(error, 'winerror', None) not in (5, 32, 33) or attempt == 39:
                raise
            time.sleep(min(0.005 * (attempt + 1), 0.05))


def send_request(directory, command):
    directory = Path(directory)
    path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=directory,
                                         prefix='.request-', delete=False) as stream:
            path = Path(stream.name)
            stream.write(command)
        _replace_request(path, directory/'show-request')
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
