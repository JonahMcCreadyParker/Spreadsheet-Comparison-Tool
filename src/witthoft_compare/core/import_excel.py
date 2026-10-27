from __future__ import annotations

from pathlib import Path
from openpyxl import load_workbook
from openpyxl.cell.cell import Cell, MergedCell
from openpyxl.worksheet.formula import ArrayFormula, DataTableFormula
from openpyxl.xml.functions import tostring

from .models import CellSnapshot, InputError, SheetSnapshot, WorkbookSnapshot, checkpoint


def cell_style(cell):
    style = {"number_format": cell.number_format}
    for attribute in ("font", "fill", "border", "alignment", "protection"):
        style[attribute] = tostring(getattr(cell, attribute).to_tree()).decode("utf-8")
    return style


def read_excel(path: Path, cancel=None) -> WorkbookSnapshot:
    checkpoint(cancel)
    try:
        book = load_workbook(path, data_only=False, read_only=False, keep_links=False)
    except Exception as exc:
        raise InputError(f"Cannot open {path.name} as Excel. Check that it is a valid, unencrypted .xlsx/.xlsm workbook. ({type(exc).__name__})") from exc
    sheets = {}
    extra_warnings = set()
    try:
        for ws in book.worksheets:
            checkpoint(cancel)
            sheet = SheetSnapshot(ws.title, merged=tuple(sorted(str(r) for r in ws.merged_cells.ranges)), default_style=cell_style(Cell(ws)))
            # openpyxl's sparse store avoids materialising the theoretical Excel grid.
            for index, ((row, col), cell) in enumerate(ws._cells.items()):
                if index % 1000 == 0:
                    checkpoint(cancel)
                if isinstance(cell, MergedCell):
                    continue
                if cell.value is None and not cell.has_style and not cell.hyperlink:
                    continue
                style = cell_style(cell)
                link = cell.hyperlink
                value = cell.value
                if isinstance(value, ArrayFormula):
                    value = f"{value.text} [array range: {value.ref}]"
                elif isinstance(value, DataTableFormula):
                    value = str(sorted(dict(value).items()))
                    extra_warnings.add("Data table formulas are compared as stored descriptors; calculated results are not compared.")
                sheet.cells[row, col] = CellSnapshot(value, cell.data_type == "f", style, (link.target or link.location) if link else None)
            sheets[ws.title] = sheet
    finally:
        book.close()
    if not sheets:
        raise InputError("This workbook has no readable worksheets (chart-only workbooks are unsupported).")
    return WorkbookSnapshot(path, path.suffix[1:].lower(), sheets, [
        "Excel formulas are read as expressions and never evaluated. Macros are not executed.",
        "Conditional formatting appearance, themes, shapes, comments, and external link contents are not compared.",
    ] + sorted(extra_warnings))
