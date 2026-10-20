"""Fieldnote: warm paper, graphite type, and a restrained vermilion accent."""

STYLE = '''
QWidget { color: #302d27; font-family: 'DejaVu Sans'; font-size: 13px; }
QDialog { background: #eee9df; }
QLabel#muted { color: #716b60; font-size: 11px; }
QLabel#eyebrow { color: #a54b2a; font-size: 10px; font-weight: 600; letter-spacing: 2px; }
QPushButton, QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QFontComboBox {
 background: #faf7ef; border: 1px solid #c7beb0; border-radius: 3px; padding: 7px;
 selection-background-color: #b84e2c; selection-color: #ffffff; }
QPushButton:hover { background: #e3dacb; border-color: #918573; }
QPushButton:pressed { background: #d6c8b5; }
QPushButton:default { background: #35332e; color: #faf7ef; }
QTabWidget::pane { border: 0; }
QTabBar::tab { background: #eee9df; color: #716b60; padding: 12px; }
QTabBar::tab:selected { color: #302d27; border-bottom: 2px solid #b84e2c; }
QTextEdit { background: #faf7ef; border: 1px solid #d6ccbd; padding: 8px; }
QMenu { background: #faf7ef; border: 1px solid #c7beb0; padding: 5px; }
QMenu::item { padding: 8px 20px; } QMenu::item:selected { background: #e6dece; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 15px; height: 15px; border: 1px solid #a49a89; background: #faf7ef; }
QCheckBox::indicator:checked { background: #b84e2c; border: 3px solid #e5b69c; }
QToolTip { color: #faf7ef; background: #35332e; border: 0; padding: 6px; }
'''


def overlay_style(settings):
    family = settings['font'].replace("'", '').replace('"', '').replace(';', '')
    base = STYLE + f"\nQWidget {{ font-family: '{family}'; }}"
    if settings['transparent']:
        ink = '#f7f3e9' if settings['transparent_ink'] == 'Light' else '#292722'
        base += f'\nQLabel, QLabel#muted, QLabel#eyebrow {{ color: {ink}; background: transparent; }}'
    return base
