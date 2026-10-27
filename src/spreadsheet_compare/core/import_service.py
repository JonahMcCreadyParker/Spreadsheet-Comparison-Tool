from pathlib import Path

from .import_csv import read_csv
from .import_excel import read_excel
from .models import InputError, checkpoint


def import_file(path, *, encoding="auto", delimiter="auto", cancel=None, progress=None):
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise InputError(f"File not found: {path}. Browse to an existing file.")
    if path.suffix.lower() not in (".csv", ".xlsx", ".xlsm"):
        raise InputError("Unsupported format. Use .csv, .xlsx, or .xlsm. Convert legacy .xls in Excel first.")
    try:
        size = path.stat().st_size
        if progress:
            progress(f"Reading {path.name} ({size / 1048576:.1f} MB)…")
        checkpoint(cancel)
        result = read_csv(path, encoding, delimiter, cancel) if path.suffix.lower() == ".csv" else read_excel(path, cancel)
        if size > 50 * 1048576:
            result.warnings.append("Large input (>50 MB): import and export may require substantial time and memory.")
        return result
    except OSError as exc:
        raise InputError(f"Cannot read {path.name}. Check file permissions and whether another program has locked it. {exc}") from exc
