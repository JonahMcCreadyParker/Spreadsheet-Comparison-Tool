from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QMenu, QWidgetAction

from .results_model import ATTRIBUTES, HEADERS


class ColumnsMenu(QMenu):
    """View-only column choices; embedded checkboxes keep the menu open."""

    def __init__(self, table, button, store=None):
        super().__init__("Columns", button)
        self.table, self.button, self.store = table, button, store
        self.checkboxes = {}
        self.addAction("Show all columns", self.show_all)
        self.addSeparator()
        hidden = store.value("results/hidden_columns", []) if store is not None else []
        hidden = hidden if isinstance(hidden, list) and all(isinstance(x, str) for x in hidden) else []
        if all(name in hidden for name in ATTRIBUTES):
            hidden = []
        for column, (name, label) in enumerate(zip(ATTRIBUTES, HEADERS)):
            checkbox = QCheckBox(label, self)
            checkbox.setContentsMargins(12, 4, 12, 4)
            checkbox.setChecked(name not in hidden)
            action = QWidgetAction(self)
            action.setDefaultWidget(checkbox)
            self.addAction(action)
            self.checkboxes[name] = checkbox
            table.setColumnHidden(column, not checkbox.isChecked())
            checkbox.toggled.connect(lambda checked, col=column: self.toggle(col, checked))
        self.update_controls()

    def toggle(self, column, checked):
        self.table.setColumnHidden(column, not checked)
        self.update_controls()
        if self.store is not None:
            self.store.setValue("results/hidden_columns", [name for name, checkbox in self.checkboxes.items() if not checkbox.isChecked()])
            self.store.sync()

    def update_controls(self):
        count = sum(checkbox.isChecked() for checkbox in self.checkboxes.values())
        for checkbox in self.checkboxes.values():
            checkbox.setEnabled(count > 1 or not checkbox.isChecked())
        self.button.setText(f"Columns ({count}/{len(ATTRIBUTES)})")

    def show_all(self):
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
