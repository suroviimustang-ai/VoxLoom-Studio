import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]


def run_job(tmp_path, request):
    path = tmp_path / "request.json"
    path.write_text(json.dumps(request), encoding="utf-8")
    done = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--worker", str(path)],
        capture_output=True,
        text=True,
        timeout=90,
    )
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    return done, result


def test_load_worker_unicode_path(tmp_path):
    path = tmp_path / "Речь и шум.wav"
    sf.write(path, np.zeros((16000, 2), dtype=np.float32), 16000)
    done, result = run_job(tmp_path, {"action": "load", "path": str(path)})
    assert done.returncode == 0 and result["rate"] == 16000
    assert np.load(tmp_path / "output.npy").shape == (16000, 2)


def test_missing_input_is_reported(tmp_path):
    done, result = run_job(
        tmp_path, {"action": "load", "path": str(tmp_path / "missing.wav")}
    )
    assert done.returncode != 0 and not result["ok"] and result["error"]


def test_silero_silence_no_false_speech(tmp_path):
    path = tmp_path / "silence.npy"
    np.save(path, np.zeros((32000, 2), dtype=np.float32))
    done, result = run_job(
        tmp_path,
        {
            "action": "detect",
            "input": str(path),
            "rate": 16000,
            "threshold": 0.5,
            "silence_ms": 350,
        },
    )
    assert result["ok"], result
    assert result["regions"] == []
