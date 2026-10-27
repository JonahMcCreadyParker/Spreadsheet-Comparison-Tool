from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from spreadsheet_compare.core.compare_service import compare
from spreadsheet_compare.gui.main_window import MainWindow


def test_select_multiple_statuses_and_combine_other_filters(app, csv_book, records):
    a = csv_book('a.csv', [['ID', 'Value'], ['1', 'old'], ['2', 'removed']])
    b = csv_book('b.csv', [['ID', 'Value'], ['1', 'changed'], ['3', 'added']])
    result = compare(a, b, records)
    window = MainWindow(persist=False)
    window.comparison_ready(result)
    window.show()
    control = window.status_filter
    assert control.text() == 'Selected Statuses'
    assert window.proxy.rowCount() == 3
    control.select_all(False)
    assert window.proxy.rowCount() == 0
    control.popup.popup(control.mapToGlobal(control.rect().bottomLeft()))
    app.processEvents()
    for status in ('Added', 'Modified'):
        QTest.mouseClick(control.checkboxes[status], Qt.MouseButton.LeftButton)
        assert control.popup.isVisible()
    assert window.proxy.rowCount() == 2
    assert {window.proxy.index(i, 0).data() for i in range(2)} == {'Added', 'Modified'}
    window.search.setText('changed')
    assert window.proxy.rowCount() == 1
    window.search.clear()
    window.filters['field'].setCurrentText('Value')
    assert window.proxy.rowCount() == 1
    control.popup.close()
    window.close()


def test_statuses_reset_on_new_comparison(app, csv_book, records):
    a = csv_book('a.csv', [['ID', 'Value'], ['1', 'old']])
    b = csv_book('b.csv', [['ID', 'Value'], ['1', 'changed']])
    window = MainWindow(persist=False)
    window.comparison_ready(compare(a, b, records))
    window.status_filter.select_all(False)
    assert window.proxy.rowCount() == 0
    window.comparison_ready(compare(a, b, records))
    assert window.status_filter.selected() == {'Modified'}
    assert window.proxy.rowCount() == 1
    window.close()
