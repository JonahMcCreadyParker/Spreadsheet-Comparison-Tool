from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import json
import os
import re
import tempfile

from ..core.models import InputError

HEADERS = ["Status", "Worksheet", "Record Key or Cell", "Field", "Original Value", "Revised Value", "Category", "Severity", "Notes", "Original Row", "Revised Row", "Original Entry (A)", "Updated Entry (B)"]


def value_text(value):
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, default=str)
    if value is None:
        return "⟨blank cell⟩"
    if value == "":
        return "⟨empty text⟩"
    return str(value)


def row_values(d):
    return [d.status, d.worksheet, d.identity, d.field, value_text(d.original), value_text(d.revised), d.category, d.severity, d.notes, d.row_a, d.row_b,
            value_text(d.context_a) if d.context_a else "", value_text(d.context_b) if d.context_b else ""]


def suggested_name(result, suffix):
    safe = lambda s: re.sub(r'[^\w.-]+', '_', s)[:60]
    return f"Comparison_{safe(result.original.path.stem)}_to_{safe(result.revised.path.stem)}_{datetime.now():%Y-%m-%d_%H%M%S}.{suffix}"


@contextmanager
def report_target(path, result, extension):
    path = Path(path).expanduser().resolve()
    sources = (result.original.path.resolve(), result.revised.path.resolve())
    if path in sources or (path.exists() and any(os.path.samefile(path, p) for p in sources if p.exists())):
        raise InputError("Reports must be saved to a separate file; source files cannot be overwritten.")
    if path.suffix.lower() != extension:
        raise InputError(f"Choose a filename ending in {extension}.")
    if not path.parent.is_dir():
        raise InputError("Report folder does not exist.")
    handle, temp = tempfile.mkstemp(prefix=".comparison_", suffix=extension, dir=path.parent)
    os.close(handle)
    try:
        yield Path(temp)
        os.replace(temp, path)
    except PermissionError as exc:
        raise InputError("Cannot save the report. Close it in Excel or choose a writable folder.") from exc
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
