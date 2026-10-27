"""Application-wide dark colours, including popups and comparison status rows."""
from PySide6.QtGui import QColor, QPalette

TEXT = "#e5edf5"
ROW_COLORS = {
    "Added": "#173b30",
    "Removed": "#45272e",
    "Modified": "#423820",
    "Ambiguous": "#423820",
    "Check": "#423820",
}

STYLE = """
QWidget { font-family: 'Segoe UI'; font-size: 10pt; color: #e5edf5; }
QMainWindow, QDialog { background: #151d28; }
QFrame#dropZone { background: #1c2836; border: 2px dashed #526f88; border-radius: 9px; }
QLabel#brand { font-size: 19pt; font-weight: 700; color: #89d5f3; padding: 5px 0; }
QLabel#zoneTitle { font-weight: 700; color: #a7dcf1; }
QPushButton, QToolButton { padding: 6px 13px; border: 1px solid #4b6077; border-radius: 4px; background: #28384b; }
QToolButton { padding: 4px; }
QPushButton:hover, QToolButton:hover { background: #354d64; border-color: #79bedc; }
QPushButton:pressed, QToolButton:pressed { background: #1d4d69; }
QPushButton:disabled, QToolButton:disabled { color: #8493a5; background: #202b39; border-color: #354457; }
QPushButton#primary { background: #226b90; color: #ffffff; font-weight: 700; border-color: #5aa6cb; }
QPushButton#primary:hover { background: #2a83ae; }
QPushButton#primary:disabled { background: #294454; color: #97a9b6; border-color: #3b5668; }
QComboBox, QLineEdit, QSpinBox { padding: 4px; background: #1b2634; border: 1px solid #4b6077; border-radius: 3px; }
QComboBox:disabled, QLineEdit:disabled, QSpinBox:disabled { color: #8493a5; background: #202b39; border-color: #354457; }
QComboBox QAbstractItemView { background: #202e3f; color: #e5edf5; selection-background-color: #285c79; selection-color: #ffffff; }
QPlainTextEdit, QListWidget, QTableView { background: #1b2634; color: #e5edf5; border: 1px solid #3b5066; selection-background-color: #285c79; selection-color: #ffffff; }
QTableView { gridline-color: #344558; }
QHeaderView::section, QTableCornerButton::section { background: #293b50; color: #e5edf5; padding: 5px; border: 1px solid #3b5066; font-weight: 600; }
QTabWidget::pane { border: 1px solid #3b5066; }
QTabBar::tab { background: #202c3b; color: #acbdcf; padding: 7px 12px; border: 1px solid #3b5066; }
QTabBar::tab:selected { background: #30475e; color: #ffffff; border-bottom: 2px solid #78c9eb; }
QTabBar::tab:hover { background: #2b3d51; }
QMenu { background: #202e3f; color: #e5edf5; border: 1px solid #526f88; padding: 4px; }
QMenu::item:selected { background: #285c79; color: #ffffff; }
QMenu::separator { height: 1px; background: #43586f; margin: 4px 6px; }
QMenu QCheckBox { background: transparent; padding: 2px; }
QCheckBox:disabled, QLabel:disabled { color: #8493a5; }
QCheckBox::indicator:unchecked, QAbstractItemView::indicator:unchecked { background: #1b2634; border: 1px solid #738aa0; border-radius: 2px; }
QCheckBox::indicator:unchecked:hover { background: #293b50; border-color: #89d5f3; }
QCheckBox::indicator:unchecked:disabled { border-color: #46566a; }
QProgressBar { background: #1b2634; color: #e5edf5; border: 1px solid #4b6077; border-radius: 3px; text-align: center; }
QProgressBar::chunk { background: #267da5; }
QStatusBar { background: #151d28; }
QStatusBar::item { border: none; }
QSplitter::handle { background: #344558; }
QToolTip { background: #293b50; color: #ffffff; border: 1px solid #79bedc; padding: 5px; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus, QListWidget:focus, QTableView:focus { border: 1px solid #79bedc; }
"""


def apply_dark_theme(app):
    # Fusion respects the application palette consistently across Windows versions.
    app.setStyle("Fusion")
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: "#151d28",
        QPalette.ColorRole.WindowText: TEXT,
        QPalette.ColorRole.Base: "#1b2634",
        QPalette.ColorRole.AlternateBase: "#243244",
        QPalette.ColorRole.Text: TEXT,
        QPalette.ColorRole.Button: "#28384b",
        QPalette.ColorRole.ButtonText: TEXT,
        QPalette.ColorRole.Highlight: "#285c79",
        QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.ToolTipBase: "#293b50",
        QPalette.ColorRole.ToolTipText: "#ffffff",
        QPalette.ColorRole.PlaceholderText: "#93a4b8",
        QPalette.ColorRole.Link: "#89d5f3",
        QPalette.ColorRole.Light: "#52677f",
        QPalette.ColorRole.Midlight: "#3b5066",
        QPalette.ColorRole.Mid: "#344558",
        QPalette.ColorRole.Dark: "#101720",
        QPalette.ColorRole.Shadow: "#0c1118",
    }
    for role, color in roles.items():
        palette.setColor(role, QColor(color))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor("#8493a5"))
    app.setPalette(palette)
    app.setStyleSheet(STYLE)
