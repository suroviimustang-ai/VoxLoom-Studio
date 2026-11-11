"""Use the same isolated environment for all subsequent GitHub Actions steps."""

import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
environment = root / ".venv-ci"
binary = environment / ("Scripts" if sys.platform == "win32" else "bin")
python = binary / ("python.exe" if sys.platform == "win32" else "python")
subprocess.run([str(python), str(root / "tools/install_dependencies.py")], check=True)
with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as stream:
    stream.write(str(binary) + "\n")
with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as stream:
    stream.write("VIRTUAL_ENV=" + str(environment) + "\n")
