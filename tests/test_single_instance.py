import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time


def test_second_launch_shows_preferences_and_quit_flushes(tmp_path):
    env=dict(os.environ,QT_QPA_PLATFORM='offscreen')
    command=[sys.executable,'-m','powerglass.app','--data-dir',str(tmp_path)]
    process=subprocess.Popen(command,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            if (tmp_path/'app.lock').exists():break
            time.sleep(.05)
        assert (tmp_path/'app.lock').exists()
        assert subprocess.run(command,env=env,timeout=8).returncode==0
        for _ in range(100):
            if not (tmp_path/'show-request').exists():break
            time.sleep(.05)
        assert not (tmp_path/'show-request').exists()
        assert subprocess.run([*command,'--quit'],env=env,timeout=10).returncode==0
        assert process.wait(timeout=5)==0
        db=sqlite3.connect(tmp_path/'sessions.sqlite3')
        assert db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]==1
        assert db.execute('SELECT ended FROM sessions').fetchone()[0] is not None
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
