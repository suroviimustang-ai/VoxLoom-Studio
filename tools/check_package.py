"""Verify a freshly installed or mounted distribution, not just its build folder."""

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))["project"][
        "version"
    ]
    folder = ROOT / "artifacts/package-verification"
    folder.mkdir(parents=True, exist_ok=True)
    mount = None
    environment = dict(
        os.environ,
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        VOXLOOM_MODEL_HOME=str(ROOT / "artifacts/installed-models"),
        QT_QPA_PLATFORM="offscreen",
    )
    if sys.platform == "win32":
        if os.environ.get("GITHUB_ACTIONS") != "true":
            raise RuntimeError(
                "Silent installer verification runs only in disposable GitHub Actions VMs"
            )
        installer = ROOT / f"release-native/VoxLoom-Studio-{version}-windows-x64.exe"
        install = folder / "installed"
        subprocess.run(
            [
                str(installer),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                "/SP-",
                f"/DIR={install}",
            ],
            check=True,
            timeout=600,
        )
        executable = install / "VoxLoom.exe"
    elif sys.platform == "darwin":
        mount = folder / "mounted"
        mount.mkdir(exist_ok=True)
        image = ROOT / f"release-native/VoxLoom-Studio-{version}-macos-arm64.dmg"
        subprocess.run(
            [
                "hdiutil",
                "attach",
                "-readonly",
                "-nobrowse",
                "-mountpoint",
                str(mount),
                str(image),
            ],
            check=True,
            timeout=120,
        )
        executable = mount / "VoxLoom.app/Contents/MacOS/VoxLoom"
    else:
        executable = (
            ROOT / f"release-native/VoxLoom-Studio-{version}-linux-x86_64.AppImage"
        )
        environment["APPIMAGE_EXTRACT_AND_RUN"] = "1"
    try:
        request = folder / "request.json"
        request.write_text(
            json.dumps(
                {"action": "load", "path": str(ROOT / "artifacts/speech_fixture.wav")}
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [str(executable), "--worker", str(request)],
            env=environment,
            check=True,
            timeout=180,
        )
        result = json.loads((folder / "result.json").read_text("utf-8"))
        if not result.get("ok"):
            raise RuntimeError(result)
        request.write_text(
            json.dumps(
                {
                    "action": "transcribe",
                    "input": str(folder / "output.npy"),
                    "rate": result["rate"],
                    "model": "base",
                    "language": "en",
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [str(executable), "--worker", str(request)],
            env=environment,
            check=True,
            timeout=300,
        )
        transcript = json.loads((folder / "result.json").read_text("utf-8"))
        if (
            not transcript.get("ok")
            or "speech" not in transcript.get("text", "").lower()
        ):
            raise RuntimeError(transcript)
        (folder / "report.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "checks": [
                        "distribution-decode",
                        "distribution-whisper-base-offline",
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    finally:
        if mount is not None:
            subprocess.run(["hdiutil", "detach", str(mount)], check=True, timeout=120)


if __name__ == "__main__":
    main()
