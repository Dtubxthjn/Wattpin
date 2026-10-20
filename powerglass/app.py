import argparse
import logging
from logging.handlers import RotatingFileHandler
from collections import deque
from pathlib import Path
import signal
import sqlite3
import sys
import threading
import time

from PySide6.QtCore import Qt, QTimer, QThread, Signal, QPoint, QRectF, QFileSystemWatcher
from PySide6.QtGui import QAction, QColor, QFont, QFontDatabase, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFontComboBox, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QSlider,
    QSpinBox, QSystemTrayIcon, QTabWidget, QTextEdit, QVBoxLayout, QWidget)

from .sensors import LinuxSensors, Snapshot
from .storage import Session, Settings, data_dir
from .ipc import send_request
from .theme import STYLE, overlay_style

MODES = ['Ultra Low', 'Low', 'Medium', 'High']


class Collector(QThread):
    ready = Signal(object)

    def __init__(self, sensors):
        super().__init__()
        self.sensors = sensors
        self.stop_event = threading.Event()

    def requestInterruption(self):
        super().requestInterruption()
        self.stop_event.set()

    def run(self):
        while not self.isInterruptionRequested():
            start = time.monotonic()
            try:
                self.ready.emit(self.sensors.sample())
            except Exception:
                logging.exception('Sensor collection failed; retrying')
                self.ready.emit(Snapshot(time.time(), time.monotonic(),
                                         issues=['Sensor read failed; retrying automatically']))
            self.stop_event.wait(max(0, 1 - (time.monotonic()-start)))
        close = getattr(self.sensors, 'close', None)
        if close:
            close()


class Sparkline(QWidget):
    def __init__(self):
        super().__init__()
        self.points = deque(maxlen=90)
        self.setFixedHeight(55)
        self.ink = '#b84e2c'

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor('#bdb3a4'), 1))
        p.drawLine(0, self.height()-4, self.width(), self.height()-4)
        values = [v for v in self.points if v is not None]
        if len(values) < 2:
            return
        maximum = max(max(values) * 1.2, 1)
        p.setPen(QPen(QColor(self.ink), 1.5))
        prior = None
        for i, value in enumerate(self.points):
            if value is None:
                prior = None
                continue
            point = QPoint(int(i / max(len(self.points)-1, 1) * self.width()),
                           int(self.height()-5-value/maximum*(self.height()-10)))
            if prior is not None:
                p.drawLine(prior, point)
            prior = point


