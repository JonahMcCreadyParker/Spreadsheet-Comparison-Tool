from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QMenu, QToolButton, QWidgetAction


class StatusCheckBox(QCheckBox):
    def hitButton(self, point):
        # Treat the entire menu row as clickable, including space after the label.
        return self.rect().contains(point)


class StatusFilter(QToolButton):
    """Select any combination of result statuses without closing the popup."""

    selection_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Selected Statuses")
        self.setAccessibleName("Selected Statuses")
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.popup = QMenu(self)
        self.setMenu(self.popup)
        self.checkboxes = {}
        self.setEnabled(False)
        self.setToolTip("Compare files to select the statuses to display.")

    def set_statuses(self, statuses):
        self.popup.clear()
        self.checkboxes = {}
        self.popup.addAction("Select all statuses", lambda: self.select_all(True))
        self.popup.addAction("Clear selection", lambda: self.select_all(False))
        self.popup.addSeparator()
        for status in sorted(set(statuses)):
            checkbox = StatusCheckBox(status, self.popup)
            checkbox.setContentsMargins(12, 4, 12, 4)
            checkbox.setChecked(True)
            action = QWidgetAction(self.popup)
            action.setDefaultWidget(checkbox)
            self.popup.addAction(action)
            self.checkboxes[status] = checkbox
            checkbox.toggled.connect(self.changed)
        self.setEnabled(bool(self.checkboxes))
        self.changed()

    def selected(self):
        return {status for status, checkbox in self.checkboxes.items() if checkbox.isChecked()}

    def select_all(self, checked):
        for checkbox in self.checkboxes.values():
            checkbox.blockSignals(True)
            checkbox.setChecked(checked)
            checkbox.blockSignals(False)
        self.changed()

    def changed(self):
        selected = self.selected()
        self.setToolTip("Displayed statuses: " + (", ".join(sorted(selected)) if selected else "none (no results displayed)"))
        self.selection_changed.emit()
