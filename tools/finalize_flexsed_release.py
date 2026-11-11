"""Record release evidence only after packaged tests and installer compilation."""

import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))["project"][
    "version"
]


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


smoke = read("artifacts/packaged-flexsed-smoke/release-smoke.json")
codecs = read("artifacts/packaged-worker-flexsed/report.json")
startup = read("artifacts/startup-check/report.json")
assert smoke["ok"] and codecs["ok"] and startup["ok"]
assert {"flexsed-offline-events", "flexsed-selection-to-asr"} <= set(smoke["checks"])
assert read("artifacts/qt-import-check.json") == []
assert {"all-whisper-models-bundled", "screen-sized-startup"} <= set(smoke["checks"])
assert "whisper-base-offline" in codecs["checks"]
installer = ROOT / f"release/VoxLoom-Studio-Setup-{VERSION}-Offline-win-x64.exe"
assert installer.is_file() and installer.stat().st_size > 1024**3
checkpoint = ROOT / "dist-flexsed/VoxLoom/_internal/models/flexsed/flexsed_as.pt"
assert (
    digest(checkpoint)
    == "5ec9a9b67ae3e612810ce150de06cd517ff7c8b1c640ba39a1422aa1e9040c32"
)
text_model = Path("models/flexsed/clap-text/model.safetensors")
assert digest(ROOT / text_model) == digest(
    ROOT / "dist-flexsed/VoxLoom/_internal" / text_model
)
whisper_models = {}
for name in ("base", "small", "large-v3-turbo"):
    relative = Path("models") / f"whisper-{name}" / "model.bin"
    expected = digest(ROOT / relative)
    assert expected == digest(ROOT / "dist-flexsed/VoxLoom/_internal" / relative)
    whisper_models[name] = expected
report = dict(
    version=VERSION + "-Offline",
    installer=installer.name,
    bytes=installer.stat().st_size,
    sha256=digest(installer),
    packaged_smoke=smoke,
    codecs_and_offline_asr=codecs,
    model_provenance=read("models/flexsed/manifest.json"),
    bundled_whisper_sha256=whisper_models,
    startup_display_checks=startup,
    limits=[
        "Tested on this Windows PC, not a clean VM.",
        "FlexSED event labels are unverified model predictions; no accuracy claim.",
    ],
)
(ROOT / "release/verification-flexsed.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(
    json.dumps(
        dict(installer=str(installer), bytes=report["bytes"], sha256=report["sha256"]),
        ensure_ascii=False,
    )
)
