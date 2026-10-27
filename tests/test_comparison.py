from copy import deepcopy
import time

import pytest
from openpyxl.styles import Font

from witthoft_compare.core.compare_service import compare
from witthoft_compare.core.models import ComparisonSettings, MODES, ADMIN_FIELDS, InputError, Cancelled
from witthoft_compare.core.normalisation import same


def test_equal_and_reordered(csv_book, records):
    rows = [["ID", "Value"], ["001", "x"], ["002", "y"]]
    a, b = csv_book("a.csv", rows), csv_book("b.csv", rows[:1] + rows[:0:-1])
    r = compare(a, b, records)
    assert not r.differences and r.counts["unchanged"] == 2
    assert not compare(a, a, ComparisonSettings()).differences


def test_added_removed_multiple_fields(csv_book, records):
    a = csv_book("a.csv", [["ID", "x", "y", "z"], ["1", "a", "b", "c"], ["2", "x", "x", "x"]])
    b = csv_book("b.csv", [["ID", "x", "y", "z"], ["3", "y", "y", "y"], ["1", "d", "e", "f"]])
    r = compare(a, b, records)
    assert {k: r.counts[k] for k in ("added", "removed", "modified", "fields")} == dict(added=1, removed=1, modified=1, fields=3)
    assert len(r.added_records) == len(r.removed_records) == 1


def test_duplicate_key_quarantines_both_sides(csv_book, records):
    a = csv_book("a.csv", [["ID", "v"], ["1", "a"], ["1", "b"], ["", "c"]])
    b = csv_book("b.csv", [["ID", "v"], ["1", "z"], ["  ", "d"]])
    r = compare(a, b, records)
    assert not r.differences
    assert sum(d.category == "Duplicate key" for d in r.warnings) == 3
    assert sum(d.category == "Blank key" for d in r.warnings) == 2
    assert not any(r.counts[k] for k in ("added", "removed", "modified", "unchanged"))


def test_composite_and_mapping(csv_book, records):
    a = csv_book("a.csv", [["Plant", "ID", "Name"], ["P1", "1", "a"], ["P2", "1", "b"]])
    b = csv_book("b.csv", [["Plant", "Tag", "Label"], ["P2", "1", "b"], ["P1", "1", "a"]])
    records.keys = ["Plant", "ID"]
    records.mappings = {"ID": "Tag", "Name": "Label"}
    r = compare(a, b, records)
    assert r.counts["unchanged"] == 2 and not r.rows


def test_structural_sheets_columns(excel_book, records):
    a = excel_book("a.xlsx", {"Data": [["ID", "Old"], [1, "v"]], "Before": [[1]]})
    b = excel_book("b.xlsx", {"Data": [["ID", "New"], [1, "v"]], "After": [[1]]})
    r = compare(a, b, records)
    assert {(d.status, d.category) for d in r.structural} == {("Added", "Worksheet"), ("Removed", "Worksheet"), ("Added", "Column"), ("Removed", "Column")}
    assert not r.differences and r.counts["sheets"] == 1
    assert r.counts["unchanged"] == 1


def test_no_sheet_rename_inference(excel_book):
    a = excel_book("a.xlsx", {"Old": [[1]]})
    b = excel_book("b.xlsx", {"New": [[2]]})
    r = compare(a, b, ComparisonSettings())
    assert r.counts["sheets"] == 0 and len(r.structural) == 2
    s = ComparisonSettings(sheet_pairs=[("Old", "New")])
    r = compare(a, b, s)
    assert r.counts["modified"] == 1 and not r.structural


def test_cell_formula_and_optional_styles(excel_book):
    def edit(wb):
        ws = wb["Data"]
        ws["A1"] = "=SUM(B1:B11)"
        ws["B1"].font = Font(strike=True)
        ws["C1"].hyperlink = "https://revised.example/"
        ws["D1"].number_format = "0.00"
    a = excel_book("a.xlsx", {"Data": [["=SUM(B1:B10)", "same", "link", 1]]})
    b = excel_book("b.xlsx", {"Data": [["=SUM(B1:B10)", "same", "link", 1]]}, edit)
    s = ComparisonSettings()
    r = compare(a, b, s)
    assert r.counts["modified"] == 1 and r.differences[0].category == "Formula"
    s.formatting = s.hyperlinks = True
    r = compare(a, b, s)
    assert r.counts["modified"] == 4
    assert {d.field for d in r.differences} >= {"font", "number_format", "Hyperlink target"}
    s.formulas = False
    assert compare(a, b, s).counts["modified"] == 3


