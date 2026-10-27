from collections import defaultdict

from .models import Difference


def classify(field):
    name = field.strip().casefold()
    if name in ("address", "plc address"):
        return "PLC address / mapping", "Review"
    if name == "data type":
        return "Data type", "Review"
    if name in ("i/o device", "cluster name"):
        return "Device / namespace", "Review"
    if name in ("raw zero scale", "raw full scale", "eng zero scale", "eng full scale"):
        return "Scaling", "Review"
    if name in ("eng units", "deadband", "format"):
        return "Units / deadband / format", "Info"
    if name == "comment":
        return "Description", "Info"
    if name in ("equipment", "item name"):
        return "Equipment association", "Info"
    return "Configuration / metadata", "Info"


def validate(records, headers, sheet, side, result):
    names = {h.strip().casefold(): h for h in headers}
    address = names.get("address", names.get("plc address"))
    device, cluster = names.get("i/o device"), names.get("cluster name")
    tag = names.get("tag name")
    groups = defaultdict(list)
    for r in records:
        if result.settings.duplicate_addresses and address:
            val = r.values.get(address)
            if val is not None and str(val).strip() and str(val) not in result.settings.address_exceptions:
                groups[(str(r.values.get(device)), str(r.values.get(cluster)), str(val))].append(r)
        if result.settings.missing_scaling:
            for field in ("raw zero scale", "raw full scale", "eng zero scale", "eng full scale"):
                col = names.get(field)
                if col is None or r.values.get(col) is None or str(r.values.get(col)).strip() == "":
                    result.warnings.append(Difference("Check", sheet, str(r.values.get(tag, f"row {r.row}")), col or field,
                        category="Missing scaling", severity="Review", notes=f"{side} row {r.row}: optional completeness check; engineering applicability must be reviewed.",
                        row_a=r.row if side == "A" else None, row_b=r.row if side == "B" else None))
    for namespace, group in groups.items():
        if len(group) > 1:
            result.warnings.append(Difference("Check", sheet, str(namespace), field=address, category="Possible duplicate address", severity="Review",
                notes=f"{side}: address reused in device/cluster namespace at rows {', '.join(str(r.row) for r in group)}. May be intentional; exceptions can be configured."))
