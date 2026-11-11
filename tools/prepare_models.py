"""Build-time downloads only; installed applications never download weights."""

import argparse
import hashlib
import json
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--whisper", default="all", choices=["all", "base", "small", "large-v3-turbo"]
    )
    parser.add_argument("--deepfilter-cache", type=Path)
    args = parser.parse_args()
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    from huggingface_hub import snapshot_download

    sources = json.loads((ROOT / "model-sources.json").read_text(encoding="utf-8"))
    names = sources["whisper"] if args.whisper == "all" else [args.whisper]
    for name in names:
        spec = sources["whisper"][name]
        destination = ROOT / "models" / f"whisper-{name}"
        snapshot_download(
            spec["repository"],
            revision=spec["revision"],
            local_dir=destination,
            allow_patterns=[
                "model.bin",
                "config.json",
                "tokenizer.json",
                "vocabulary.*",
                "preprocessor_config.json",
            ],
        )
        with (destination / "model.bin").open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != spec["sha256"]:
                raise ValueError(f"Checksum mismatch: Whisper {name}")
        print(f"Whisper {name}: verified", flush=True)
    target = ROOT / "models/DeepFilterNet3"
    if args.deepfilter_cache:
        shutil.copytree(
            args.deepfilter_cache,
            target,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.log"),
        )
    if not (target / "checkpoints/model_120.ckpt.best").is_file():
        archive = ROOT / "artifacts/downloads/DeepFilterNet3.zip"
        archive.parent.mkdir(parents=True, exist_ok=True)
        temporary = archive.with_suffix(".partial")
        with (
            urllib.request.urlopen(
                sources["deepfilter"]["url"], timeout=90
            ) as response,
            temporary.open("wb") as out,
        ):
            shutil.copyfileobj(response, out)
        os.replace(temporary, archive)
        destination = (ROOT / "models").resolve()
        with zipfile.ZipFile(archive) as zf:
            for member in zf.infolist():
                if (
                    not (destination / member.filename)
                    .resolve()
                    .is_relative_to(destination)
                ):
                    raise ValueError("Unsafe path in model archive")
            zf.extractall(destination)
    if not (target / "config.ini").is_file():
        raise RuntimeError("DeepFilterNet3 configuration missing")
    for name, expected in sources["deepfilter"]["files"].items():
        with (target / name).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
                raise ValueError(f"Checksum mismatch: DeepFilterNet3/{name}")
    print("Offline models ready. FlexSED: run tools/prepare_flexsed.py.", flush=True)


if __name__ == "__main__":
    main()
