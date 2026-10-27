from copy import deepcopy
from pathlib import Path
import json

from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QCheckBox, QListWidget, QListWidgetItem, QAbstractItemView, QTableView,
    QSplitter, QPlainTextEdit, QProgressBar, QLineEdit, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QTabWidget, QDialog, QHeaderView, QScrollArea, QToolButton,
)

from ..config.profiles import config_path, load_profiles, save_profiles
from ..core.compare_service import compare
from ..core.import_service import import_file
from ..core.models import ADMIN_FIELDS, ComparisonSettings, MODES, InputError
from ..core.record_compare import preview_stats
from ..core.sheet_mapping import sheet_pairs
from ..core.normalisation import display
from ..reporting.excel_report import export_excel
from ..reporting.csv_report import export_csv
from ..reporting.common import suggested_name
from .comparison_worker import Worker
from .drop_zone import DropZone
from .results_model import ResultsFilter, ResultsModel
from .settings_dialog import SettingsDialog
from .columns_menu import ColumnsMenu


STYLE = """
QMainWindow, QDialog { background: #f2f5f7; }
QWidget { font-family: 'Segoe UI'; font-size: 10pt; color: #203746; }
QFrame#dropZone { background: white; border: 2px dashed #7998aa; border-radius: 9px; }
QLabel#brand { font-size: 19pt; font-weight: 700; color: #153d54; padding: 5px 0; }
QLabel#zoneTitle { font-weight: 700; color: #245c78; }
QPushButton { padding: 6px 13px; border: 1px solid #a9bdc8; border-radius: 4px; background: white; }
QPushButton:hover { background: #e4eff5; }
QPushButton:disabled { color: #8797a1; background: #edf1f4; }
QPushButton#primary { background: #176080; color: white; font-weight: 700; }
QPushButton#primary:disabled { background: #93aeb9; }
QComboBox, QLineEdit, QPlainTextEdit, QListWidget, QTableView { background: white; }
QComboBox, QLineEdit { padding: 4px; }
QHeaderView::section { background: #dfe9ef; padding: 5px; border: 0; }
QToolTip { background: white; color: #203746; }
"""


