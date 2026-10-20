"""Atomic, collision-free control requests for the single per-user instance."""
from pathlib import Path
import tempfile


def send_request(directory, command):
    directory = Path(directory)
    path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=directory,
                                         prefix='.request-', delete=False) as stream:
            path = Path(stream.name)
            stream.write(command)
        path.replace(directory/'show-request')
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
