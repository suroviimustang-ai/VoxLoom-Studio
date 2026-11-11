"""Create portable model ZIPs and a trusted catalog from prepared pinned weights."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = (
    "whisper-base",
    "whisper-small",
    "whisper-large-v3-turbo",
    "DeepFilterNet3",
    "flexsed",
)


def specifications():
    catalog = {}
    for name in MODELS:
        directory = ROOT / "models" / name
        files = {}
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or ".cache" in path.parts or path.suffix == ".log":
                continue
            with path.open("rb") as stream:
                checksum = hashlib.file_digest(stream, "sha256").hexdigest()
            files[path.relative_to(directory).as_posix()] = {
                "bytes": path.stat().st_size,
                "sha256": checksum,
            }
        if not files:
            raise RuntimeError(f"Missing prepared model: {name}")
        catalog[name] = {"files": files}
    return {"schema": 1, "models": catalog}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-catalog", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "release-native/models")
    args = parser.parse_args()
    actual = specifications()
    catalog_path = ROOT / "assets/model-catalog.json"
    if args.write_catalog:
        catalog_path.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print(f"Catalog written: {catalog_path}")
        return
    if actual != json.loads(catalog_path.read_text("utf-8")):
        raise RuntimeError("Prepared weights differ from the reviewed model catalog")
    args.output.mkdir(parents=True, exist_ok=True)
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text("utf-8")
    license_paths = [
        "licenses/Whisper/LICENSE",
        "licenses/DeepFilterNet/deepfilternet-0.5.6.dist-info/LICENSE",
        "licenses/FlexSED/LICENSE",
        "licenses/CLAP/APACHE-2.0.txt",
        "licenses/CLAP/UPSTREAM_CODE_LICENSE",
    ]
    license_texts = {name: (ROOT / name).read_text("utf-8") for name in license_paths}
    for name, model in actual["models"].items():
        target = args.output / f"VoxLoom-Models-{name}-v1.zip"
        temporary = target.with_suffix(".partial")
        with zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1
        ) as zf:
            zf.writestr(
                "pack.json",
                json.dumps(
                    {
                        "schema": 1,
                        "model": name,
                        "notices": notices,
                        "licenses": license_texts,
                    }
                ),
            )
            for relative in model["files"]:
                zf.write(ROOT / "models" / name / relative, relative)
        if temporary.stat().st_size >= 2 * 1024**3:
            raise RuntimeError(f"GitHub asset limit exceeded: {target.name}")
        temporary.replace(target)
        print(f"Model pack: {target.name} ({target.stat().st_size} bytes)", flush=True)


if __name__ == "__main__":
    main()