class MainWindow(QMainWindow):
    idle = Signal()

    def __init__(self, *, persist=True):
        super().__init__()
        self.setWindowTitle("Witthoft Engineering — Spreadsheet Comparison Tool")
        self.resize(1400, 1000)
        self.setMinimumSize(960, 640)
        self.setStyleSheet(STYLE)
        self.persist = persist
        self.profiles, self.settings = load_profiles() if persist else ({}, ComparisonSettings())
        # Sheet selections and keys are validated against every newly loaded pair.
        self.books = [None, None]
        self.result = None
        self.worker = None
        self.headers = [[], []]
        self._refreshing = False
        self._preview_pending = False
        self._propose_engineering_key = True
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(18, 12, 18, 10)
        layout.setSpacing(9)
        brand = QLabel("WITTHOFT ENGINEERING  /  Spreadsheet Comparison")
        brand.setObjectName("brand")
        layout.addWidget(brand)
        self.controls = QWidget()
        controls_layout = QVBoxLayout(self.controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        drop_row = QHBoxLayout()
        self.zones = [DropZone("ORIGINAL (A)"), DropZone("REVISED (B)")]
        for side, zone in enumerate(self.zones):
            zone.selected.connect(lambda path, i=side: self.load_file(i, path))
            zone.cleared.connect(lambda i=side: self.clear_file(i))
            zone.invalid.connect(self.show_error)
            zone.reimport.connect(lambda i=side: self.load_file(i, self.books[i].path) if self.books[i] else None)
            drop_row.addWidget(zone)
        controls_layout.addLayout(drop_row)
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Comparison mode"))
        self.mode = QComboBox()
        self.mode.addItems(MODES)
        self.mode.setCurrentText(self.settings.mode)
        self.mode.currentIndexChanged.connect(self.mode_changed)
        mode_row.addWidget(self.mode, 2)
        self.settings_button = QPushButton("Settings / Profiles…")
        self.settings_button.clicked.connect(self.open_settings)
        mode_row.addWidget(self.settings_button)
        self.swap = QPushButton("Swap A / B")
        self.swap.clicked.connect(self.swap_files)
        mode_row.addWidget(self.swap)
        self.reset = QPushButton("Reset")
        self.reset.clicked.connect(self.reset_all)
        mode_row.addWidget(self.reset)
        controls_layout.addLayout(mode_row)
        self.help = QLabel()
        self.help.setWordWrap(True)
        controls_layout.addWidget(self.help)
        sheet_row = QHBoxLayout()
        self.scope = QComboBox()
        self.scope.addItems(["All matching sheets", "Selected sheet pair", "Custom pairs (Settings)"])
        self.scope.currentIndexChanged.connect(self.selection_changed)
        sheet_row.addWidget(self.scope)
        self.sheet_a, self.sheet_b = QComboBox(), QComboBox()
        for name, combo in (("A", self.sheet_a), ("B", self.sheet_b)):
            sheet_row.addWidget(QLabel(name))
            sheet_row.addWidget(combo, 1)
            combo.currentIndexChanged.connect(self.selection_changed)
        self.formulas = QCheckBox("Formulas")
        self.formatting = QCheckBox("Formatting")
        self.hyperlinks = QCheckBox("Hyperlinks")
        for w, name in ((self.formulas, "formulas"), (self.formatting, "formatting"), (self.hyperlinks, "hyperlinks")):
            w.setChecked(getattr(self.settings, name))
            w.toggled.connect(self.options_changed)
            sheet_row.addWidget(w)
        controls_layout.addLayout(sheet_row)
        self.key_row = QWidget()
        kr = QHBoxLayout(self.key_row)
        kr.setContentsMargins(0, 0, 0, 0)
        kr.addWidget(QLabel("Match keys\n(check multiple\nfor composite key)"))
        self.keys = QListWidget()
        self.keys.setMaximumHeight(72)
        self.keys.itemChanged.connect(self.keys_changed)
        kr.addWidget(self.keys, 2)
        self.active_settings = QLabel()
        self.active_settings.setWordWrap(True)
        self.active_settings.setTextFormat(Qt.TextFormat.PlainText)
        kr.addWidget(self.active_settings, 3)
        controls_layout.addWidget(self.key_row)
        layout.addWidget(self.controls)
        action = QHBoxLayout()
        self.compare_button = QPushButton("&Compare")
        self.compare_button.setObjectName("primary")
        self.compare_button.clicked.connect(self.start_compare)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(lambda: self.worker.cancel() if self.worker else None)
        action.addWidget(self.compare_button)
        action.addWidget(self.cancel_button)
        self.summary = QLabel("Import Original and Revised files to begin.")
        self.summary.setWordWrap(True)
        action.addWidget(self.summary, 1)
        layout.addLayout(action)
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search all result columns… (Ctrl+F)")
        self.search.textChanged.connect(self.filter_results)
        filters.addWidget(self.search, 2)
        self.filters = {}
        for field, label in (("status", "Status"), ("worksheet", "Sheet"), ("field", "Field"), ("category", "Category"), ("severity", "Severity")):
            combo = QComboBox()
            combo.setMinimumWidth(75)
            combo.setMaximumWidth(180)
            combo.addItem(f"All {label.lower()}s", "")
            combo.currentIndexChanged.connect(self.filter_results)
            self.filters[field] = combo
            filters.addWidget(combo, 1)
        self.excel = QPushButton("Export Excel")
        self.csv = QPushButton("Export CSV")
        self.excel.clicked.connect(lambda: self.choose_export("xlsx"))
        self.csv.clicked.connect(lambda: self.choose_export("csv"))
        filters.addWidget(self.excel)
        filters.addWidget(self.csv)
        layout.addLayout(filters)
        view_row = QHBoxLayout()
        self.columns_button = QToolButton()
        self.columns_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.columns_button.setToolTip("Check the columns to display in the results table. Choices are remembered locally.")
        view_row.addWidget(self.columns_button)
        view_row.addStretch()
        layout.addLayout(view_row)
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.model = ResultsModel()
        self.proxy = ResultsFilter()
        self.proxy.setSourceModel(self.model)
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setWordWrap(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        for col, width in enumerate((100, 140, 160, 130, 120, 190, 120, 190, 280, 280, 180, 85, 300)):
            self.table.setColumnWidth(col, width)
        self.view_store = QSettings(str(config_path().with_name("view.ini")), QSettings.Format.IniFormat) if persist else None
        self.columns_menu = ColumnsMenu(self.table, self.columns_button, self.view_store)
        self.columns_button.setMenu(self.columns_menu)
        header = self.table.horizontalHeader()
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(lambda point: self.columns_menu.popup(header.mapToGlobal(point)))
        self.table.selectionModel().currentRowChanged.connect(self.show_detail)
        splitter.addWidget(self.table)
        tabs = QTabWidget()
        self.context = QPlainTextEdit()
        self.context.setReadOnly(True)
        tabs.addTab(self.context, "Selected difference — raw context")
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        tabs.addTab(self.preview, "Input previews / key diagnostics")
        self.bottom_tabs = tabs
        splitter.addWidget(tabs)
        splitter.setSizes([420, 170])
        layout.addWidget(splitter, 1)
        self.status = QLabel("Ready — files stay on this computer.")
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.statusBar().addWidget(self.status, 1)
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(180)
        self.progress.setRange(0, 1)
        self.statusBar().addPermanentWidget(self.progress)
        self.setCentralWidget(central)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.search.setFocus)
        QShortcut(QKeySequence("Escape"), self, activated=lambda: self.worker.cancel() if self.worker else None)
        self.update_mode_controls()
        self.update_buttons()
        available = self.screen().availableGeometry()
        self.resize(min(1400, available.width() - 24), min(1000, available.height() - 48))

    def show_error(self, text):
        self.status.setText(text)
        QMessageBox.warning(self, "Spreadsheet comparison", text)

    def run_task(self, operation, complete):
        if self.worker:
            return
        self.worker = Worker(operation, self)
        self.worker.succeeded.connect(complete)
        self.worker.failed.connect(self.show_error)
        self.worker.cancelled.connect(lambda: self.status.setText("Cancelled — no source files changed."))
        self.worker.progress.connect(self.status.setText)
        self.worker.finished.connect(self.task_finished)
        self.controls.setEnabled(False)
        self.progress.setRange(0, 0)
        self.update_buttons()
        self.worker.start()

    def task_finished(self):
        worker = self.worker
        self.worker = None
        worker.deleteLater()
        self.controls.setEnabled(True)
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.update_buttons()
        if self._preview_pending:
            self._preview_pending = False
            self.refresh_preview()
        else:
            self.idle.emit()

    def update_buttons(self):
        ready = not self.worker and all(self.books)
        keys = self.settings.mode == MODES[0] or bool(self.settings.keys)
        self.compare_button.setEnabled(bool(ready and keys))
        self.cancel_button.setEnabled(self.worker is not None)
        self.swap.setEnabled(bool(ready))
        self.excel.setEnabled(self.result is not None and self.worker is None)
        self.csv.setEnabled(self.result is not None and self.worker is None)

    def invalidate(self):
        self.result = None
        self.model.set_rows([])
        self.context.clear()
        self.summary.setText("Settings or inputs changed — click Compare to update results.")
        self.update_buttons()

    def load_file(self, side, path):
        if self.worker:
            return
        zone = self.zones[side]
        encoding, delimiter = zone.encoding.currentText(), zone.delimiter.currentData()
        self.status.setText(f"Importing {Path(path).name}…")
        self.run_task(lambda **kwargs: import_file(path, encoding=encoding, delimiter=delimiter, **kwargs),
                      lambda book: self.loaded(side, book))

    def loaded(self, side, book):
        self._propose_engineering_key = True
        self.books[side] = book
        self.zones[side].show_book(book)
        self.settings.sheet_pairs = []
        self._refreshing = True
        combo = self.sheet_a if side == 0 else self.sheet_b
        combo.clear()
        combo.addItems(book.sheets)
        self.scope.setCurrentIndex(0)
        if all(self.books) and (self.books[0].kind == "csv") != (self.books[1].kind == "csv"):
            self.scope.setCurrentIndex(1)
        self._refreshing = False
        self.invalidate()
        self.selection_changed()
        self.bottom_tabs.setCurrentIndex(1)
        self.status.setText(f"Imported {book.path.name}. Review preview, sheets, and keys.")

    def clear_file(self, side):
        self.books[side] = None
        self.zones[side].show_book(None)
        self._refreshing = True
        (self.sheet_a if side == 0 else self.sheet_b).clear()
        self._refreshing = False
        self.headers[side] = []
        self.settings.sheet_pairs = []
        self.invalidate()
        self.refresh_preview()

    def reset_all(self):
        mode = self.mode.currentText()
        self.settings = ComparisonSettings(mode=mode, ignored=list(ADMIN_FIELDS) if mode == MODES[2] else [])
        self._refreshing = True
        self.formulas.setChecked(True)
        self.formatting.setChecked(False)
        self.hyperlinks.setChecked(False)
        self.scope.setCurrentIndex(0)
        self._refreshing = False
        self._propose_engineering_key = True
        self.clear_file(0)
        self.clear_file(1)
        self.preview.clear()
        self.status.setText("Reset — drop Original and Revised files.")

    def swap_files(self):
        if self.worker or not all(self.books):
            return
        self.books.reverse()
        self.settings.header_a, self.settings.header_b = self.settings.header_b, self.settings.header_a
        mapping = self.settings.mappings
        self.settings.keys = [mapping.get(k, k) for k in self.settings.keys]
        self.settings.ignored = [mapping.get(k, k) for k in self.settings.ignored]
        self.settings.mappings = {v: k for k, v in mapping.items() if v}
        self.settings.sheet_pairs = [(b, a) for a, b in self.settings.sheet_pairs]
        self._refreshing = True
        names = self.sheet_b.currentText(), self.sheet_a.currentText()
        for i, combo in enumerate((self.sheet_a, self.sheet_b)):
            combo.clear()
            combo.addItems(self.books[i].sheets)
            combo.setCurrentText(names[i])
            self.zones[i].show_book(self.books[i])
        self._refreshing = False
        self.invalidate()
        self.selection_changed()

    def mode_changed(self):
        self._propose_engineering_key = True
        self.settings.mode = self.mode.currentText()
        self.settings.ignored = list(ADMIN_FIELDS) if self.settings.mode == MODES[2] else []
        self.settings.keys = []
        self.invalidate()
        self.update_mode_controls()
        self.refresh_preview()

    def update_mode_controls(self):
        cell = self.settings.mode == MODES[0]
        self.key_row.setVisible(not cell)
        excel = all(self.books) and all(b.kind != "csv" for b in self.books)
        self.formulas.setEnabled(cell)
        self.formatting.setEnabled(bool(cell and excel))
        self.hyperlinks.setEnabled(bool(cell and excel))
        self.help.setText("Compare the same cell addresses. Row insertions can cause many differences; use Match Records for tables. Formula expressions are compared by default." if cell else
            "Match unique keys regardless of row order. Duplicate/blank keys remain ambiguous. Select keys and review the preview before comparing." if self.settings.mode == MODES[1] else
            "Engineering preset: Tag Name is proposed when present. Review address/type/scaling checks; changes do not automatically indicate faults.")
        self.sheet_a.setEnabled(self.scope.currentIndex() == 1)
        self.sheet_b.setEnabled(self.scope.currentIndex() == 1)
        self.active_settings.setText(f"Normalisation: trim={self.settings.trim}, case-sensitive={self.settings.case_sensitive}, blank=empty={self.settings.blank_empty}, numeric={self.settings.numeric_equivalence}\nIgnored: {', '.join(self.settings.ignored) or '(none)'}")

    def options_changed(self):
        if self._refreshing:
            return
        self.settings.formulas = self.formulas.isChecked()
        self.settings.formatting = self.formatting.isChecked()
        self.settings.hyperlinks = self.hyperlinks.isChecked()
        self.invalidate()

    def selection_changed(self):
        if self._refreshing:
            return
        if self.scope.currentIndex() == 0:
            self.settings.sheet_pairs = []
        elif self.scope.currentIndex() == 1:
            self.settings.sheet_pairs = [(self.sheet_a.currentText(), self.sheet_b.currentText())] if self.sheet_a.count() and self.sheet_b.count() else []
        self.update_mode_controls()
        self.invalidate()
        self.refresh_preview()

    def refresh_preview(self):
        if self.worker:
            self._preview_pending = True
            return
        books, settings = list(self.books), deepcopy(self.settings)

        def operation(cancel=None, progress=None):
            texts, headers = [], [[], []]
            stats = []
            try:
                pairs = sheet_pairs(*books, settings) if all(books) else []
                if all(books) and not pairs:
                    texts.append("No same-name sheets. Select an explicit pair; a rename is never inferred.")
            except InputError as exc:
                pairs = []
                texts.append(str(exc))
            for i, book in enumerate(books):
                if not book:
                    continue
                texts.append(f"{'ORIGINAL A' if i == 0 else 'REVISED B'}: {book.path}\nSheets: {', '.join(book.sheets)}")
                if all(books):
                    only = set(book.sheets) - set(books[1 - i].sheets)
                    texts.append(f"Only in {'A' if i == 0 else 'B'} by name: {', '.join(sorted(only)) or '(none)'}")
                texts.extend(book.warnings)
                names = [p[i] for p in pairs] or [next(iter(book.sheets))]
                for j, name in enumerate(names):
                    sheet = book.sheets[name]
                    texts.append(f"\n[{name}] preview (first 8 populated rows):")
                    by_row = {}
                    for (r, c), cell in sheet.cells.items():
                        if r not in by_row:
                            by_row[r] = []
                        by_row[r].append((c, display(cell.value)))
                    for r in sorted(by_row)[:8]:
                        texts.append(f"Row {r}: " + " | ".join(f"{c}: {v}" for c, v in sorted(by_row[r])[:20]))
                    try:
                        h, records, diagnostic = preview_stats(sheet, settings, "A" if i == 0 else "B")
                        headers[i] = h if j == 0 else [x for x in headers[i] if x in h]
                        texts.append(diagnostic)
                    except InputError as exc:
                        texts.append(str(exc))
            return "\n".join(texts), headers

        self.run_task(operation, self.preview_ready)

    def preview_ready(self, payload):
        text, self.headers = payload
        self.preview.setPlainText(text)
        self._refreshing = True
        current = self.settings.keys
        valid = [h for h in self.headers[0] if self.settings.mappings.get(h, h) in self.headers[1]]
        proposed = [k for k in current if k in valid]
        if not proposed and self._propose_engineering_key and self.settings.mode == MODES[2] and "Tag Name" in valid:
            proposed = ["Tag Name"]
        self._propose_engineering_key = False
        self.settings.keys = proposed
        self.keys.clear()
        for h in valid:
            item = QListWidgetItem(h, self.keys)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if h in proposed else Qt.CheckState.Unchecked)
        self._refreshing = False
        self.update_mode_controls()
        # Recompute diagnostics once if an engineering key was just proposed.
        if proposed != current:
            self._preview_pending = True

    def keys_changed(self):
        if self._refreshing:
            return
        self.settings.keys = [self.keys.item(i).text() for i in range(self.keys.count()) if self.keys.item(i).checkState() == Qt.CheckState.Checked]
        self.invalidate()
        self.refresh_preview()

    def open_settings(self):
        dialog = SettingsDialog(self.settings, *self.headers, self.profiles, self.books, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings, self.profiles = dialog.settings, dialog.profiles
            self._propose_engineering_key = True
            self._refreshing = True
            self.mode.blockSignals(True)
            self.mode.setCurrentText(self.settings.mode)
            self.mode.blockSignals(False)
            self.scope.setCurrentIndex(2 if self.settings.sheet_pairs else 0)
            for w, name in ((self.formulas, "formulas"), (self.formatting, "formatting"), (self.hyperlinks, "hyperlinks")):
                w.setChecked(getattr(self.settings, name))
            self._refreshing = False
            self.update_mode_controls()
            self.invalidate()
            self.save_preferences()
            self.refresh_preview()

    def save_preferences(self):
        if self.persist:
            try:
                save_profiles(self.profiles, self.settings)
            except OSError as exc:
                self.status.setText(f"Preferences could not be saved: {exc}")

    def start_compare(self):
        if self.worker or not all(self.books):
            return
        self.save_preferences()
        settings = deepcopy(self.settings)
        self.status.setText("Comparing…")
        self.run_task(lambda **kwargs: compare(*self.books, settings, **kwargs), self.comparison_ready)

    def comparison_ready(self, result):
        self.result = result
        self.model.set_rows(result.rows)
        c = result.counts
        unit = "cells" if result.settings.mode == MODES[0] else "records"
        warn = sum(d.severity != "Info" for d in result.warnings)
        self.summary.setText(f"{c['sheets']} sheets · {unit}: +{c['added']} / −{c['removed']} / {c['modified']} modified / {c['unchanged']} unchanged · {c['fields']} changed fields/attributes · {len(result.structural)} structural · {warn} warnings · {c['errors']} errors")
        for field, combo in self.filters.items():
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(f"All {field}s", "")
            for value in sorted({getattr(d, field) for d in result.rows}):
                combo.addItem(value, value)
            combo.blockSignals(False)
        self.filter_results()
        self.status.setText("Comparison complete. Exports include all results, regardless of filters.")
        self.bottom_tabs.setCurrentIndex(0)

    def filter_results(self):
        self.proxy.update(self.search.text(), {field: combo.currentData() or "" for field, combo in self.filters.items()})

    def show_detail(self, index, previous=None):
        if not index.isValid():
            return
        d = self.model.rows[self.proxy.mapToSource(index).row()]
        sources = f"Original (A): {self.result.original.path}\nRevised (B): {self.result.revised.path}\n" if self.result else ""
        self.context.setPlainText(f"{d.status} | {d.worksheet} | {d.identity} | {d.field}\n{sources}Original row: {d.row_a if d.row_a is not None else 'No corresponding entry'} / Revised row: {d.row_b if d.row_b is not None else 'No corresponding entry'}\nOriginal raw ({type(d.original).__name__}): {d.original!r}\nUpdated raw ({type(d.revised).__name__}): {d.revised!r}\n{d.notes}\n\nORIGINAL ENTRY (A)\n{json.dumps(d.context_a, ensure_ascii=False, indent=2, default=str)}\n\nUPDATED ENTRY (B)\n{json.dumps(d.context_b, ensure_ascii=False, indent=2, default=str)}")

    def choose_export(self, extension):
        if not self.result:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export all results (GUI filters do not restrict report)", suggested_name(self.result, extension), f"Report (*.{extension})")
        if path:
            if not Path(path).suffix:
                path += "." + extension
            self.export_to(path)

    def export_to(self, path):
        if self.worker or self.result is None:
            return
        result = self.result
        writer = export_csv if Path(path).suffix.lower() == ".csv" else export_excel
        self.status.setText("Exporting all results…")
        self.run_task(lambda **kwargs: writer(result, path, **kwargs), lambda name: self.status.setText(f"Report saved: {name}"))

    def closeEvent(self, event):
        if self.worker:
            self.worker.cancel()
            self.status.setText("Cancelling active operation. Close again once it finishes.")
            event.ignore()
            return
        self.save_preferences()
        event.accept()
