"""Generate a non-private spoken fixture using the host's speech synthesizer."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = "This is a test recording for speech restoration. The original audio must remain unchanged. We can find speech, remove background noise, and transcribe the selected fragment."


def main():
    target = ROOT / "artifacts/speech_fixture.wav"
    target.parent.mkdir(exist_ok=True)
    if target.exists():
        return
    if sys.platform == "win32":
        command = [
            "powershell",
            "-NoProfile",
            "-File",
            str(ROOT / "tools/prepare_speech_fixture.ps1"),
        ]
    elif sys.platform == "darwin":
        command = [
            "say",
            "-v",
            "Samantha",
            "-o",
            str(target),
            "--file-format=WAVE",
            "--data-format=LEI16@22050",
            TEXT,
        ]
    else:
        command = ["espeak-ng", "-v", "en-us", "-s", "145", "-w", str(target), TEXT]
    subprocess.run(command, check=True)
    if not target.is_file():
        raise RuntimeError("Speech synthesis did not produce a fixture")


if __name__ == "__main__":
    main()
