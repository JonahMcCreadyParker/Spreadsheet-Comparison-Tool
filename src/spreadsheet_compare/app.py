import sys

from PySide6.QtWidgets import QApplication

from .gui.main_window import MainWindow


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Spreadsheet Compare")
    app.setOrganizationName("Spreadsheet Compare")
    if "--self-test" in sys.argv:
        from .self_test import run_self_test
        index = sys.argv.index("--self-test")
        return run_self_test(app, sys.argv[index + 1])
    window = MainWindow()
    window.show()
    return app.exec()