class Preferences(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle('Wattpin · Preferences')
        self.resize(620, 560)
        self.setStyleSheet(STYLE)
        layout = QVBoxLayout(self)
        title = QLabel('Wattpin / Preferences')
        title.setStyleSheet('font-size: 23px; font-weight: 500; padding: 12px;')
        layout.addWidget(title)
        tabs = QTabWidget()
        layout.addWidget(tabs)
        self.fields = {}
        appearance = QWidget()
        form = QFormLayout(appearance)
        form.setVerticalSpacing(12)
        s = owner.settings.values
        for key, label, options in [('mode', 'Detail level', MODES),
                                     ('unit', 'Primary unit', ['W', 'A']),
                                     ('transparent_ink', 'Transparent text', ['Light', 'Dark'])]:
            widget = QComboBox()
            widget.addItems(options)
            widget.setCurrentText(s[key])
            self.fields[key] = widget
            form.addRow(label, widget)
        font = QFontComboBox()
        font.setCurrentFont(QFont(s['font']))
        self.fields['font'] = font
        form.addRow('Font family', font)
        for key, label, low, high in [('font_size', 'Text size', 10, 28), ('opacity', 'Opacity (%)', 25, 100)]:
            widget = QSpinBox()
            widget.setRange(low, high)
            widget.setValue(s[key])
            self.fields[key] = widget
            form.addRow(label, widget)
        for key, label in [('transparent', 'Transparent background · no panel or border'),
                           ('locked', 'Click through / lock placement'), ('bottom', 'Keep behind other windows')]:
            widget = QCheckBox(label)
            widget.setChecked(s[key])
            self.fields[key] = widget
            form.addRow(widget)
        hint = QLabel('Ultra Low shows only live watts and W, regardless of the primary unit.\nTransparent mode leaves text on your wallpaper. Choose light or dark ink.\nUnlock from the tray menu to move. Desktop placement depends on the window system.')
        hint.setWordWrap(True)
        hint.setObjectName('muted')
        form.addRow(hint)
        tabs.addTab(appearance, 'Appearance')
        sensors = QWidget()
        form = QFormLayout(sensors)
        for key, label, low, high in [('voltage', 'Supply voltage (V)', 1, 500),
                                      ('power_factor', 'Power factor (for A)', .1, 1),
                                      ('overhead', 'Unmetered hardware estimate (W)', 0, 1000),
                                      ('efficiency', 'PSU efficiency (%)', 30, 100)]:
            widget = QDoubleSpinBox()
            widget.setRange(low, high)
            widget.setDecimals(2)
            widget.setValue(s[key])
            self.fields[key] = widget
            form.addRow(label, widget)
        estimate = QCheckBox('Show estimated wall draw using overhead and PSU efficiency')
        estimate.setChecked(s['estimate'])
        self.fields['estimate'] = estimate
        form.addRow(estimate)
        meter = QLineEdit(s['meter_file'])
        meter.setPlaceholderText('Optional: absolute path to live meter JSON')
        self.fields['meter_file'] = meter
        form.addRow('External wall meter', meter)
        if sys.platform == 'win32':
            privileged = QPushButton('Enable privileged hardware sensors…')
            privileged.setToolTip('Windows will ask permission to run only the read-only sensor helper as administrator.')
            privileged.clicked.connect(lambda: owner.collector.sensors.elevate_requested.set())
            form.addRow(privileged)
            for key,label in [('windows_elevate','Request privileged sensors at login (Windows permission prompt)'),
                              ('windows_discrete_gpu','Count AMD/Intel GPU separately (discrete cards only)')]:
                checkbox = QCheckBox(label)
                checkbox.setChecked(s[key])
                self.fields[key] = checkbox
                form.addRow(checkbox)
        info = QTextEdit()
        info.setReadOnly(True)
        info.setPlainText(('Windows uses the bundled LibreHardwareMonitor helper and NVIDIA board readings. '
            'Some sensors require the privileged helper and a supported hardware driver. '
            if sys.platform == 'win32' else 'Automatically uses Linux RAPL, AMD/Nouveau hwmon and NVIDIA board power. ') +
            'CPU child domains are displayed but never counted twice.\n\n'
            'Sensor totals omit hardware without meters. RAM, disks, motherboard and fans '
            'are never assigned invented readings. Whole-PC accuracy needs a wall meter. '
            'Amps are derived: W ÷ (supply voltage × power factor).\n\n'
            'Live meter file: {"timestamp": <Unix seconds>, "watts": 123.4}. '
            'Update at least once per 5 seconds. The meter must measure the PC only.\n\n'
            + '\n'.join(owner.last.issues if owner.last else ['Discovering sensors…']))
        form.addRow(info)
        tabs.addTab(sensors, 'Sensors && accuracy')
        sessions = QWidget()
        form = QVBoxLayout(sessions)
        retention = QSpinBox()
        retention.setRange(1, 365)
        retention.setSuffix(' days of detailed readings')
        retention.setValue(s['retention_days'])
        self.fields['retention_days'] = retention
        form.addWidget(retention)
        flush = QSpinBox()
        flush.setRange(1, 15)
        flush.setValue(s['flush_seconds'])
        flush.setSuffix(' seconds between disk commits')
        self.fields['flush_seconds'] = flush
        form.addWidget(flush)
        info = QLabel('Every reading is tracked; disk writes are batched to save resources.\nDefault: commit every 5 seconds and always on normal shutdown.\nSudden power loss may lose the last uncommitted interval.\nChoose 1 second for more frequent disk persistence.\n\nAll display modes collect the same readings.\nSession Wh excludes manual overhead and PSU estimates.\nOlder detailed readings are removed according to retention above;\nsession totals are kept. Export readings before their retention expires.\n\nMIT-licensed open-source software · version 0.4.3\nNo accounts, telemetry, or network listener.')
        info.setWordWrap(True)
        form.addWidget(info)
        export = QPushButton('Export retained readings to CSV…')
        export.clicked.connect(owner.export)
        form.addWidget(export)
        totals = QPushButton('Export all session totals to CSV…')
        totals.clicked.connect(lambda: owner.export(totals=True))
        form.addWidget(totals)
        form.addStretch()
        tabs.addTab(sessions, 'Sessions')
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self):
        for key, widget in self.fields.items():
            if key == 'font':
                value = widget.currentFont().family()
            elif isinstance(widget, QComboBox):
                value = widget.currentText()
            elif isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                value = widget.text().strip()
            else:
                value = widget.value()
            self.owner.settings.values[key] = value
        self.owner.settings.save()
        self.owner.collector.sensors.meter_file = self.owner.settings.values['meter_file']
        if sys.platform == 'win32':
            self.owner.collector.sensors.discrete_gpu = self.owner.settings.values['windows_discrete_gpu']
        self.owner.session.retention_days = self.owner.settings.values['retention_days']
        self.owner.session.flush_seconds = self.owner.settings.values['flush_seconds']
        self.owner.apply_settings()
        self.accept()


