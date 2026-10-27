from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
import re


def normalise(value, settings):
    if value is None:
        return ("blank", "")
    if isinstance(value, str):
        val = value.strip() if settings.trim else value
        if settings.blank_empty and not val.strip():
            return ("blank", "")
        if settings.numeric_equivalence and re.fullmatch(r"[+-]?(?:0|[1-9]\d*)(?:\.\d+)?", val):
            try:
                return ("number", Decimal(val))
            except InvalidOperation:
                pass
        return ("text", val if settings.case_sensitive else val.casefold())
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, (int, float, Decimal)):
        return ("number", Decimal(str(value)))
    if isinstance(value, (date, datetime, time)):
        return (type(value).__name__, value.isoformat())
    return (type(value).__name__, str(value))


def same(a, b, settings):
    return normalise(a, settings) == normalise(b, settings)


def display(value):
    if value is None:
        return "⟨blank cell⟩"
    if value == "":
        return '⟨empty text⟩'
    if isinstance(value, str) and not value.strip():
        return repr(value)
    return str(value)
