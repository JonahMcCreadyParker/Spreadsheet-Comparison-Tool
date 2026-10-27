from __future__ import annotations

from dataclasses import asdict, dataclass, field as dc_field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

MODES = ("General — Cell by Cell", "General — Match Records", "Engineering — PLC / Tag Records")
ADMIN_FIELDS = ("Project", "OID", "Unique ID", "EDITCODE", "LINKED", "TAGGENLINK")


class InputError(ValueError):
    """An actionable input/configuration error."""


class Cancelled(Exception):
    pass


@dataclass
class CellSnapshot:
    value: Any = None
    formula: bool = False
    style: dict[str, str] = dc_field(default_factory=dict)
    hyperlink: str | None = None


@dataclass
class SheetSnapshot:
    name: str
    cells: dict[tuple[int, int], CellSnapshot] = dc_field(default_factory=dict)
    merged: tuple[str, ...] = ()
    default_style: dict[str, str] = dc_field(default_factory=dict)

    def value(self, row: int, col: int) -> Any:
        return self.cells.get((row, col), CellSnapshot()).value


@dataclass
class WorkbookSnapshot:
    path: Path
    kind: str
    sheets: dict[str, SheetSnapshot]
    warnings: list[str] = dc_field(default_factory=list)
    import_options: dict = dc_field(default_factory=dict)


@dataclass
class ComparisonSettings:
    mode: str = MODES[0]
    sheet_pairs: list[tuple[str, str]] = dc_field(default_factory=list)
    keys: list[str] = dc_field(default_factory=list)
    mappings: dict[str, str] = dc_field(default_factory=dict)
    ignored: list[str] = dc_field(default_factory=list)
    header_a: int = 1
    header_b: int = 1
    trim: bool = False
    case_sensitive: bool = True
    blank_empty: bool = False
    numeric_equivalence: bool = False
    formulas: bool = True
    formatting: bool = False
    hyperlinks: bool = False
    duplicate_addresses: bool = True
    missing_scaling: bool = False
    address_exceptions: list[str] = dc_field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ComparisonSettings:
        defaults = cls()
        if not isinstance(data, dict):
            return defaults
        clean = {}
        for name in defaults.__dataclass_fields__:
            if name not in data:
                continue
            val, default = data[name], getattr(defaults, name)
            if type(val) is type(default):
                clean[name] = val
        result = cls(**clean)
        if result.mode not in MODES:
            result.mode = MODES[0]
        for name in ("keys", "ignored", "address_exceptions"):
            setattr(result, name, [v for v in getattr(result, name) if isinstance(v, str)])
        result.mappings = {k: v for k, v in result.mappings.items() if isinstance(k, str) and isinstance(v, str)}
        result.sheet_pairs = [tuple(p) for p in result.sheet_pairs if isinstance(p, (list, tuple)) and len(p) == 2 and all(isinstance(x, str) for x in p)]
        result.header_a = max(1, min(result.header_a, 1048576))
        result.header_b = max(1, min(result.header_b, 1048576))
        return result


@dataclass
class Record:
    row: int
    values: dict[str, Any]


@dataclass
class Difference:
    status: str
    worksheet: str
    identity: str = ""
    field: str = ""
    original: Any = None
    revised: Any = None
    category: str = "Value"
    severity: str = "Info"
    notes: str = ""
    row_a: int | None = None
    row_b: int | None = None
    context_a: dict = dc_field(default_factory=dict)
    context_b: dict = dc_field(default_factory=dict)


@dataclass
class ComparisonResult:
    original: WorkbookSnapshot
    revised: WorkbookSnapshot
    settings: ComparisonSettings
    timestamp: str = dc_field(default_factory=lambda: datetime.now().astimezone().isoformat(timespec="seconds"))
    differences: list[Difference] = dc_field(default_factory=list)
    warnings: list[Difference] = dc_field(default_factory=list)
    structural: list[Difference] = dc_field(default_factory=list)
    added_records: list[dict] = dc_field(default_factory=list)
    removed_records: list[dict] = dc_field(default_factory=list)
    counts: dict[str, int] = dc_field(default_factory=lambda: dict(added=0, removed=0, modified=0, unchanged=0, fields=0, sheets=0, errors=0))

    @property
    def rows(self) -> list[Difference]:
        return self.differences + self.structural + self.warnings


Progress = Callable[[str], None]
Check = Callable[[], bool]


def checkpoint(cancel: Check | None = None) -> None:
    if cancel and cancel():
        raise Cancelled("Operation cancelled; no report was written.")

