from copy import deepcopy

from .cell_compare import compare_cells
from .models import ComparisonResult, Difference, InputError, MODES, checkpoint
from .record_compare import compare_records
from .sheet_mapping import sheet_pairs


def compare(original, revised, settings, *, cancel=None, progress=None):
    if settings.mode not in MODES:
        raise InputError("Select a supported comparison mode.")
    settings = deepcopy(settings)
    pairs = sheet_pairs(original, revised, settings)
    settings.sheet_pairs = pairs
    result = ComparisonResult(original, revised, settings)
    for side, book in (("A", original), ("B", revised)):
        for warning in book.warnings:
            result.warnings.append(Difference("Notice", "", category="Import / limitations", severity="Info", notes=f"{side}: {warning}"))
    if settings.mode == MODES[0]:
        result.warnings.append(Difference("Notice", "", category="Cell alignment", severity="Info", notes="Cells are matched by address. Row insertions may cascade into many changes; use Match Records for tables."))
        if original.kind == "csv" or revised.kind == "csv":
            if settings.formatting or settings.hyperlinks:
                result.warnings.append(Difference("Notice", "", category="Not comparable", severity="Warning", notes="Formatting/hyperlinks excluded because CSV has no Excel metadata."))
                settings.formatting = settings.hyperlinks = False
        if not settings.formulas:
            result.warnings.append(Difference("Notice", "", category="Excluded formulas", notes="Cells containing a formula on either side have value comparison excluded; formulas are never evaluated."))
    used_a, used_b = {x for x, _ in pairs}, {y for _, y in pairs}
    for side, book, used in (("A", original, used_a), ("B", revised, used_b)):
        other = revised if side == "A" else original
        for name in book.sheets:
            if name not in used:
                # Selected-out same-name sheets are not claimed as added/removed.
                if name in other.sheets:
                    result.warnings.append(Difference("Notice", name, category="Excluded worksheet", notes=f"{side}: sheet not selected for comparison."))
                else:
                    result.structural.append(Difference("Removed" if side == "A" else "Added", name, category="Worksheet",
                        original=name if side == "A" else None, revised=name if side == "B" else None,
                        notes="Only in this input, unpaired. No rename inferred. Cells excluded from top-line counts."))
    for index, (na, nb) in enumerate(pairs):
        checkpoint(cancel)
        if progress:
            progress(f"Comparing worksheet {index + 1} / {len(pairs)}: {na} → {nb}")
        label = na if na == nb else f"{na} → {nb}"
        if settings.mode == MODES[0]:
            compare_cells(original.sheets[na], revised.sheets[nb], label, result, cancel)
        else:
            compare_records(original.sheets[na], revised.sheets[nb], label, result, cancel)
        result.counts["sheets"] += 1
    checkpoint(cancel)
    return result