class Overlay(QWidget):
    def __init__(self, settings, session):
        super().__init__()
        self.settings, self.session = settings, session
        self.last = None
        self.drag = None
        self.dialog = None
        self.storage_error = False
        self.stopping = False
        self.setWindowTitle('Wattpin')
        self.position_timer = QTimer(self)
        self.position_timer.setSingleShot(True)
        self.position_timer.timeout.connect(self.save_position)
        app = QApplication.instance()
        for screen in app.screens():
            self.watch_screen(screen)
        app.screenAdded.connect(self.watch_screen)
        app.screenRemoved.connect(self.queue_position_check)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(10)
        self.brand = QLabel('', self)
        self.brand.setObjectName('eyebrow')
        self.brand.hide()
        self.gear = QPushButton('···')
        self.gear.setToolTip('Preferences')
        self.gear.setAccessibleName('Open preferences')
        self.gear.setFixedSize(30, 26)
        self.gear.clicked.connect(self.preferences)
        self.scope = QLabel('', self)
        self.scope.setObjectName('muted')
        self.scope.hide()
        self.value = QLabel('— W')
        reading_row = QHBoxLayout()
        reading_row.addWidget(self.value)
        reading_row.addStretch()
        reading_row.addWidget(self.gear, 0, Qt.AlignTop)
        layout.addLayout(reading_row)
        self.subtitle = QLabel('Waiting for the first energy interval')
        self.subtitle.setObjectName('muted')
        layout.addWidget(self.subtitle)
        self.graph = Sparkline()
        layout.addWidget(self.graph)
        self.details = QLabel()
        self.details.setTextFormat(Qt.PlainText)
        layout.addWidget(self.details)
        self.footer = QLabel('SESSION  ·  0.00 Wh')
        self.footer.setObjectName('muted')
        layout.addWidget(self.footer)
        self.tray = QSystemTrayIcon(self)
        assets = Path(__file__).parent / 'assets'
        self.tray.setIcon(QIcon(str(assets/'wattpin-tray.svg')))
        self.setWindowIcon(QIcon(str(assets/'wattpin.svg')))
        menu = QMenu()
        menu.addAction('Preferences…', self.preferences)
        menu.addAction('Lock / unlock placement', self.toggle_lock)
        menu.addAction('Show / hide widget', lambda: self.setVisible(not self.isVisible()))
        for mode in MODES:
            menu.addAction(mode + ' detail', lambda checked=False, m=mode: self.set_mode(m))
        menu.addSeparator()
        menu.addAction('Transparent background on / off', self.toggle_transparent)
        menu.addAction('Export sessions…', self.export)
        menu.addAction('Quit', QApplication.instance().quit)
        self.menu = menu
        self.tray.setContextMenu(menu)
        self.tray.setToolTip('Wattpin · desktop power monitor')
        self.tray.activated.connect(lambda reason: self.preferences() if reason == QSystemTrayIcon.DoubleClick else None)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        if sys.platform == 'win32':
            from .windows_sensors import WindowsSensors
            backend = WindowsSensors(settings.values['meter_file'],settings.values['windows_discrete_gpu'],settings.values['windows_elevate'])
        else:
            backend = LinuxSensors(meter_file=settings.values['meter_file'])
        self.collector = Collector(backend)
        self.collector.ready.connect(self.receive)
        self.apply_settings()
        self.collector.start()

    def paintEvent(self, event):
        if self.settings.values['transparent']:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(242, 236, 224, int(self.settings.values['opacity'] * 2.55)))
        p.setPen(QPen(QColor('#b5aa98'), 1))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 5, 5)
        if self.settings.values['mode'] != 'Ultra Low':
            p.setPen(QPen(QColor('#ba5131'), 2))
            p.drawLine(1, 20, 1, 55)
            p.setPen(QPen(QColor('#c4b9a6'), 1))
            for x in range(22, self.width()-20, 12):
                p.drawLine(x, self.height()-5, x, self.height()-(10 if (x-22)%48 == 0 else 8))

    def apply_settings(self):
        s = self.settings.values
        # Keep a recovery path on desktops with no system tray.
        if not QSystemTrayIcon.isSystemTrayAvailable():
            s['locked'] = False
        flags = Qt.FramelessWindowHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus
        desktop = s['bottom'] and QApplication.platformName() == 'xcb'
        # The desktop type already sits below applications. Also requesting
        # BELOW can put it underneath the wallpaper, which takes its clicks.
        if s['bottom'] and not desktop:
            flags |= Qt.WindowStaysOnBottomHint
        if s['locked']:
            flags |= Qt.WindowTransparentForInput
        # X11 utility windows are minimized by Show Desktop. A desktop widget
        # must belong to the desktop layer, otherwise it disappears with apps.
        self.setAttribute(Qt.WA_X11NetWmWindowTypeDesktop, desktop)
        self.setWindowFlags(flags)
        family = s['font'].replace("'", '').replace('"', '').replace(';', '')
        self.setStyleSheet(overlay_style(s))
        self.setFont(QFont(s['font'], s['font_size']))
        ultra = s['mode'] == 'Ultra Low'
        self.value.setStyleSheet(f"font-family: '{family}'; font-size: {s['font_size']*(2 if ultra else 3)}px; font-weight: 500;")
        self.details.setStyleSheet(f"font-family: '{family}'; font-size: {s['font_size']}px;")
        for widget in [self.gear, self.subtitle, self.footer]:
            widget.setVisible(not ultra)
        self.layout().setContentsMargins(*( (10, 4, 10, 4) if ultra else (23, 20, 23, 23)))
        self.layout().setSpacing(0 if ultra else 10)
        self.graph.setVisible(s['mode'] in ('Medium', 'High'))
        self.details.setVisible(s['mode'] in ('Medium', 'High'))
        self.graph.ink = ('#f7f3e9' if s['transparent_ink'] == 'Light' else '#292722') if s['transparent'] else '#b84e2c'
        self.setMinimumWidth(0 if ultra else 340 if s['mode'] == 'Low' else 420)
        self.setMaximumWidth(900)
        if self.last:
            self.render(self.last)
        if ultra:
            self.fit_ultra_low()
        self.adjustSize()
        self.move(s['x'], s['y'])
        self.keep_on_screen()
        self.show()
        self.update()

    def receive(self, snapshot):
        if self.stopping:
            return  # a queued worker signal can arrive after shutdown closes the database
        self.last = snapshot
        try:
            self.session.add(snapshot)
            self.storage_error = False
        except (sqlite3.Error, OSError):
            logging.exception('Cannot persist a power sample')
            try:
                self.session.db.rollback()
            except sqlite3.Error:
                logging.exception('Cannot roll back the failed sample')
            if not self.storage_error:
                self.tray.showMessage('Wattpin · storage unavailable',
                                      'Live readings continue, but session data could not be saved. Check free disk space.')
            self.storage_error = True
        self.graph.points.append(snapshot.watts)
        if self.isVisible():
            if self.graph.isVisible():
                self.graph.update()
            self.render(snapshot)

    def render(self, snapshot):
        s = self.settings.values
        unit = 'W' if s['mode'] == 'Ultra Low' else s['unit']
        watts = snapshot.watts
        estimated = s['estimate'] and not snapshot.wall and watts is not None
        if estimated:
            watts = (watts + s['overhead']) / (s['efficiency']/100)
        scope = ('WHOLE PC · WALL METER' if snapshot.wall else
                 'ESTIMATED WALL DRAW' if estimated else 'MONITORED COMPONENTS · PARTIAL PC')
        if s['mode'] == 'Ultra Low':
            self.value.setText('— W' if watts is None else f'{watts:.1f} W')
            self.setToolTip(scope + '\n' + '\n'.join(snapshot.issues))
            self.fit_ultra_low()
            return
        self.scope.setText(scope)
        if watts is None:
            self.value.setText('— ' + unit)
            self.subtitle.setText('No readable power sensors · open preferences')
        else:
            current = watts / (s['voltage'] * s['power_factor'])
            self.value.setText(f'{watts:.1f} W' if unit == 'W' else f'≈ {current:.2f} A')
            self.subtitle.setText(f'≈ {current:.2f} A at {s["voltage"]:g} V · PF {s["power_factor"]:g}'
                                  if s['unit'] == 'W' else f'{watts:.1f} W · derived AC current')
        readings = snapshot.readings if s['mode'] == 'High' else [r for r in snapshot.readings if r.included]
        self.details.setText('\n'.join(f'{r.name}   {r.watts:.1f} W' +
            (f'\n  {r.source}' + (' · included in parent / wall' if not r.included else '')
             if s['mode'] == 'High' else '') for r in readings) or 'Sensors unavailable')
        mins = int(self.session.covered // 60)
        self.footer.setText(f'SESSION  {self.session.wh:.3f} Wh  ·  {mins}m measured' +
                             ('  ·  sensor notice' if snapshot.issues else ''))
        self.setToolTip(self.scope.text() + '\n' + ('\n'.join(snapshot.issues) or 'Live readings · one-second intervals') +
                        ('\nSession data could not be saved' if self.storage_error else ''))
        if self.value.fontMetrics().horizontalAdvance(self.value.text()) > self.value.width():
            self.adjustSize()

    def fit_ultra_low(self):
        margins = self.layout().contentsMargins()
        width = self.value.fontMetrics().horizontalAdvance(self.value.text()) + margins.left()+margins.right()+4
        if self.minimumWidth()!=width or self.maximumWidth()!=width:
            self.setFixedWidth(width)
            self.adjustSize()

    def preferences(self):
        if self.dialog and self.dialog.isVisible():
            self.dialog.raise_()
            self.dialog.activateWindow()
            return
        self.dialog = Preferences(self)
        self.dialog.setAttribute(Qt.WA_DeleteOnClose)
        self.dialog.finished.connect(lambda _: setattr(self, 'dialog', None))
        self.dialog.show()

    def toggle_lock(self):
        self.settings.values['locked'] = not self.settings.values['locked']
        self.settings.save()
        self.apply_settings()

    def toggle_transparent(self):
        self.settings.values['transparent'] = not self.settings.values['transparent']
        self.settings.save()
        self.apply_settings()

    def set_mode(self, mode):
        if mode not in MODES:
            return
        self.settings.values['mode'] = mode
        self.settings.save()
        self.apply_settings()

    def export(self, checked=False, totals=False):
        path, _ = QFileDialog.getSaveFileName(self, 'Export recorded sessions', 'wattpin-sessions.csv', 'CSV (*.csv)')
        if path:
            try:
                if totals:
                    self.session.export_totals(path)
                else:
                    self.session.export(path)
            except (OSError, sqlite3.Error) as error:
                QMessageBox.warning(self, 'Export failed', str(error))

    def contextMenuEvent(self, event):
        self.menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.settings.values['locked']:
            self.drag = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            # X11 window managers may acknowledge the move request but refuse
            # to move a desktop-type window. Drag these directly instead.
            desktop = self.testAttribute(Qt.WA_X11NetWmWindowTypeDesktop)
            if not desktop and self.windowHandle() and self.windowHandle().startSystemMove():
                # The window manager owns this drag; do not also move manually.
                self.drag = None

    def mouseMoveEvent(self, event):
        if self.drag is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag)

    def mouseReleaseEvent(self, event):
        if self.drag is not None:
            self.drag = None
            self.save_position()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.queue_position_check()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.queue_position_check()

    def watch_screen(self, screen):
        screen.geometryChanged.connect(self.queue_position_check)
        screen.availableGeometryChanged.connect(self.queue_position_check)
        screen.logicalDotsPerInchChanged.connect(self.queue_position_check)
        self.queue_position_check()

    def queue_position_check(self, *args):
        if not self.stopping:
            self.position_timer.start(400)

    def keep_on_screen(self):
        app = QApplication.instance()
        screens = app.screens()
        if not screens:
            return
        # Match by overlap, so a partly off-screen window stays on its monitor.
        rect = self.frameGeometry()
        def overlap(screen):
            intersection = rect.intersected(screen.availableGeometry())
            return max(0, intersection.width()) * max(0, intersection.height())
        screen = max(screens, key=overlap)
        if not overlap(screen):
            screen = app.primaryScreen() or screen
        area = screen.availableGeometry()
        position = QPoint(max(area.left(), min(rect.x(), area.right()-rect.width()+1)),
                          max(area.top(), min(rect.y(), area.bottom()-rect.height()+1)))
        if position != self.pos():
            self.move(position)

    def save_position(self):
        if self.stopping:
            return
        self.keep_on_screen()
        self.settings.values.update(x=self.x(), y=self.y())
        self.settings.save()

    def stop(self):
        if self.stopping:
            return
        self.stopping = True
        self.position_timer.stop()
        self.collector.requestInterruption()
        # Sampling and helper cleanup may each have a timeout. Never destroy a live
        # QThread after an arbitrary shorter wait (which aborts the whole process).
        self.collector.wait()
        try:
            self.settings.save()
            self.session.close()
        except (OSError, sqlite3.Error):
            logging.exception('Could not save final state at shutdown')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=data_dir())
    parser.add_argument('--screenshot', type=Path, help='Save an actual-sensor preview and exit')
    parser.add_argument('--preferences', action='store_true')
    parser.add_argument('--quit', action='store_true', help='Save and stop the running instance')
    parser.add_argument('--self-test', action='store_true', help='Verify bundled Qt and artwork without polling hardware')
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    app.setApplicationName('Wattpin')
    font = Path(__file__).parent/'assets/DejaVuSansMono.ttf'
    if font.exists():
        QFontDatabase.addApplicationFont(str(font))
    if args.self_test:
        icon = QIcon(str(Path(__file__).parent/'assets/wattpin.svg'))
        return 0 if not icon.pixmap(32,32).isNull() else 1
    args.data_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.WARNING, handlers=[RotatingFileHandler(
        args.data_dir / 'runtime.log', maxBytes=1024*1024, backupCount=2)],
        format='%(asctime)s %(levelname)s %(message)s', force=True)
    app.setQuitOnLastWindowClosed(False)
    # A single writer avoids accidental duplicate session collectors at login.
    from PySide6.QtCore import QLockFile
    args.data_dir.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(args.data_dir / 'app.lock'))
    lock.setStaleLockTime(0)
    if args.quit:
        if lock.tryLock(100):
            lock.unlock()
            return 0
        send_request(args.data_dir,'quit')
        for _ in range(70):
            if lock.tryLock(100):
                lock.unlock()
                return 0
        return 1
    if not lock.tryLock(100):
        send_request(args.data_dir,'show')
        print('Wattpin is already running; showing its preferences.')
        return 0
    settings = Settings(args.data_dir)
    widget = Overlay(settings, Session(args.data_dir, settings.values['retention_days'], settings.values['flush_seconds']))
    app.aboutToQuit.connect(widget.stop)
    app.commitDataRequest.connect(lambda manager: widget.session.flush())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    def process_requests():
        request = args.data_dir / 'show-request'
        if request.exists():
            command = request.read_text()
            request.unlink(missing_ok=True)
            if command == 'quit':
                app.quit()
                return
            widget.show()
            widget.preferences()
    watcher = QFileSystemWatcher([str(args.data_dir)])
    watcher.directoryChanged.connect(process_requests)
    QTimer.singleShot(0,process_requests)
    if args.preferences:
        widget.preferences()
    if args.screenshot:
        def capture():
            widget.grab().save(str(args.screenshot))
            if widget.dialog:
                widget.dialog.grab().save(str(args.screenshot.with_stem(args.screenshot.stem+'-preferences')))
            app.quit()
        QTimer.singleShot(3500, capture)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
