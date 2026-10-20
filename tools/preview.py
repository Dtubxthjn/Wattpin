"""Capture all presentation modes using actual local sensors."""
from pathlib import Path
import sys
import tempfile

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from powerglass.app import Overlay, MODES
from powerglass.storage import Settings, Session

app = QApplication([])
directory = tempfile.TemporaryDirectory(prefix='powerglass-preview-')
widget = Overlay(Settings(directory.name), Session(directory.name))
output = Path(sys.argv[1] if len(sys.argv)>1 else 'docs/images')
output.mkdir(parents=True, exist_ok=True)


def capture():
    widget.windowIcon().pixmap(256, 256).save(str(output/'wattpin-logo.png'))
    for mode in MODES:
        widget.set_mode(mode)
        app.processEvents()
        widget.grab().save(str(output/(mode.lower().replace(' ', '-')+'.png')))
    widget.set_mode('Ultra Low')
    widget.toggle_transparent()
    app.processEvents()
    widget.grab().save(str(output/'ultra-low-transparent.png'))
    widget.set_mode('Low')
    widget.toggle_transparent()
    widget.preferences()
    app.processEvents()
    widget.dialog.grab().save(str(output/'preferences.png'))
    print('Captured all modes using actual sensor discovery in', output)
    widget.stop()
    app.quit()


QTimer.singleShot(3500, capture)
app.exec()
directory.cleanup()
