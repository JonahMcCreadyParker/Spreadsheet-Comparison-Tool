from .models import InputError


def sheet_pairs(a, b, settings):
    if settings.sheet_pairs:
        for x, y in settings.sheet_pairs:
            if x not in a.sheets or y not in b.sheets:
                raise InputError(f"Worksheet pair is no longer available: {x} → {y}. Select sheets again.")
        if len(set(settings.sheet_pairs)) != len(settings.sheet_pairs):
            raise InputError("Worksheet pairs must not be repeated.")
        if len({a for a, _ in settings.sheet_pairs}) != len(settings.sheet_pairs) or len({b for _, b in settings.sheet_pairs}) != len(settings.sheet_pairs):
            raise InputError("Each worksheet may appear in only one pair per comparison, to prevent double counting.")
        return list(settings.sheet_pairs)
    if a.kind == b.kind == "csv":
        return [(next(iter(a.sheets)), next(iter(b.sheets)))]
    if (a.kind == "csv") != (b.kind == "csv"):
        raise InputError("For CSV versus Excel, explicitly select a worksheet pair.")
    return [(name, name) for name in a.sheets if name in b.sheets]
