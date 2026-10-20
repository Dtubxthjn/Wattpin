"""Generate public screenshots from synthetic data without reading hardware or user settings."""
from pathlib import Path
import math
import sys
import tempfile

from PySide6.QtWidgets import QApplication

from powerglass import app as gui
from powerglass.sensors import Reading, Snapshot
from powerglass.storage import Settings, Session


class DemoSensors:
    """Deliberately contains no hardware discovery, file input, or device identifiers."""
    def __init__(self, *args, **kwargs):
        self.meter_file = ''

    def sample(self, tick=0):
        cpu = 30 + 6 * math.sin(tick / 8)
        return Snapshot(1700000000 + tick, tick, [
            Reading('demo-cpu', 'CPU package (demo)', cpu, 'Synthetic preview', cpu),
            Reading('demo-dram', 'DRAM (demo)', 3, 'Synthetic preview', 3),
            Reading('demo-gpu', 'GPU (demo)', 12, 'Synthetic preview'),
        ])


def main():
    app = QApplication.instance() or QApplication([])
    original = gui.LinuxSensors
    gui.LinuxSensors = DemoSensors
    windows_module = None
    original_windows = None
    if sys.platform == 'win32':
        from powerglass import windows_sensors as windows_module
        original_windows = windows_module.WindowsSensors
        windows_module.WindowsSensors = DemoSensors
    output = Path(sys.argv[1] if len(sys.argv) > 1 else 'docs/images')
    output.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix='wattpin-demo-') as directory:
            widget = gui.Overlay(Settings(directory), Session(directory))
            try:
                widget.collector.requestInterruption()
                widget.collector.wait()
                app.processEvents()
                widget.set_mode('Medium')
                for tick in range(1, 91):
                    widget.receive(DemoSensors().sample(tick))
                widget.windowIcon().pixmap(256, 256).save(str(output / 'wattpin-logo.png'))
                for mode in gui.MODES:
                    widget.set_mode(mode)
                    app.processEvents()
                    widget.grab().save(str(output / (mode.lower().replace(' ', '-') + '.png')))
                widget.set_mode('Ultra Low')
                widget.toggle_transparent()
                app.processEvents()
                widget.grab().save(str(output / 'ultra-low-transparent.png'))
                widget.set_mode('Low')
                widget.toggle_transparent()
                widget.preferences()
                app.processEvents()
                widget.dialog.grab().save(str(output / 'preferences.png'))
                widget.dialog.close()
            finally:
                widget.stop()
                widget.close()
    finally:
        gui.LinuxSensors = original
        if windows_module:
            windows_module.WindowsSensors = original_windows
    print('Captured synthetic demonstration previews; no real hardware or user settings read.')


if __name__ == '__main__':
    main()
