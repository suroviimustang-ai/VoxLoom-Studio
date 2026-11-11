from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from PyQt6 import QtCore as C

from .diagnostics import LOG


class Job(C.QObject):
    finished = C.pyqtSignal(dict, object)
    failed = C.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = C.QProcess(self)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self.stderr_tail = ""
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.readyReadStandardOutput.connect(self.process.readAllStandardOutput)
        self.temp = None
        self.model_temp = None
        self.cancelled = False
        self.settled = False

    def start(self, request, data=None, noise=None):
        request = dict(request)
        self.action = request.get("action")
        self.temp = tempfile.TemporaryDirectory(prefix="voxloom-")
        if self.action == "install_models":
            from .processing import writable_models

            models = writable_models()
            models.mkdir(parents=True, exist_ok=True)
            self.model_temp = tempfile.TemporaryDirectory(
                prefix=".install-", dir=models
            )
            request["staging_root"] = self.model_temp.name
        root = Path(self.temp.name)
        if data is not None:
            np.save(root / "input.npy", data, allow_pickle=False)
            request["input"] = str(root / "input.npy")
        if noise is not None:
            np.save(root / "noise.npy", noise, allow_pickle=False)
            request["noise"] = str(root / "noise.npy")
        path = root / "request.json"
        path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
        args = ["--worker", str(path)]
        if not getattr(sys, "frozen", False):
            args.insert(0, str(Path(__file__).resolve().parents[1] / "main.py"))
        self.process.setProgram(sys.executable)
        self.process.setArguments(args)
        self.process.start()

    def cancel(self):
        self.cancelled = True
        self.process.kill()

    def _read_stderr(self):
        text = bytes(self.process.readAllStandardError()).decode(
            "utf-8", errors="replace"
        )
        self.stderr_tail = (self.stderr_tail + text)[-4096:]

    def _error(self, error):
        if error == C.QProcess.ProcessError.FailedToStart:
            self._settle({"ok": False, "error": self.process.errorString()}, None)

    def _finished(self, *args):
        if self.settled:
            return
        output = None
        try:
            root = Path(self.temp.name)
            if self.cancelled:
                result = {
                    "ok": False,
                    "error": "Операция отменена. Предыдущий результат сохранён.",
                }
            elif (root / "result.json").exists():
                result = json.loads((root / "result.json").read_text(encoding="utf-8"))
                if not isinstance(result, dict) or not isinstance(
                    result.get("ok"), bool
                ):
                    raise ValueError("Некорректный формат ответа процесса.")
                if result["ok"] and args and args[0] != 0:
                    raise RuntimeError("Процесс аварийно завершился после обработки.")
                if result["ok"] and getattr(self, "action", None) in (
                    "load",
                    "denoise",
                    "normalize",
                ):
                    output = np.load(root / "output.npy", allow_pickle=False)
                    if (
                        output.ndim != 2
                        or not len(output)
                        or not np.isfinite(output).all()
                    ):
                        raise ValueError("Повреждён результат обработки аудио.")
            else:
                self._read_stderr()
                result = {
                    "ok": False,
                    "error": f"Процесс обработки завершился без результата.\n{self.stderr_tail[-2500:]}",
                }
        except Exception as exc:
            LOG.exception("Invalid worker response")
            result = {
                "ok": False,
                "error": f"Не удалось прочитать результат обработки: {exc}",
            }
        self._settle(result, output)

    def cleanup(self):
        for temporary in (self.temp, self.model_temp):
            if temporary:
                try:
                    temporary.cleanup()
                except OSError:
                    LOG.exception("Temporary files could not be removed")

    def _settle(self, result, output):
        if self.settled:
            return
        self.settled = True
        self.cleanup()
        self.finished.emit(result, output)
