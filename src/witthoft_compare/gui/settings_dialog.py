from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QFormLayout,
    QCheckBox, QSpinBox, QPlainTextEdit, QDialogButtonBox, QLabel, QComboBox,
    QPushButton, QInputDialog, QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem,
)

from ..core.models import ADMIN_FIELDS, ComparisonSettings, MODES


class SettingsDialog(QDialog):
    def __init__(self, settings, headers_a, headers_b, profiles, books, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Comparison settings and local profiles")
        self.resize(820, 650)
        self.settings = deepcopy(settings)
        self.profiles = deepcopy(profiles)
        self.headers_a, self.headers_b, self.books = headers_a, headers_b, books
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.profile = QComboBox()
        self.profile.addItems(list(MODES) + list(profiles))
        top.addWidget(QLabel("Profile"))
        top.addWidget(self.profile, 1)
        load = QPushButton("Load profile")
        load.clicked.connect(self.load_profile)
        save = QPushButton("Save as…")
        save.clicked.connect(self.save_profile)
        reset = QPushButton("Reset to defaults")
        reset.clicked.connect(self.reset_defaults)
        for w in (load, save, reset):
            top.addWidget(w)
        layout.addLayout(top)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        options = QWidget()
        form = QFormLayout(options)
        self.mode = QComboBox()
        self.mode.addItems(MODES)
        form.addRow("Mode", self.mode)
        self.header_a, self.header_b = QSpinBox(), QSpinBox()
        for w in (self.header_a, self.header_b):
            w.setRange(1, 1048576)
        form.addRow("Header row — Original A", self.header_a)
        form.addRow("Header row — Revised B", self.header_b)
        self.checks = {}
        for name, label in (
            ("trim", "Trim leading/trailing whitespace"),
            ("case_sensitive", "Case-sensitive values and keys"),
            ("blank_empty", "Treat blank cells, empty text, and whitespace as equal"),
            ("numeric_equivalence", "Numeric equivalence (001 stays text; 1 may equal numeric 1)"),
            ("formulas", "Compare formula expressions (cell mode)"),
            ("formatting", "Compare all supported style attributes (cell mode)"),
            ("hyperlinks", "Compare hyperlink destinations (cell mode)"),
            ("duplicate_addresses", "Check duplicate addresses within device / cluster (engineering)"),
            ("missing_scaling", "Check missing scaling limits (engineering; optional)"),
        ):
            check = QCheckBox(label)
            self.checks[name] = check
            form.addRow(check)
        self.tabs.addTab(options, "Comparison / normalisation")
        fields = QWidget()
        fl = QVBoxLayout(fields)
        fl.addWidget(QLabel("Map Original labels to Revised labels. Unmapped columns appear as structural changes.\nKeys are selected on the main screen; ignored fields use Original names."))
        self.mapping = QTableWidget(0, 2)
        self.mapping.setHorizontalHeaderLabels(["Original column", "Revised column"])
        self.mapping.horizontalHeader().setStretchLastSection(True)
        fl.addWidget(self.mapping, 2)
        fl.addWidget(QLabel("Ignored fields (checked = excluded from changed-field counts):"))
        self.ignored = QListWidget()
        fl.addWidget(self.ignored, 1)
        self.tabs.addTab(fields, "Fields / ignores")
        sheets = QWidget()
        sl = QVBoxLayout(sheets)
        sl.addWidget(QLabel("Explicit worksheet pairs (empty = all same-name sheets).\nManual pairing is a user choice; it is not proof of a worksheet rename."))
        self.pairs = QTableWidget(0, 2)
        self.pairs.setHorizontalHeaderLabels(["Original sheet", "Revised sheet"])
        self.pairs.horizontalHeader().setStretchLastSection(True)
        sl.addWidget(self.pairs)
        buttons = QHBoxLayout()
        add_pair = QPushButton("Add pair")
        add_pair.clicked.connect(lambda: self.add_pair())
        remove_pair = QPushButton("Remove selected pair")
        remove_pair.clicked.connect(lambda: self.pairs.removeRow(self.pairs.currentRow()))
        all_sheets = QPushButton("Use all matching sheets")
        all_sheets.clicked.connect(lambda: self.pairs.setRowCount(0))
        for w in (add_pair, remove_pair, all_sheets):
            buttons.addWidget(w)
        sl.addLayout(buttons)
        self.tabs.addTab(sheets, "Worksheet pairs")
        exceptions = QWidget()
        el = QVBoxLayout(exceptions)
        el.addWidget(QLabel("Duplicate-address exceptions: one exact raw address per line.\nThese suppress possible-collision checks only; address changes remain compared."))
        self.exceptions = QPlainTextEdit()
        el.addWidget(self.exceptions)
        self.tabs.addTab(exceptions, "Engineering exceptions")
        self.note = QLabel("Profiles stay on this computer. Changes take effect after OK. Recheck keys after loading a profile.")
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        layout.addWidget(box)
        self.populate()
        self.mode.currentIndexChanged.connect(self.update_enabled)

    def update_enabled(self):
        cell = self.mode.currentText() == MODES[0]
        engineering = self.mode.currentText() == MODES[2]
        for name in ("formulas", "formatting", "hyperlinks"):
            self.checks[name].setEnabled(cell)
        for name in ("duplicate_addresses", "missing_scaling"):
            self.checks[name].setEnabled(engineering)
        for w in (self.header_a, self.header_b, self.mapping, self.ignored):
            w.setEnabled(not cell)
        self.exceptions.setEnabled(engineering)

    def populate(self):
        s = self.settings
        self.mode.setCurrentText(s.mode)
        self.header_a.setValue(s.header_a)
        self.header_b.setValue(s.header_b)
        for name, check in self.checks.items():
            check.setChecked(getattr(s, name))
        self.mapping.setRowCount(len(self.headers_a))
        for row, h in enumerate(self.headers_a):
            item = QTableWidgetItem(h)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.mapping.setItem(row, 0, item)
            combo = QComboBox()
            combo.addItem("(Unmapped)", "")
            for value in self.headers_b:
                combo.addItem(value, value)
            desired = s.mappings.get(h, h)
            combo.setCurrentIndex(max(0, combo.findData(desired)))
            self.mapping.setCellWidget(row, 1, combo)
        self.mapping.resizeColumnToContents(0)
        self.ignored.clear()
        for field in dict.fromkeys(self.headers_a + s.ignored):
            item = QListWidgetItem(field, self.ignored)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if field in s.ignored else Qt.CheckState.Unchecked)
        self.pairs.setRowCount(0)
        for pair in s.sheet_pairs:
            self.add_pair(pair)
        self.exceptions.setPlainText("\n".join(s.address_exceptions))
        self.update_enabled()

    def add_pair(self, pair=None):
        row = self.pairs.rowCount()
        self.pairs.insertRow(row)
        for col, book in enumerate(self.books):
            combo = QComboBox()
            combo.addItems(list(book.sheets) if book else [])
            if pair:
                combo.setCurrentText(pair[col])
            self.pairs.setCellWidget(row, col, combo)

    def collect(self):
        s = deepcopy(self.settings)
        s.mode = self.mode.currentText()
        s.header_a, s.header_b = self.header_a.value(), self.header_b.value()
        for name, check in self.checks.items():
            setattr(s, name, check.isChecked())
        s.mappings = {}
        for row in range(self.mapping.rowCount()):
            original = self.mapping.item(row, 0).text()
            revised = self.mapping.cellWidget(row, 1).currentData()
            if revised != original:
                s.mappings[original] = revised
        s.ignored = [self.ignored.item(i).text() for i in range(self.ignored.count()) if self.ignored.item(i).checkState() == Qt.CheckState.Checked]
        s.sheet_pairs = [(self.pairs.cellWidget(r, 0).currentText(), self.pairs.cellWidget(r, 1).currentText()) for r in range(self.pairs.rowCount())]
        s.address_exceptions = self.exceptions.toPlainText().splitlines()
        return s

    def load_profile(self):
        name = self.profile.currentText()
        if name in MODES:
            self.settings = ComparisonSettings(mode=name, ignored=list(ADMIN_FIELDS) if name == MODES[2] else [])
        else:
            self.settings = deepcopy(self.profiles[name])
        self.populate()

    def save_profile(self):
        name, accepted = QInputDialog.getText(self, "Save local profile", "Profile name (duplicates current settings):")
        if accepted and name.strip() and name.strip() not in MODES:
            self.profiles[name.strip()] = self.collect()
            if self.profile.findText(name.strip()) < 0:
                self.profile.addItem(name.strip())
            self.profile.setCurrentText(name.strip())
            self.note.setText(f"Profile '{name.strip()}' will be saved locally after OK.")

    def reset_defaults(self):
        mode = self.mode.currentText()
        self.settings = ComparisonSettings(mode=mode, ignored=list(ADMIN_FIELDS) if mode == MODES[2] else [])
        self.populate()

    def accept(self):
        self.settings = self.collect()
        super().accept()
