"""Build for the host OS. Cross-compilation is deliberately unsupported."""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    commands = [[sys.executable, "tools/doctor.py", "--models"]]
    if not args.skip_tests:
        commands += [
            [sys.executable, "-m", "pytest", "-q"],
            [sys.executable, "tools/check_startup.py"],
        ]
    commands += [
        [sys.executable, "tools/collect_licenses.py"],
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "VoxLoom.spec",
            "--noconfirm",
            "--distpath",
            "dist-native",
            "--workpath",
            "build-native",
        ],
    ]
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)
    if sys.platform == "darwin":
        target = ROOT / "dist-native/VoxLoom.app"
    else:
        target = (
            ROOT
            / "dist-native/VoxLoom"
            / ("VoxLoom.exe" if sys.platform == "win32" else "VoxLoom")
        )
    print(
        f"Native bundle: {target}\nKeep the entire bundle directory, not just its executable."
    )


if __name__ == "__main__":
    main()
