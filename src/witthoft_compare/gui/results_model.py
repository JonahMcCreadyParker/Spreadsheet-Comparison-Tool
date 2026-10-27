from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QSortFilterProxyModel
from PySide6.QtGui import QColor

from ..core.normalisation import display

ATTRIBUTES = ("status", "worksheet", "identity", "field", "row_a", "original", "row_b", "revised", "context_a", "context_b", "category", "severity", "notes")
HEADERS = ("Status", "Worksheet", "Record Key or Cell", "Field", "Original (A) Row", "Original Value", "Revised (B) Row", "Updated Value", "Original Entry (A)", "Updated Entry (B)", "Category", "Severity", "Notes")


class ResultsModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return len(ATTRIBUTES)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return HEADERS[section] if orientation == Qt.Orientation.Horizontal else section + 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        d = self.rows[index.row()]
        value = getattr(d, ATTRIBUTES[index.column()])
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            attribute = ATTRIBUTES[index.column()]
            if attribute in ("original", "revised"):
                text = display(value)
            elif attribute in ("context_a", "context_b"):
                import json
                text = json.dumps(value, ensure_ascii=False, default=str) if value else ""
            else:
                text = str(value) if value is not None else ""
            return text if role == Qt.ItemDataRole.ToolTipRole else text[:2000]
        if role == Qt.ItemDataRole.BackgroundRole:
            return QColor({"Added": "#e2f0d9", "Removed": "#fce4d6", "Modified": "#fff2cc", "Ambiguous": "#fff2cc", "Check": "#fff2cc"}.get(d.status, "#f4f7fa"))


class ResultsFilter(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search = ""
        self.criteria = {}

    def filterAcceptsRow(self, row, parent):
        d = self.sourceModel().rows[row]
        if any(value and getattr(d, field) != value for field, value in self.criteria.items()):
            return False
        return not self.search or any(self.search in display(getattr(d, field)).casefold() for field in ATTRIBUTES)

    def update(self, search, criteria):
        self.search, self.criteria = search.casefold(), criteria
        self.beginFilterChange()
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)
