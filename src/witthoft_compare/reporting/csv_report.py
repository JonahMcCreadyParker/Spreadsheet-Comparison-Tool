import csv

from .common import HEADERS, report_target, row_values
from ..core.models import checkpoint


def protect_csv(value):
    if value is None:
        return ""
    value = str(value)
    if value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")):
        return "'" + value
    return value


def export_csv(result, path, *, cancel=None, progress=None):
    with report_target(path, result, ".csv") as temp:
        with temp.open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.writer(stream)
            writer.writerow(HEADERS)
            for index, d in enumerate(result.rows):
                if index % 500 == 0:
                    checkpoint(cancel)
                writer.writerow([protect_csv(v) for v in row_values(d)])
        checkpoint(cancel)
    return str(path)
