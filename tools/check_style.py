"""Run the project's pinned Python formatting and static checks."""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fix", action="store_true", help="Apply safe fixes and formatting"
    )
    args = parser.parse_args()
    ruff = [sys.executable, "-m", "ruff"]
    if args.fix:
        # Formatting resolves layout diagnostics that the linter cannot fix.
        subprocess.run(ruff + ["format", "."], cwd=ROOT, check=True)
        subprocess.run(ruff + ["check", ".", "--fix"], cwd=ROOT, check=True)
        subprocess.run(ruff + ["format", "."], cwd=ROOT, check=True)
    subprocess.run(ruff + ["format", "--check", "."], cwd=ROOT, check=True)
    subprocess.run(ruff + ["check", "."], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
