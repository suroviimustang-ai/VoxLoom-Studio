"""Local bounded diagnostic logs; never transmit recordings or transcripts."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG = logging.getLogger("voxloom")
LOG.addHandler(logging.NullHandler())


def configure_logging():
    if sys.platform == "win32":
        folder = (
            Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "VoxLoom" / "logs"
        )
    elif sys.platform == "darwin":
        folder = Path.home() / "Library/Logs/VoxLoom"
    else:
        folder = (
            Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
            / "voxloom/logs"
        )
    try:
        folder.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            folder / "voxloom.log",
            maxBytes=1024 * 1024,
            backupCount=2,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        LOG.addHandler(handler)
        LOG.setLevel(logging.INFO)
        return folder / "voxloom.log"
    except OSError:
        return None


def install_exception_handler(app, log_path):
    from PyQt6.QtWidgets import QMessageBox

    reporting = False

    def handle(kind, value, trace):
        nonlocal reporting
        if issubclass(kind, KeyboardInterrupt):
            app.quit()
            return
        LOG.error("Unhandled application error", exc_info=(kind, value, trace))
        if reporting:
            return
        reporting = True
        try:
            text = "Не удалось завершить действие. Сохраните результаты и перезапустите программу."
            if log_path:
                text += f"\n\nДиагностика: {log_path}"
            QMessageBox.critical(app.activeWindow(), "VoxLoom · ошибка", text)
        finally:
            reporting = False

    sys.excepthook = handle
