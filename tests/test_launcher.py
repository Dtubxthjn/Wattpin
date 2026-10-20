import pytest
import sys
from powerglass.launcher import environment


@pytest.mark.skipif(sys.platform != "linux", reason="Linux bundled-library environment behavior")
def test_bundled_library_path_preserves_existing_environment():
    env = environment({'LD_LIBRARY_PATH': '/example', 'DISPLAY': ':9'})
    assert env['LD_LIBRARY_PATH'].endswith(':/example')
    assert 'vendor/usr/lib/x86_64-linux-gnu' in env['LD_LIBRARY_PATH']
    assert env['DISPLAY'] == ':9'
