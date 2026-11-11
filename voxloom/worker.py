"""One disposable process per operation: bounded threads and hard cancellation."""

from __future__ import annotations

import json
import traceback
from pathlib import Path

import numpy as np


def execute(request_path: str) -> int:
    root = Path(request_path).parent
    result = {}
    try:
        request = json.loads(Path(request_path).read_text(encoding="utf-8"))
        if not isinstance(request, dict):
            raise ValueError("Некорректный запрос обработки.")
        from .audio import load_audio, save_audio
        from .processing import denoise, normalize
        from .speech import detect, transcribe

        action = request["action"]
        if action == "load":
            data, rate = load_audio(request["path"])
            np.save(root / "output.npy", data, allow_pickle=False)
            result = {"rate": rate}
        else:
            data = np.load(request["input"], mmap_mode="r", allow_pickle=False)
            rate = request["rate"]
            if action == "denoise":
                noise = (
                    np.load(request["noise"], allow_pickle=False)
                    if request.get("noise")
                    else None
                )
                output = denoise(
                    data, rate, request["method"], request["strength"], noise
                )
                np.save(root / "output.npy", output, allow_pickle=False)
            elif action == "normalize":
                output, note = normalize(data, rate, request["mode"], request["target"])
                np.save(root / "output.npy", output, allow_pickle=False)
                result = {"message": note}
            elif action == "detect":
                result = {
                    "regions": [
                        r.as_dict()
                        for r in detect(
                            data, rate, request["threshold"], request["silence_ms"]
                        )
                    ]
                }
            elif action == "events":
                from .events import detect_events

                result = detect_events(
                    data,
                    rate,
                    request["queries"],
                    request.get("threshold", 0.5),
                    request.get("channel", 0),
                )
            elif action == "transcribe":
                result = transcribe(data, rate, request["model"], request["language"])
            elif action == "export":
                save_audio(request["path"], data, rate)
                result = {"message": f"Сохранено: {request['path']}"}
            else:
                raise ValueError("Неизвестная операция.")
        result["ok"] = True
    except Exception as exc:
        result = {"ok": False, "error": str(exc), "traceback": traceback.format_exc()}
    try:
        from .files import write_text_atomic

        write_text_atomic(root / "result.json", json.dumps(result, ensure_ascii=False))
    except OSError:
        # The parent also handles a missing response (e.g. full disk / access denied).
        return 1
    return 0 if result["ok"] else 1