def test_cell_added_removed_count_once(excel_book):
    def edit(wb):
        wb["Data"]["A1"] = None
        wb["Data"]["B2"] = 2
        wb["Data"]["B2"].font = Font(strike=True)
    a = excel_book("a.xlsx", {"Data": [[1]]})
    b = excel_book("b.xlsx", {"Data": [[1]]}, edit)
    r = compare(a, b, ComparisonSettings(formatting=True))
    assert r.counts["added"] == r.counts["removed"] == 1


def test_mixed_explicit_normalisation(csv_book, excel_book, records):
    a = csv_book("a.csv", [["ID", "Value"], ["001", "1"]])
    b = excel_book("b.xlsx", {"Table": [["ID", "Value"], ["001", 1]]})
    with pytest.raises(InputError, match="explicitly"):
        compare(a, b, records)
    records.sheet_pairs = [("CSV Data", "Table")]
    assert compare(a, b, records).counts["modified"] == 1
    records.numeric_equivalence = True
    assert compare(a, b, records).counts["modified"] == 0


@pytest.mark.parametrize("a,b,equal", [(None, "None", False), (None, "NaN", False), (None, 0, False), (None, "", False), ("001", 1, False), (1, "1", False), (" ", "", False), (True, 1, False)])
def test_fidelity_default(a, b, equal):
    assert same(a, b, ComparisonSettings()) is equal


def test_normalisation_explicit():
    s = ComparisonSettings(trim=True, case_sensitive=False, blank_empty=True, numeric_equivalence=True)
    assert same(" A ", "a", s)
    assert same(None, "  ", s)
    assert same(1, "1.0", s)
    assert not same("001", 1, s)
    assert not same(None, "None", s)


@pytest.mark.parametrize("headers", [["Name"], ["ID", "ID"], ["ID", " "]])
def test_invalid_keys_headers(csv_book, records, headers):
    book = csv_book("a.csv", [headers, ["x"] * len(headers)])
    with pytest.raises(InputError):
        compare(book, book, records)


def test_header_row_and_unmapped(csv_book, records):
    book = csv_book("a.csv", [["Title", ""], ["ID", "Value"], ["1", "a"]])
    records.header_a = records.header_b = 2
    assert compare(book, book, records).counts["unchanged"] == 1
    records.mappings = {"Value": ""}
    r = compare(book, book, records)
    assert len(r.structural) == 2


def test_10000_records(csv_book, records):
    rows = [["ID", "Value"]] + [[f"{i:06}", "value"] for i in range(12000)]
    a, b = csv_book("a.csv", rows), csv_book("b.csv", rows[:1] + rows[:0:-1])
    started = time.monotonic()
    r = compare(a, b, records)
    assert r.counts["unchanged"] == 12000 and not r.differences
    assert time.monotonic() - started < 10


def test_cancellation(csv_book, records):
    a = csv_book("a.csv", [["ID"], ["1"]])
    with pytest.raises(Cancelled):
        compare(a, a, records, cancel=lambda: True)


def test_csv_metadata_exclusion(csv_book, excel_book):
    a = csv_book("a.csv", [["Value"], ["x"]])
    b = excel_book("b.xlsx", {"Data": [["Value"], ["x"]]})
    r = compare(a, b, ComparisonSettings(sheet_pairs=[("CSV Data", "Data")], formatting=True, hyperlinks=True))
    assert not r.differences
    assert not r.settings.formatting and not r.settings.hyperlinks
    assert any(d.category == "Not comparable" for d in r.warnings)


def test_blank_sheets_and_merged_changes(excel_book):
    a = excel_book("a.xlsx", {"Blank": []})
    b = excel_book("b.xlsx", {"Blank": []})
    assert compare(a, b, ComparisonSettings()).counts["modified"] == 0
    c = excel_book("c.xlsx", {"Blank": []}, lambda wb: wb["Blank"].merge_cells("A1:B2"))
    r = compare(a, c, ComparisonSettings())
    assert not r.differences and r.structural[0].field == "Merged ranges"


def test_array_formula_is_stable(excel_book):
    from openpyxl.worksheet.formula import ArrayFormula
    def edit(wb):
        wb["Data"]["A1"] = ArrayFormula(ref="A1:A2", text="=ROW(A1:A2)")
    a, b = excel_book("a.xlsx", edit=edit), excel_book("b.xlsx", edit=edit)
    assert not compare(a, b, ComparisonSettings()).differences


def test_sheet_pair_cannot_double_count(excel_book):
    book = excel_book("a.xlsx", {"One": [[1]], "Two": [[2]]})
    with pytest.raises(InputError, match="double counting"):
        compare(book, book, ComparisonSettings(sheet_pairs=[("One", "One"), ("One", "Two")]))
