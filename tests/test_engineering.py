from spreadsheet_compare.core.compare_service import compare
from spreadsheet_compare.core.models import ADMIN_FIELDS, ComparisonSettings, MODES


def test_engineering_categories_ignores(csv_book):
    columns = ["Tag Name", "Address", "Data Type", "I/O Device", "Raw Full Scale", "Project", "OID"]
    a = csv_book("a.csv", [columns, ["TAG1", "S7:[PLC1]DB620,Real48,1", "REAL", "PLC1", "100", "old", "123"]])
    b = csv_book("b.csv", [columns, ["TAG1", "S7:[PLC1]DB620,Real52,1", "LONG", "PLC2", "200", "new", "456"]])
    s = ComparisonSettings(mode=MODES[2], keys=["Tag Name"], ignored=list(ADMIN_FIELDS))
    r = compare(a, b, s)
    assert r.counts["modified"] == 1 and r.counts["fields"] == 4
    assert {d.category for d in r.differences} == {"PLC address / mapping", "Data type", "Device / namespace", "Scaling"}
    assert len([d for d in r.warnings if d.severity == "Review"]) == 4
    assert r.differences[0].original == "S7:[PLC1]DB620,Real48,1"
    s.ignored = []
    assert compare(a, b, s).counts["fields"] == 6


def test_namespaces_and_exceptions(csv_book):
    columns = ["Tag Name", "Address", "I/O Device", "Cluster Name"]
    book = csv_book("a.csv", [columns, ["A", "10", "PLC1", "C1"], ["B", "10", "PLC2", "C1"], ["C", "10", "PLC1", "C2"]])
    s = ComparisonSettings(mode=MODES[2], keys=["Tag Name"])
    assert not compare(book, book, s).warnings
    book2 = csv_book("b.csv", [columns, ["A", "10", "PLC1", "C1"], ["B", "10", "PLC1", "C1"]])
    assert len(compare(book2, book2, s).warnings) == 2
    s.address_exceptions = ["10"]
    assert not compare(book2, book2, s).warnings
    s.address_exceptions = []
    s.duplicate_addresses = False
    assert not compare(book2, book2, s).warnings


def test_optional_missing_scaling(csv_book):
    book = csv_book("a.csv", [["Tag Name", "Raw Zero Scale"], ["A", "0"]])
    s = ComparisonSettings(mode=MODES[2], keys=["Tag Name"], missing_scaling=True)
    assert len(compare(book, book, s).warnings) == 6
