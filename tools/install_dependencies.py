"""Install native CPU dependencies into the active virtual environment."""

import argparse
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def commands(system=None, machine=None):
    system = system or platform.system()
    machine = machine or platform.machine()
    if system not in ("Windows", "Darwin", "Linux"):
        raise RuntimeError(f"Unsupported OS: {system}")
    if system == "Darwin" and machine.lower() not in ("arm64", "aarch64"):
        raise RuntimeError(
            "This dependency set targets Apple Silicon. PyTorch 2.8 has no macOS Intel wheels. Intel Macs require a separately validated runtime; do not mix ARM64 and x86_64 Python."
        )
    pip = [sys.executable, "-m", "pip"]
    torch = pip + ["install", "torch==2.8.0", "torchaudio==2.8.0"]
    if system in ("Windows", "Linux"):
        torch += ["--index-url", "https://download.pytorch.org/whl/cpu"]
    return [
        pip + ["install", "--upgrade", "pip"],
        torch,
        pip
        + [
            "install",
            "-r",
            str(ROOT / "requirements.txt"),
            "-r",
            str(ROOT / "requirements-neural.txt"),
            "-r",
            str(ROOT / "requirements-flexsed.txt"),
        ],
        pip + ["check"],
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if sys.prefix == sys.base_prefix and not args.dry_run:
        raise SystemExit("Create and activate a Python 3.11 virtual environment first.")
    if sys.version_info[:2] != (3, 11):
        raise SystemExit("Use Python 3.11 for the documented dependency set.")
    for command in commands():
        print(" ".join(command), flush=True)
        if not args.dry_run:
            subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
