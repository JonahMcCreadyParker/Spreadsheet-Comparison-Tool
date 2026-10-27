import csv
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from openpyxl import Workbook

from witthoft_compare.core.import_service import import_file
from witthoft_compare.core.models import ComparisonSettings, MODES


@pytest.fixture
def csv_book(tmp_path):
    def create(name, rows, encoding="utf-8-sig", delimiter=","):
        path = tmp_path / name
        with path.open("w", newline="", encoding=encoding) as stream:
            csv.writer(stream, delimiter=delimiter).writerows(rows)
        return import_file(path)
    return create


@pytest.fixture
def excel_book(tmp_path):
    def create(name, sheets=None, edit=None):
        path = tmp_path / name
        wb = Workbook()
        wb.remove(wb.active)
        for title, rows in (sheets or {"Data": []}).items():
            ws = wb.create_sheet(title)
            for row in rows:
                ws.append(row)
        if edit:
            edit(wb)
        wb.save(path)
        wb.close()
        return import_file(path)
    return create


@pytest.fixture
def records():
    return ComparisonSettings(mode=MODES[1], keys=["ID"])


@pytest.fixture(scope="session")
def app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])
