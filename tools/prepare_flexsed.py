"""Fetch pinned upstream inference code and verified public model files."""

import hashlib
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REVISION = "89aac3351e807de57c4fe3148d982922a3318e46"
MODEL_REVISION = "eefe52b7ad686a9bc9f1f5dd0803e2c52171e128"
CLAP_REVISION = "8fa0f1c6d0433df6e97c127f64b2a1d6c0dcda8a"


def fetch(url, path, sha256=None):
    path.parent.mkdir(parents=True, exist_ok=True)

    def digest(file):
        with file.open("rb") as handle:
            return hashlib.file_digest(handle, "sha256").hexdigest()

    if path.is_file() and (not sha256 or digest(path) == sha256):
        return
    temporary = path.with_suffix(path.suffix + ".partial")
    print(f"Downloading {path.name}", flush=True)
    with (
        urllib.request.urlopen(url, timeout=90) as response,
        temporary.open("wb") as output,
    ):
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    if sha256 and digest(temporary) != sha256:
        raise ValueError(f"Checksum mismatch: {path}")
    os.replace(temporary, path)


def main():
    vendor = ROOT / "voxloom" / "_vendor" / "flexsed"
    vendor.mkdir(parents=True, exist_ok=True)
    for parent in (vendor, vendor.parent):
        (parent / "__init__.py").touch()
    base = f"https://raw.githubusercontent.com/JHU-LCAP/FlexSED/{REVISION}/"
    for name in ("dasheng.py", "transformer.py", "sed_decoder.py"):
        fetch(base + "src/models/" + name, vendor / name)
    fetch(base + "LICENSE", ROOT / "licenses" / "FlexSED" / "LICENSE")
    model = ROOT / "models" / "flexsed"
    fetch(
        f"https://huggingface.co/Higobeatz/FlexSED/resolve/{MODEL_REVISION}/ckpts/flexsed_as.pt",
        model / "flexsed_as.pt",
        "5ec9a9b67ae3e612810ce150de06cd517ff7c8b1c640ba39a1422aa1e9040c32",
    )
    clap = ROOT / "artifacts" / "clap-original"
    base = f"https://huggingface.co/laion/clap-htsat-unfused/resolve/{CLAP_REVISION}/"
    for name in (
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.json",
        "merges.txt",
        "README.md",
    ):
        fetch(base + name, clap / name)
    fetch(
        base + "pytorch_model.bin",
        clap / "pytorch_model.bin",
        "1cd3c601bc4afe0fa87be3de4c13dd2cfadd249fac1e29acf74a9b296c3219bb",
    )
    from transformers import ClapTextModelWithProjection, RobertaTokenizerFast

    encoder = ClapTextModelWithProjection.from_pretrained(
        str(clap), local_files_only=True
    )
    encoder.save_pretrained(model / "clap-text", safe_serialization=True)
    RobertaTokenizerFast.from_pretrained(
        str(clap), local_files_only=True
    ).save_pretrained(model / "clap-text")
    manifest = dict(
        upstream=REVISION,
        checkpoint=MODEL_REVISION,
        clap=CLAP_REVISION,
        checkpoint_sha256="5ec9a9b67ae3e612810ce150de06cd517ff7c8b1c640ba39a1422aa1e9040c32",
    )
    (model / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (ROOT / "licenses" / "FlexSED" / "provenance.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    notice = ROOT / "licenses" / "CLAP"
    notice.mkdir(parents=True, exist_ok=True)
    shutil.copy2(clap / "README.md", notice / "README.md")
    fetch(
        "https://raw.githubusercontent.com/LAION-AI/CLAP/main/LICENSE",
        notice / "UPSTREAM_CODE_LICENSE",
    )
    fetch("https://www.apache.org/licenses/LICENSE-2.0.txt", notice / "APACHE-2.0.txt")
    print("FlexSED and CLAP text encoder ready for offline inference", flush=True)


if __name__ == "__main__":
    main()
