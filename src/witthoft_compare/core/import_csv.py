from __future__ import annotations

import csv
import io
from pathlib import Path

from .models import CellSnapshot, InputError, SheetSnapshot, WorkbookSnapshot, checkpoint

csv.field_size_limit(2147483647)


def read_csv(path: Path, encoding: str = "auto", delimiter: str = "auto", cancel=None) -> WorkbookSnapshot:
    warnings = []
    checkpoint(cancel)
    raw = path.read_bytes()
    if encoding not in ("auto", "utf-8-sig", "utf-8", "cp1252"):
        raise InputError("Choose UTF-8, UTF-8 BOM, or Windows cp1252 encoding.")
    enc = "utf-8-sig" if encoding == "auto" else encoding
    try:
        text = raw.decode(enc)
    except UnicodeDecodeError:
        if encoding != "auto":
            raise InputError(f"Cannot decode {path.name} as {encoding}. Choose another CSV encoding.") from None
        enc = "cp1252"
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError:
            raise InputError("CSV encoding could not be read. Re-export as UTF-8 or select an encoding.") from None
        warnings.append("CSV decoded using Windows cp1252 fallback; check the preview.")
    if "\x00" in text:
        raise InputError("CSV contains NUL bytes. Re-export as UTF-8 CSV (UTF-16 is not supported).")
    if delimiter == "auto":
        try:
            delimiter = csv.Sniffer().sniff(text[:65536], delimiters=",;\t").delimiter
        except csv.Error:
            delimiter = ","
            warnings.append("Delimiter could not be detected; comma assumed. Check preview or override.")
    if delimiter not in (",", ";", "\t"):
        raise InputError("Delimiter must be comma, semicolon, or tab.")
    sheet = SheetSnapshot("CSV Data")
    width = None
    try:
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
        for row_number, row in enumerate(reader, 1):
            checkpoint(cancel)
            if width is None:
                width = len(row)
            if row and len(row) != width:
                raise InputError(f"CSV record {row_number} has {len(row)} fields; expected {width}. Check delimiter and quoting.")
            for col, value in enumerate(row, 1):
                sheet.cells[row_number, col] = CellSnapshot(value)
    except csv.Error as exc:
        raise InputError(f"Malformed CSV: {exc}. Check quotes and delimiters.") from exc
    return WorkbookSnapshot(path, "csv", {sheet.name: sheet}, warnings, {"encoding": enc, "delimiter": repr(delimiter)})
