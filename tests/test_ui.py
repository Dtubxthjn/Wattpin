import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from powerglass.app import Overlay, Preferences, MODES
from powerglass.sensors import Snapshot, Reading
from powerglass.storage import Settings, Session


def test_modes_preferences_and_energy_continue(tmp_path):
    app = QApplication.instance() or QApplication([])
    widget = Overlay(Settings(tmp_path), Session(tmp_path))
    assert widget.windowTitle() == 'Wattpin'
    assert not widget.windowIcon().isNull()
    assert not widget.tray.icon().isNull()
    # Stop real hardware polling to exercise deterministic UI state transitions.
    widget.collector.requestInterruption()
    widget.collector.wait(3500)
    app.processEvents()
    widget.receive(Snapshot(1, 1, [Reading('cpu', 'CPU package', 40, 'RAPL', 40)]))
    for i, mode in enumerate(MODES, start=2):
        widget.set_mode(mode)
        widget.receive(Snapshot(i, i, [Reading('cpu', 'CPU package', 40, 'RAPL', 40)]))
        assert widget.settings.values['mode'] == mode
        assert widget.details.isVisible() == (mode in ('Medium', 'High'))
        assert '40.0 W' in widget.value.text()
        assert not widget.brand.isVisible()
        assert not widget.scope.isVisible()
    dialog = Preferences(widget)
    dialog.fields['unit'].setCurrentText('A')
    dialog.fields['font_size'].setValue(18)
    dialog.save()
    assert 'A' in widget.value.text()
    assert Settings(tmp_path).values['font_size'] == 18
    assert widget.session.covered >= 2
    dialog.close()
    # Ultra Low is strictly watts even when the saved primary unit is amps.
    widget.set_mode('Ultra Low')
    assert widget.value.text() == '40.0 W'
    assert all(not label.isVisible() for label in [widget.brand, widget.scope,
        widget.subtitle, widget.footer, widget.gear, widget.details, widget.graph])
    assert widget.width() < 250
    widget.toggle_transparent()
    app.processEvents()
    transparent = widget.grab().toImage()
    assert transparent.pixelColor(2, 2).alpha() == 0
    widget.toggle_transparent()
    app.processEvents()
    opaque = widget.grab().toImage()
    assert opaque.pixelColor(6, 6).alpha() > 100
    # Changing appearance must use the current widget dimensions at screen edges.
    widget.settings.values.update(font_size=14)
    widget.set_mode('Ultra Low')
    screen=app.primaryScreen().availableGeometry()
    x=screen.right()-widget.width()+1
    y=screen.bottom()-widget.height()+1
    widget.settings.values.update(x=x,y=y)
    widget.apply_settings()
    assert widget.x()==x
    assert widget.y()==y
    widget.stop()
    widget.receive(Snapshot(99, 99, [Reading('cpu', 'CPU', 40, 'RAPL', 40)]))
    widget.stop()  # queued reads and repeated shutdown must not touch a closed database
    widget.close()


def test_offscreen_move_recovers_without_preferences_and_preserves_hidden_state(tmp_path):
    app = QApplication.instance() or QApplication([])
    widget = Overlay(Settings(tmp_path), Session(tmp_path))
    try:
        widget.collector.requestInterruption()
        widget.collector.wait()
        area = app.primaryScreen().availableGeometry()
        # Reproduce the observed native position beyond the display boundary.
        widget.move(area.right()+1000, area.bottom()+1000)
        QTest.qWait(900)
        assert area.contains(widget.frameGeometry())
        saved = Settings(tmp_path).values
        assert (saved['x'], saved['y']) == (widget.x(), widget.y())
        # A screen layout notification also recovers without reapplying flags.
        widget.move(-10000, -10000)
        app.primaryScreen().availableGeometryChanged.emit(area)
        QTest.qWait(900)
        assert area.contains(widget.frameGeometry())
        # Deliberately hiding the widget must remain respected.
        widget.hide()
        widget.queue_position_check()
        QTest.qWait(900)
        assert not widget.isVisible()
        QTest.qWait(900)
        assert not widget.position_timer.isActive()  # no idle polling
    finally:
        widget.stop()
        widget.close()


def test_x11_background_widget_uses_desktop_window_type(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(QApplication, 'platformName', staticmethod(lambda: 'xcb'))
    widget = Overlay(Settings(tmp_path), Session(tmp_path))
    try:
        assert widget.testAttribute(Qt.WA_X11NetWmWindowTypeDesktop)
        assert not widget.windowFlags() & Qt.WindowStaysOnBottomHint
        widget.settings.values['bottom'] = False
        widget.apply_settings()
        assert not widget.testAttribute(Qt.WA_X11NetWmWindowTypeDesktop)
    finally:
        widget.stop()
        widget.close()


def test_desktop_drag_moves_and_saves_but_locked_widget_does_not(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(QApplication, 'platformName', staticmethod(lambda: 'xcb'))
    widget = Overlay(Settings(tmp_path), Session(tmp_path))
    handle = Mock()
    handle.startSystemMove.return_value = True
    monkeypatch.setattr(widget, 'windowHandle', lambda: handle)
    def event(point):
        return SimpleNamespace(button=lambda: Qt.LeftButton,
            buttons=lambda: Qt.LeftButton, globalPosition=lambda: point.toPointF())
    try:
        widget.move(20, 20)
        start = widget.pos()
        point = start + QPoint(20, 20)
        widget.mousePressEvent(event(point))
        widget.mouseMoveEvent(event(point + QPoint(50, 40)))
        widget.mouseReleaseEvent(event(point + QPoint(50, 40)))
        assert widget.pos() == start + QPoint(50, 40)
        assert (Settings(tmp_path).values['x'], Settings(tmp_path).values['y']) == (70, 60)
        handle.startSystemMove.assert_not_called()
        widget.settings.values['locked'] = True
        widget.mousePressEvent(event(point))
        widget.mouseMoveEvent(event(point + QPoint(100, 100)))
        assert widget.pos() == QPoint(70, 60)
    finally:
        widget.stop()
        widget.close()
