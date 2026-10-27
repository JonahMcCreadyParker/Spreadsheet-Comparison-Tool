from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QTableView, QToolButton

from witthoft_compare.gui.columns_menu import ColumnsMenu
from witthoft_compare.gui.main_window import MainWindow
from witthoft_compare.gui.results_model import ATTRIBUTES, ResultsModel


def test_columns_checkboxes_change_view_and_keep_data(app):
    window = MainWindow(persist=False)
    window.show()
    menu = window.columns_menu
    menu.popup(window.columns_button.mapToGlobal(window.columns_button.rect().bottomLeft()))
    app.processEvents()
    for name in ("context_a", "context_b"):
        QTest.mouseClick(menu.checkboxes[name], Qt.MouseButton.LeftButton)
        assert window.table.isColumnHidden(ATTRIBUTES.index(name))
        assert menu.isVisible()
    assert window.model.columnCount() == len(ATTRIBUTES)
    assert "11/13" in window.columns_button.text()
    menu.show_all()
    assert all(not window.table.isColumnHidden(i) for i in range(len(ATTRIBUTES)))
    menu.close()
    window.close()


def test_column_choices_persist_and_leave_one_visible(app, tmp_path):
    store = QSettings(str(tmp_path / "view.ini"), QSettings.Format.IniFormat)
    table, button = QTableView(), QToolButton()
    model = ResultsModel()
    table.setModel(model)
    menu = ColumnsMenu(table, button, store)
    for name in ATTRIBUTES[1:]:
        menu.checkboxes[name].setChecked(False)
    assert not menu.checkboxes["status"].isEnabled()
    restored = ColumnsMenu(table, button, QSettings(str(tmp_path / "view.ini"), QSettings.Format.IniFormat))
    assert restored.checkboxes["status"].isChecked()
    assert all(table.isColumnHidden(i) for i in range(1, len(ATTRIBUTES)))
    restored.show_all()
    assert all(c.isEnabled() and c.isChecked() for c in restored.checkboxes.values())
