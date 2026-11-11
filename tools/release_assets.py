"""Publish only verified assets from one source commit to a draft GitHub release."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))["project"][
    "version"
]
TAG = "v" + VERSION
PLATFORMS = {"win32": "windows-x64", "darwin": "macos-arm64", "linux": "linux-x86_64"}


def gh(*args, capture=False):
    return subprocess.run(
        ["gh", *map(str, args)],
        cwd=ROOT,
        check=True,
        capture_output=capture,
        text=True,
        encoding="utf-8",
    ).stdout


def release():
    return json.loads(
        gh(
            "api",
            f"repos/{os.environ['GITHUB_REPOSITORY']}/releases/tags/{TAG}",
            capture=True,
        )
    )


def file_info(path):
    if not 0 < path.stat().st_size < 2 * 1024**3:
        raise RuntimeError(f"Invalid asset size: {path}")
    with path.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"name": path.name, "sha256": checksum, "bytes": path.stat().st_size}


def upload_report(name, files, checks):
    report = {
        "source_sha": os.environ["GITHUB_SHA"],
        "version": VERSION,
        "assets": [file_info(p) for p in files],
        "checks": checks,
    }
    path = ROOT / "release-native" / name
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    gh("release", "upload", TAG, *files, path, "--clobber")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=["init", "upload-models", "download-models", "upload-app", "publish"],
    )
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError(
            "This publisher is restricted to the repository's GitHub Actions workflow"
        )
    if args.action == "init":
        result = subprocess.run(
            ["gh", "release", "view", TAG, "--json", "isDraft"],
            capture_output=True,
            text=True,
        )
        options = [
            "--target",
            os.environ["GITHUB_SHA"],
            "--title",
            f"VoxLoom Studio {VERSION}",
            "--notes-file",
            "docs/RELEASE_NOTES.md",
        ]
        if result.returncode == 0:
            if not json.loads(result.stdout)["isDraft"]:
                raise RuntimeError(
                    "This version is already published; bump the version instead of overwriting it"
                )
            gh("release", "edit", TAG, *options)
        else:
            gh("release", "create", TAG, "--draft", "--prerelease", *options)
        return
    current = release()
    if not current["draft"] or current["target_commitish"] != os.environ["GITHUB_SHA"]:
        raise RuntimeError("Release must be a draft for this exact source commit")
    if args.action == "download-models":
        destination = ROOT / "artifacts/model-packs"
        destination.mkdir(parents=True, exist_ok=True)
        gh(
            "release",
            "download",
            TAG,
            "--pattern",
            "VoxLoom-Models-*.zip",
            "--dir",
            destination,
        )
    elif args.action == "upload-models":
        files = sorted((ROOT / "release-native/models").glob("VoxLoom-Models-*.zip"))
        if len(files) != 5:
            raise RuntimeError("All five model packs are required")
        source = ROOT / f"release-native/VoxLoom-Studio-{VERSION}-source.zip"
        subprocess.run(
            [
                "git",
                "archive",
                "--format=zip",
                f"--prefix=VoxLoom-Studio-{VERSION}/",
                "-o",
                str(source),
                os.environ["GITHUB_SHA"],
            ],
            check=True,
            cwd=ROOT,
        )
        upload_report("model-packs.json", [*files, source], ["trusted-catalog-match"])
    elif args.action == "upload-app":
        name = PLATFORMS[sys.platform]
        suffix = {"win32": ".exe", "darwin": ".dmg", "linux": ".AppImage"}[sys.platform]
        file = ROOT / f"release-native/VoxLoom-Studio-{VERSION}-{name}{suffix}"
        checks = []
        for path in (
            "artifacts/native-verification/release-smoke.json",
            "artifacts/package-verification/report.json",
        ):
            report = json.loads((ROOT / path).read_text("utf-8"))
            if not report.get("ok"):
                raise RuntimeError(f"Missing successful validation: {path}")
            checks.extend(report["checks"])
        worker_report = json.loads(
            (ROOT / "artifacts/packaged-worker-flexsed/report.json").read_text("utf-8")
        )
        if not worker_report.get("ok"):
            raise RuntimeError("Packaged worker verification failed")
        checks.extend(worker_report["checks"])
        upload_report(f"build-{name}.json", [file], checks)
    else:
        destination = ROOT / "artifacts/publish-reports"
        destination.mkdir(parents=True, exist_ok=True)
        for name in [
            "model-packs.json",
            *[f"build-{p}.json" for p in PLATFORMS.values()],
        ]:
            gh("release", "download", TAG, "--pattern", name, "--dir", destination)
        assets = {item["name"]: item for item in current["assets"]}
        lines = []
        for path in destination.glob("*.json"):
            report = json.loads(path.read_text("utf-8"))
            if report["source_sha"] != os.environ["GITHUB_SHA"]:
                raise RuntimeError("Mixed build commits; refusing publication")
            for item in report["assets"]:
                remote = assets[item["name"]]
                if (
                    remote["size"] != item["bytes"]
                    or remote.get("digest") != "sha256:" + item["sha256"]
                ):
                    raise RuntimeError(f"Uploaded checksum mismatch: {item['name']}")
                lines.append(f"{item['sha256']}  {item['name']}")
        checksums = destination / "SHA256SUMS.txt"
        checksums.write_text("\n".join(sorted(lines)) + "\n", encoding="utf-8")
        gh("release", "upload", TAG, checksums, "--clobber")
        gh("release", "edit", TAG, "--draft=false", "--prerelease")


if __name__ == "__main__":
    main()
