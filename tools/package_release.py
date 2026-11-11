"""Wrap a tested native compact bundle in EXE, AppImage or DMG."""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "release-native"


def run(arguments, **kwargs):
    subprocess.run([str(value) for value in arguments], check=True, cwd=ROOT, **kwargs)


def download_tool(name):
    spec = json.loads((ROOT / "packaging/tool-sources.json").read_text("utf-8"))[name]
    path = ROOT / "artifacts/packaging-tools" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        partial = path.with_suffix(".partial")
        with (
            urllib.request.urlopen(spec["url"], timeout=120) as response,
            partial.open("wb") as target,
        ):
            shutil.copyfileobj(response, target)
        partial.replace(path)
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != spec["sha256"]:
        raise RuntimeError(f"Packaging tool checksum mismatch: {name}")
    path.chmod(0o755)
    return path


def main():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))["project"][
        "version"
    ]
    OUTPUT.mkdir(exist_ok=True)
    if sys.platform == "win32":
        compiler = shutil.which("ISCC")
        if not compiler:
            base = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
            choices = sorted(base.glob("Inno Setup */ISCC.exe"))
            compiler = str(choices[-1]) if choices else None
        if not compiler:
            raise RuntimeError("Install Inno Setup 6 or later, or add ISCC to PATH")
        run(
            [
                compiler,
                f"/DAppVersion={version}",
                f"/DBundleDir={ROOT / 'dist-native/VoxLoom'}",
                ROOT / "packaging/VoxLoom-Compact.iss",
            ]
        )
        target = OUTPUT / f"VoxLoom-Studio-{version}-windows-x64.exe"
    elif sys.platform == "darwin":
        if platform.machine() != "arm64":
            raise RuntimeError("The macOS release targets Apple Silicon")
        target = OUTPUT / f"VoxLoom-Studio-{version}-macos-arm64.dmg"
        with tempfile.TemporaryDirectory(
            prefix="dmg-", dir=ROOT / "artifacts"
        ) as stage:
            stage = Path(stage)
            shutil.copytree(
                ROOT / "dist-native/VoxLoom.app", stage / "VoxLoom.app", symlinks=True
            )
            (stage / "Applications").symlink_to("/Applications")
            run(
                [
                    "hdiutil",
                    "create",
                    "-volname",
                    "VoxLoom Studio",
                    "-srcfolder",
                    stage,
                    "-format",
                    "UDZO",
                    "-fs",
                    "HFS+",
                    "-ov",
                    target,
                ]
            )
        run(["hdiutil", "verify", target])
    elif sys.platform == "linux":
        if platform.machine() not in ("x86_64", "AMD64"):
            raise RuntimeError("The Linux release targets x86_64")
        tool, runtime = download_tool("appimagetool"), download_tool("appimage-runtime")
        target = OUTPUT / f"VoxLoom-Studio-{version}-linux-x86_64.AppImage"
        with tempfile.TemporaryDirectory(
            prefix="appdir-", dir=ROOT / "artifacts"
        ) as temporary:
            appdir = Path(temporary) / "VoxLoom.AppDir"
            payload = appdir / "usr/lib/voxloom"
            shutil.copytree(ROOT / "dist-native/VoxLoom", payload, symlinks=True)
            shutil.copy2(ROOT / "assets/voxloom.png", appdir / "voxloom.png")
            (appdir / "voxloom.desktop").write_text(
                "[Desktop Entry]\nType=Application\nName=VoxLoom Studio\nExec=VoxLoom\nIcon=voxloom\nCategories=AudioVideo;Audio;\nTerminal=false\n",
                encoding="utf-8",
            )
            launcher = appdir / "AppRun"
            launcher.write_text(
                '#!/bin/sh\nAPPDIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"\nexec "$APPDIR/usr/lib/voxloom/VoxLoom" "$@"\n',
                encoding="utf-8",
            )
            launcher.chmod(0o755)
            run(
                [tool, "--runtime-file", runtime, "--comp", "zstd", appdir, target],
                env=dict(os.environ, ARCH="x86_64", APPIMAGE_EXTRACT_AND_RUN="1"),
            )
        target.chmod(0o755)
    else:
        raise RuntimeError(f"Unsupported build platform: {sys.platform}")
    if not target.is_file() or not 0 < target.stat().st_size < 2 * 1024**3:
        raise RuntimeError(f"Missing or oversized release asset: {target}")
    print(f"Release package: {target}", flush=True)


if __name__ == "__main__":
    main()
