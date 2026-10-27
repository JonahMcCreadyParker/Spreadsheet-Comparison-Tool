"""Frozen entry point with startup diagnostics for windowed deployments."""
import json
import os
from pathlib import Path
import sys
import traceback

if __name__ == "__main__":
    try:
        from witthoft_compare.app import main
        code = main()
    except Exception:
        message = traceback.format_exc()
        if "--self-test" in sys.argv:
            folder = Path(sys.argv[sys.argv.index("--self-test") + 1]).resolve()
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "self-test.json").write_text(json.dumps({"passed": False, "startup_error": message}, indent=2), encoding="utf-8")
        else:
            folder = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "WitthoftEngineering" / "SpreadsheetCompare"
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "startup-error.log").write_text(message, encoding="utf-8")
            from PySide6.QtWidgets import QApplication, QMessageBox
            app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "Spreadsheet Compare startup error", f"The application could not start. Diagnostics: {folder / 'startup-error.log'}\n\n{message.splitlines()[-1]}")
        code = 1
    raise SystemExit(code)
