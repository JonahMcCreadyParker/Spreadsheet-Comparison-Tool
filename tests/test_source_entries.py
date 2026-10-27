import csv
import json

from openpyxl import load_workbook
from PySide6.QtCore import Qt

from spreadsheet_compare.core.compare_service import compare
from spreadsheet_compare.core.models import ComparisonSettings
from spreadsheet_compare.gui.results_model import ATTRIBUTES, ResultsModel
from spreadsheet_compare.reporting.csv_report import export_csv
from spreadsheet_compare.reporting.excel_report import export_excel


def test_reordered_change_exposes_both_rows_and_entries(csv_book, records, tmp_path, app):
    a = csv_book("original.csv", [["ID", "Name", "Other"], ["001", "old", "unchanged"], ["002", "same", "x"]])
    b = csv_book("updated.csv", [["ID", "Name", "Other"], ["002", "same", "x"], ["001", "=new", "unchanged"]])
    result = compare(a, b, records)
    change = result.differences[0]
    model = ResultsModel()
    model.set_rows([change])
    shown = lambda name: model.data(model.index(0, ATTRIBUTES.index(name)), Qt.ItemDataRole.DisplayRole)
    assert shown("row_a") == "2" and shown("row_b") == "3"
    assert shown("original") == "old" and shown("revised") == "=new"
    assert json.loads(shown("context_a")) == {"ID": "001", "Name": "old", "Other": "unchanged"}
    assert json.loads(shown("context_b"))["Name"] == "=new"
    for ext, writer in (("xlsx", export_excel), ("csv", export_csv)):
        path = tmp_path / f"report.{ext}"
        writer(result, path)
        if ext == "xlsx":
            wb = load_workbook(path)
            rows = list(wb["Differences"].values)
            wb.close()
        else:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.reader(stream))
        data = dict(zip(rows[0], rows[1]))
        assert str(data["Original Row"]) == "2" and str(data["Revised Row"]) == "3"
        assert json.loads(data["Original Entry (A)"])["Name"] == "old"
        assert json.loads(data["Updated Entry (B)"])["Name"] == "=new"


def test_cell_change_includes_whole_corresponding_rows(excel_book):
    a = excel_book("a.xlsx", {"Data": [["ID", "Name"], ["001", "old"]]})
    b = excel_book("b.xlsx", {"Data": [["ID", "Name"], ["001", "new"]]})
    change = compare(a, b, ComparisonSettings()).differences[0]
    assert change.row_a == change.row_b == 2
    assert change.context_a == {"A2": "001", "B2": "old"}
    assert change.context_b == {"A2": "001", "B2": "new"}


def test_added_entry_has_only_revised_source_row(csv_book, records):
    a = csv_book("a.csv", [["ID", "Name"]])
    b = csv_book("b.csv", [["ID", "Name"], ["001", "new"]])
    change = compare(a, b, records).differences[0]
    assert change.row_a is None and change.row_b == 2
    assert not change.context_a and change.context_b == {"ID": "001", "Name": "new"}
