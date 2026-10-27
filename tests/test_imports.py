import pytest

from witthoft_compare.core.import_service import import_file
from witthoft_compare.core.models import InputError, Cancelled


def test_csv_fidelity(csv_book):
    a = csv_book("a.csv", [["ID", "Address", "Comment", "Empty", "Spaces"], ["00123", "S7:[PLC1]DB620,Real48,1", 'comma, quote"\nnewline', "", "  "]])
    s = a.sheets["CSV Data"]
    assert [s.value(2, c) for c in range(1, 6)] == ["00123", "S7:[PLC1]DB620,Real48,1", 'comma, quote"\nnewline', "", "  "]


def test_csv_cp1252_fallback(csv_book):
    book = csv_book("a.csv", [["ID", "Comment"], ["001", "café €"]], encoding="cp1252")
    assert book.sheets["CSV Data"].value(2, 2) == "café €"
    assert "fallback" in " ".join(book.warnings)


@pytest.mark.parametrize("delimiter", [",", ";", "\t"])
def test_delimiter(csv_book, delimiter):
    book = csv_book("a.csv", [["ID", "Name"], ["1", "a"]], delimiter=delimiter)
    assert book.sheets["CSV Data"].value(2, 2) == "a"
    assert book.import_options["delimiter"] == repr(delimiter)


def test_csv_formula_is_text(csv_book):
    book = csv_book("a.csv", [["ID"], ["=1+1"]])
    cell = book.sheets["CSV Data"].cells[2, 1]
    assert cell.value == "=1+1" and not cell.formula


def test_explicit_encoding_error(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_bytes(b"ID\n\x81\n")
    with pytest.raises(InputError, match="decode"):
        import_file(path, encoding="utf-8")


@pytest.mark.parametrize("text", ['ID,Name\n1,"unclosed', "ID,Name\n1,a,b", "ID\n\x00"])
def test_bad_csv(tmp_path, text):
    path = tmp_path / "bad.csv"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(InputError):
        import_file(path, delimiter=",")


def test_bad_files(tmp_path):
    with pytest.raises(InputError, match="not found"):
        import_file(tmp_path / "missing.csv")
    path = tmp_path / "old.xls"
    path.write_text("not excel")
    with pytest.raises(InputError, match="legacy"):
        import_file(path)
    path = tmp_path / "corrupt.xlsx"
    path.write_text("not excel")
    with pytest.raises(InputError, match="valid, unencrypted"):
        import_file(path)


def test_excel_sparse_merged_formula_xlsm(excel_book):
    def edit(wb):
        ws = wb["Data"]
        ws["XFD1048576"] = "edge"
        ws["B2"] = "=SUM(A1:A10)"
        ws.merge_cells("C3:D4")
    book = excel_book("a.xlsm", {"Data": [["ID"]], "Blank": []}, edit)
    assert book.sheets["Data"].cells[2, 2].formula
    assert book.sheets["Data"].merged == ("C3:D4",)
    assert len(book.sheets["Data"].cells) == 3
    assert not book.sheets["Blank"].cells


def test_cancel_import(csv_book):
    book = csv_book("a.csv", [["ID"], ["1"]])
    with pytest.raises(Cancelled):
        import_file(book.path, cancel=lambda: True)
