"""Exercise compact model installation, GUI workers and offline recognition."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packs", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform == "darwin":
        executable = ROOT / "dist-native/VoxLoom.app/Contents/MacOS/VoxLoom"
    else:
        executable = (
            ROOT
            / "dist-native/VoxLoom"
            / ("VoxLoom.exe" if sys.platform == "win32" else "VoxLoom")
        )
    folder = ROOT / "artifacts/native-verification"
    folder.mkdir(parents=True, exist_ok=True)
    models = ROOT / "artifacts/installed-models"
    environment = dict(
        os.environ,
        VOXLOOM_MODEL_HOME=str(models),
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        QT_QPA_PLATFORM="offscreen",
    )
    packs = sorted(args.packs.glob("VoxLoom-Models-*.zip"))
    if len(packs) != 5:
        raise RuntimeError("Expected all five verified model packs")
    request = folder / "request.json"
    request.write_text(
        json.dumps(
            {"action": "install_models", "paths": [str(p.resolve()) for p in packs]}
        ),
        encoding="utf-8",
    )
    subprocess.run(
        [str(executable), "--worker", str(request)],
        check=True,
        env=environment,
        timeout=1200,
    )
    result = json.loads((folder / "result.json").read_text("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(result)
    subprocess.run(
        [
            str(executable),
            "--smoke-test",
            str(ROOT / "artifacts/speech_fixture.wav"),
            str(folder),
        ],
        check=True,
        env=environment,
        timeout=1800,
    )
    report = json.loads((folder / "release-smoke.json").read_text("utf-8"))
    if not report.get("ok") or "flexsed-offline-events" not in report["checks"]:
        raise RuntimeError(report)
    subprocess.run(
        [sys.executable, "tools/verify_release.py", str(executable)],
        cwd=ROOT,
        check=True,
        env=environment,
        timeout=1200,
    )
    print(
        "Compact bundle and all separate model packs passed offline checks.", flush=True
    )


if __name__ == "__main__":
    main()
