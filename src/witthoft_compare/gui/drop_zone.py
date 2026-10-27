from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QComboBox


class DropZone(QFrame):
    selected = Signal(str)
    cleared = Signal()
    invalid = Signal(str)
    reimport = Signal()

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("dropZone")
        self.setAccessibleName(title + " file drop target")
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setObjectName("zoneTitle")
        layout.addWidget(heading)
        self.label = QLabel("Drop a CSV / XLSX / XLSM file here")
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.TextFormat.PlainText)
        self.label.setMinimumHeight(42)
        layout.addWidget(self.label)
        self.details = QLabel("No file selected")
        self.details.setWordWrap(True)
        self.details.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.details)
        buttons = QHBoxLayout()
        self.browse = QPushButton("&Browse…")
        self.browse.clicked.connect(self.choose)
        self.clear = QPushButton("Clear")
        self.clear.clicked.connect(self.cleared)
        buttons.addWidget(self.browse)
        buttons.addWidget(self.clear)
        buttons.addStretch()
        layout.addLayout(buttons)
        options = QHBoxLayout()
        options.addWidget(QLabel("CSV encoding"))
        self.encoding = QComboBox()
        self.encoding.addItems(["auto", "utf-8-sig", "utf-8", "cp1252"])
        options.addWidget(self.encoding)
        options.addWidget(QLabel("Delimiter"))
        self.delimiter = QComboBox()
        for title, value in (("Auto", "auto"), ("Comma", ","), ("Semicolon", ";"), ("Tab", "\t")):
            self.delimiter.addItem(title, value)
        options.addWidget(self.delimiter)
        self.reload = QPushButton("Re-import")
        self.reload.clicked.connect(self.reimport)
        options.addWidget(self.reload)
        layout.addLayout(options)

    def choose(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose spreadsheet", "", "Spreadsheets (*.csv *.xlsx *.xlsm);;All files (*)")
        if path:
            self.accept_paths([path])

    def accept_paths(self, paths):
        if len(paths) != 1:
            self.invalid.emit("Drop exactly one file into each Original/Revised box.")
        elif Path(paths[0]).suffix.lower() not in (".csv", ".xlsx", ".xlsm"):
            self.invalid.emit("Supported formats are .csv, .xlsx, and .xlsm. Convert .xls in Excel first.")
        else:
            self.selected.emit(str(paths[0]))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and all(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.accept_paths([u.toLocalFile() for u in event.mimeData().urls()])
        event.acceptProposedAction()

    def show_book(self, book):
        self.label.setText(book.path.name if book else "Drop a CSV / XLSX / XLSM file here")
        self.label.setToolTip(str(book.path) if book else "")
        self.details.setText(f"{book.kind.upper()} · {len(book.sheets)} sheet(s): {', '.join(book.sheets)}\n{len(book.warnings)} import notice(s) — see preview" if book else "No file selected")
        self.details.setToolTip("\n".join(book.warnings) if book else "")
        for control in (self.encoding, self.delimiter, self.reload):
            control.setEnabled(book is None or book.kind == "csv")
