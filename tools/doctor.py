"""Check native imports in separate processes so a bad DLL cannot hide later checks."""

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "Qt": "from PyQt6 import QtCore, QtGui, QtWidgets",
    "Audio codecs": "import av, soundfile, sounddevice",
    "Whisper / VAD": "import faster_whisper, ctranslate2, onnxruntime",
    "DeepFilterNet": "import torch, torchaudio, libdf; from df.enhance import init_df",
    "CLAP": "from transformers import ClapTextModelWithProjection, RobertaTokenizerFast",
    "RNNoise": "import numpy as np; from voxloom.rnnoise_native import process; process(np.zeros(480, np.float32))",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", action="store_true")
    args = parser.parse_args()
    reports = []
    for name, code in CHECKS.items():
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=90,
            )
            reports.append(
                dict(
                    component=name,
                    ok=result.returncode == 0,
                    error=result.stderr[-1500:] if result.returncode else "",
                )
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            reports.append(dict(component=name, ok=False, error=str(exc)))
        print(name, "OK" if reports[-1]["ok"] else "FAILED", flush=True)
    if args.models:
        sys.path.insert(0, str(ROOT))
        from voxloom.events import available
        from voxloom.processing import WHISPER_MODELS, model_directory, whisper_ready

        reports += [
            dict(component="Whisper " + name, ok=whisper_ready(name))
            for name in WHISPER_MODELS
        ]
        reports += [
            dict(component="FlexSED files", ok=available()),
            dict(
                component="DeepFilterNet3 files",
                ok=(
                    model_directory("DeepFilterNet3")
                    / "checkpoints/model_120.ckpt.best"
                ).is_file(),
            ),
        ]
    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    report = dict(
        ok=all(item["ok"] for item in reports),
        platform=platform.system(),
        architecture=platform.machine(),
        python=platform.python_version(),
        checks=reports,
    )
    (output / "doctor.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not report["ok"]:
        print(json.dumps(report, indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
