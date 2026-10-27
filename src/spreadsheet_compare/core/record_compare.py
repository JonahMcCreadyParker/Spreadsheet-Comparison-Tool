from collections import defaultdict
import json

from .models import Difference, InputError, Record, checkpoint
from .normalisation import display, normalise, same


def table(sheet, header_row=1):
    columns = sorted(col for (row, col), cell in sheet.cells.items() if row == header_row and cell.value is not None)
    headers = [str(sheet.value(header_row, col)) for col in columns]
    if not headers:
        raise InputError(f"No column headers in {sheet.name}, row {header_row}. Set the header row in Settings.")
    if any(not h.strip() for h in headers) or len(set(headers)) != len(headers):
        raise InputError(f"Blank or duplicate column labels in {sheet.name}, row {header_row}. Give each column a unique name.")
    by_row = defaultdict(dict)
    for (row, col), cell in sheet.cells.items():
        if row > header_row:
            by_row[row][col] = cell.value
    records = []
    for row, cells in sorted(by_row.items()):
        if not any(v is not None and v != "" for v in cells.values()):
            continue
        if any(c not in columns and v is not None and v != "" for c, v in cells.items()):
            raise InputError(f"Data without a column header in {sheet.name}, row {row}. Correct headers or select the right header row.")
        records.append(Record(row, {h: cells.get(c) for h, c in zip(headers, columns)}))
    return headers, records


def index_records(records, keys, settings):
    groups, blanks = defaultdict(list), []
    for record in records:
        raw = [record.values[k] for k in keys]
        if any(v is None or (isinstance(v, str) and not v.strip()) for v in raw):
            blanks.append(record)
        else:
            groups[tuple(normalise(v, settings) for v in raw)].append(record)
    return groups, blanks


def key_label(record, keys):
    # JSON tuple representation avoids collisions in display (keys themselves are typed tuples).
    return json.dumps([record.values[k] for k in keys], ensure_ascii=False, default=str)


def preview_stats(sheet, settings, side="A"):
    headers, records = table(sheet, settings.header_a if side == "A" else settings.header_b)
    keys = settings.keys if side == "A" else [settings.mappings.get(k, k) for k in settings.keys]
    if not keys or any(k not in headers for k in keys):
        return headers, records, "Select valid key columns to see duplicate/blank counts."
    groups, blanks = index_records(records, keys, settings)
    duplicate_rows = sum(len(v) for v in groups.values() if len(v) > 1)
    return headers, records, f"{len(records)} records; {duplicate_rows} rows with duplicate keys; {len(blanks)} blank keys."


def compare_records(a, b, label, result, cancel=None):
    s = result.settings
    ha, ra = table(a, s.header_a)
    hb, rb = table(b, s.header_b)
    if not s.keys:
        raise InputError("Select one or more match key columns. Engineering mode proposes Tag Name when available.")
    mapping = {h: s.mappings.get(h, h) for h in ha}
    if any(k not in ha or mapping.get(k) not in hb for k in s.keys):
        raise InputError(f"Missing key column in {label}. Check selected keys and Original → Revised field mappings.")
    active_mapping = {k: v for k, v in mapping.items() if v in hb}
    if len(set(active_mapping.values())) != len(active_mapping):
        raise InputError("Two original columns map to the same revised column. Use one-to-one field mappings.")
    for h in ha:
        if mapping[h] not in hb:
            result.structural.append(Difference("Removed", label, field=h, original=h, category="Column"))
    for h in hb:
        if h not in mapping.values():
            result.structural.append(Difference("Added", label, field=h, revised=h, category="Column"))
    fields = [h for h in ha if mapping[h] in hb and h not in s.ignored]
    kb = [mapping[k] for k in s.keys]
    ga, ba = index_records(ra, s.keys, s)
    gb, bb = index_records(rb, kb, s)
    for side, records, keys in (("A", ba, s.keys), ("B", bb, kb)):
        for record in records:
            result.warnings.append(Difference("Ambiguous", label, f"{side} row {record.row}", category="Blank key", severity="Warning",
                notes="Blank identity; excluded from additions/removals and modifications.", row_a=record.row if side == "A" else None,
                row_b=record.row if side == "B" else None, context_a=record.values if side == "A" else {}, context_b=record.values if side == "B" else {}))
    for index, key in enumerate(sorted(ga.keys() | gb.keys(), key=repr)):
        if index % 500 == 0:
            checkpoint(cancel)
        aa, ab = ga.get(key, []), gb.get(key, [])
        if len(aa) > 1 or len(ab) > 1:
            for side, group, keys in (("A", aa, s.keys), ("B", ab, kb)):
                for record in group:
                    result.warnings.append(Difference("Ambiguous", label, key_label(record, keys), category="Duplicate key", severity="Warning",
                        notes=f"{side} row {record.row}: key duplicated in at least one input; no arbitrary pairing.",
                        row_a=record.row if side == "A" else None, row_b=record.row if side == "B" else None,
                        context_a=record.values if side == "A" else {}, context_b=record.values if side == "B" else {}))
            continue
        if not aa or not ab:
            added = not aa
            record, keys = (ab[0], kb) if added else (aa[0], s.keys)
            identity = key_label(record, keys)
            payload = {"Worksheet": label, "Key": identity, "Source row": record.row, "Values": record.values}
            (result.added_records if added else result.removed_records).append(payload)
            result.counts["added" if added else "removed"] += 1
            result.differences.append(Difference("Added" if added else "Removed", label, identity, "Record",
                None if added else record.values, record.values if added else None, "Tag" if s.mode.endswith("Tag Records") else "Record",
                row_a=None if added else record.row, row_b=record.row if added else None,
                context_a={} if added else record.values, context_b=record.values if added else {}))
            continue
        oa, ob = aa[0], ab[0]
        changed = [h for h in fields if not same(oa.values[h], ob.values[mapping[h]], s)]
        result.counts["modified" if changed else "unchanged"] += 1
        result.counts["fields"] += len(changed)
        for h in changed:
            category, severity = "Value", "Info"
            if s.mode.endswith("Tag Records"):
                from .engineering_rules import classify
                category, severity = classify(h)
            d = Difference("Modified", label, key_label(oa, s.keys), h, oa.values[h], ob.values[mapping[h]], category, severity,
                "Engineering review requested; a change is not necessarily a defect." if severity == "Review" else "",
                oa.row, ob.row, oa.values, ob.values)
            result.differences.append(d)
            if severity == "Review":
                result.warnings.append(Difference("Check", label, d.identity, h, d.original, d.revised, category, "Review", d.notes,
                    oa.row, ob.row, oa.values, ob.values))
    if s.mode.endswith("Tag Records"):
        from .engineering_rules import validate
        validate(ra, ha, label, "A", result)
        # Canonical original names allow manual mappings to participate in engineering checks.
        translated = [Record(r.row, {next((x for x, y in mapping.items() if y == h), h): v for h, v in r.values.items()}) for r in rb]
        validate(translated, list(translated[0].values) if translated else hb, label, "B", result)
