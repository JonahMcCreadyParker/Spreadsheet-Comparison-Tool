from threading import Event
import traceback

from PySide6.QtCore import QThread, Signal

from ..core.models import Cancelled, InputError


class Worker(QThread):
    succeeded = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    progress = Signal(str)

    def __init__(self, operation, parent=None):
        super().__init__(parent)
        self.operation = operation
        self.stop = Event()

    def run(self):
        try:
            value = self.operation(cancel=self.stop.is_set, progress=self.progress.emit)
            self.succeeded.emit(value)
        except Cancelled:
            self.cancelled.emit()
        except Exception as exc:
            message = str(exc) if isinstance(exc, (InputError, OSError, ValueError)) else f"{type(exc).__name__}: {exc}"
            self.failed.emit(message)

    def cancel(self):
        self.stop.set()
