import json
import os
from pathlib import Path
import tempfile

from ..core.models import ComparisonSettings


def config_path():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".config"))
    return base / "WitthoftEngineering" / "SpreadsheetCompare" / "profiles.json"


def load_profiles(path=None):
    try:
        data = json.loads(Path(path or config_path()).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}, ComparisonSettings()
        profiles = data.get("profiles", {})
        if not isinstance(profiles, dict):
            profiles = {}
        return {k: ComparisonSettings.from_dict(v) for k, v in profiles.items() if isinstance(v, dict)}, ComparisonSettings.from_dict(data.get("last", {}))
    except (OSError, ValueError, TypeError):
        return {}, ComparisonSettings()


def save_profiles(profiles, last, path=None):
    path = Path(path or config_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"profiles": {k: v.as_dict() for k, v in profiles.items()}, "last": last.as_dict()}
    handle, temp = tempfile.mkstemp(dir=path.parent, suffix=".json")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
