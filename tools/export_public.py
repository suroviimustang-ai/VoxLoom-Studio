"""Create a new, allowlisted source tree. Never export the working directory wholesale."""

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP = (
    ".editorconfig",
    ".gitattributes",
    "PSScriptAnalyzerSettings.psd1",
    "requirements-dev.txt",
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    ".gitignore",
    "pyproject.toml",
    "requirements.txt",
    "requirements-neural.txt",
    "requirements-flexsed.txt",
    "requirements-lock.txt",
    "model-sources.json",
    "main.py",
    "run.ps1",
    "build.ps1",
    "build-flexsed.ps1",
    "VoxLoom.spec",
)
TOOLS = (
    "check_style.py",
    "check_powershell.ps1",
    "prepare_models.py",
    "prepare_flexsed.py",
    "prepare_assets.py",
    "prepare_speech_fixture.ps1",
    "collect_licenses.py",
    "check_qt_imports.py",
    "verify_release.py",
    "finalize_flexsed_release.py",
    "check_startup.py",
    "recipe_chain_dsp.py",
    "export_public.py",
    "install_dependencies.py",
    "ci_install.py",
    "doctor.py",
    "build_portable.py",
    "build_model_packs.py",
    "package_release.py",
    "prepare_speech_fixture.py",
    "verify_native_bundle.py",
    "check_package.py",
    "release_assets.py",
    "windows_runtime.py",
)
DOCS = (
    "ARCHITECTURE.md",
    "RELEASING.md",
    "LICENSES.md",
    "BUILDING.md",
    "CODING_STANDARDS.md",
    "PUBLISHING.md",
    "DOWNLOADS.md",
    "MODULES.md",
    "RELEASE_NOTES.md",
)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def export(destination):
    destination.mkdir(parents=True, exist_ok=False)
    paths = [ROOT / name for name in TOP]
    paths += [ROOT / "tools" / name for name in TOOLS]
    paths += [ROOT / "docs" / name for name in DOCS]
    paths += [ROOT / "packaging/VoxLoom-FlexSED.iss"]
    paths += [
        ROOT / "packaging/VoxLoom-Compact.iss",
        ROOT / "packaging/tool-sources.json",
    ]
    for folder in ("voxloom", "tests", "assets", "licenses", ".github"):
        paths += [
            p
            for p in (ROOT / folder).rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and p.suffix not in (".pyc", ".log")
        ]
    manifest = []
    for source in sorted(set(paths)):
        relative = source.relative_to(ROOT)
        if source.suffix.lower() in (
            ".wav",
            ".flac",
            ".mp3",
            ".ogg",
            ".aac",
            ".m4a",
            ".srt",
            ".pt",
            ".pth",
            ".npy",
            ".npz",
            ".bin",
            ".safetensors",
        ):
            raise ValueError(f"Private/binary data in public source list: {relative}")
        if source.stat().st_size >= 95 * 1024**2:
            raise ValueError(f"File too large for public sources: {relative}")
        if source.suffix not in (".png", ".ico", ".icns"):
            content = source.read_text(encoding="utf-8-sig", errors="replace")
            # Literal local-user paths and likely credential formats, not generic examples.
            if re.search(
                r"(?i)[a-z]:[/\\]Users[/\\]sever|gh[pousr]_[A-Za-z0-9]{30,}|hf_[A-Za-z0-9]{30,}",
                content,
            ):
                raise ValueError(f"Potential private information: {relative}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        manifest.append(
            dict(
                path=relative.as_posix(),
                bytes=target.stat().st_size,
                sha256=digest(target),
            )
        )
    (destination / "SOURCE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    archive = destination.parent / (destination.name + ".zip")
    with zipfile.ZipFile(
        archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as zf:
        for path in sorted(destination.rglob("*")):
            if path.is_file():
                zf.write(
                    path, str(Path(destination.name) / path.relative_to(destination))
                )
    print(
        json.dumps(
            dict(
                source_tree=str(destination),
                archive=str(archive),
                files=len(manifest),
                bytes=archive.stat().st_size,
                sha256=digest(archive),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--destination", type=Path, default=ROOT / "public-export/VoxLoom-Studio"
    )
    export(parser.parse_args().destination.resolve())
