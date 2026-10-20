"""Manual X11 integration check; briefly toggles Show Desktop and restores it.

Run with the project's Qt environment on an X11 desktop. --app checks a frozen
executable with isolated test data; --locked checks click-through placement.
The two small probe windows simulate wallpaper remapping and an ordinary app.
"""
import argparse,subprocess,tempfile,sys
from pathlib import Path
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from powerglass.app import Overlay
from powerglass.storage import Settings,Session
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--app',type=Path)
parser.add_argument('--locked',action='store_true')
args=parser.parse_args()
app=QApplication([]);app.setQuitOnLastWindowClosed(False)
if app.platformName()!='xcb':
    raise SystemExit('This manual check requires an X11 desktop.')
r=Path(tempfile.mkdtemp(prefix='wattpin-layer-'))
s=Settings(r);s.values.update(mode='Ultra Low',transparent=True,locked=args.locked,x=100,y=100);s.save()
if args.app:
    class FrozenWidget:
        def __init__(self):
            self.process=subprocess.Popen([str(args.app.resolve()),'--data-dir',str(r)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        def winId(self):
            for _ in range(50):
                for line in subprocess.check_output(['wmctrl','-lpG'],text=True).splitlines():
                    fields=line.split(None,8)
                    if len(fields)==9 and fields[2]==str(self.process.pid):
                        return int(fields[0],16)
                QTest.qWait(100)
            raise AssertionError('Frozen widget did not appear')
        def stop(self):
            self.process.terminate()
            try:self.process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                self.process.kill();self.process.wait()
        def close(self):pass
    w=FrozenWidget()
else:
    w=Overlay(s,Session(r));w.collector.requestInterruption();w.collector.wait()
wall=QWidget();wall.setWindowTitle('Wattpin wallpaper probe');wall.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowDoesNotAcceptFocus);wall.setAttribute(Qt.WA_X11NetWmWindowTypeDesktop);wall.resize(40,40);wall.move(0,0)
normal=QWidget();normal.setWindowTitle('Wattpin normal-window probe');normal.setWindowFlags(Qt.Window|Qt.WindowDoesNotAcceptFocus);normal.resize(40,40);normal.move(50,0)
def prop(wid,*names):return subprocess.check_output(['xprop','-id',hex(int(wid)),*names],text=True)
def stack():
 text=subprocess.check_output(['xprop','-root','_NET_CLIENT_LIST_STACKING'],text=True)
 return [int(v.strip(),16) for v in text.split('#',1)[1].split(',')]
def check():
 order=stack();a,b,c=map(lambda v:int(v.winId()),[wall,w,normal]);assert order.index(a)<order.index(b)<order.index(c),order
 assert '_NET_WM_STATE_HIDDEN' not in prop(w.winId(),'_NET_WM_STATE')
 assert '_NET_WM_WINDOW_TYPE_DOCK' in prop(w.winId(),'_NET_WM_WINDOW_TYPE')
 assert 'not found' in prop(w.winId(),'_NET_WM_STRUT_PARTIAL')
 assert 'not found' in prop(w.winId(),'_NET_WM_STRUT')
 assert ('_NET_WM_STATE_ABOVE' not in prop(w.winId(),'_NET_WM_STATE'))
showing=subprocess.check_output(['xprop','-root','_NET_SHOWING_DESKTOP'],text=True).strip().endswith('= 1')
try:
 QTest.qWait(1000);normal.show();wall.show();QTest.qWait(600)
 for n in range(6):
  wall.raise_();QTest.qWait(150);check()
  subprocess.run(['wmctrl','-k','on'],check=True);QTest.qWait(250);check()
  subprocess.run(['wmctrl','-k','off'],check=True);QTest.qWait(250);check()
  # Remapping a wallpaper mimics it starting or refreshing after login.
  wall.hide();QTest.qWait(50);wall.show();QTest.qWait(250);check()
 print('PASS: 6 wallpaper raise/remap and Show Desktop cycles; widget above wallpaper, below applications, visible, no reserved work area')
finally:
 subprocess.run(['wmctrl','-k','on' if showing else 'off'],check=True)
 wall.close();normal.close();w.stop();w.close()
