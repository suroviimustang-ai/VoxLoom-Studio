"""Verify the packaged worker and bundled codecs/models without using source imports."""

import json
import os
import subprocess
import sys
from pathlib import Path

import av
import numpy as np
import soundfile as sf

root = Path(__file__).resolve().parents[1]
exe = (
    Path(sys.argv[1]).resolve()
    if len(sys.argv) > 1
    else root / "dist/VoxLoom/VoxLoom.exe"
)
destination = (
    root
    / "artifacts"
    / ("packaged-worker-flexsed" if len(sys.argv) > 1 else "packaged-worker-checks")
)
destination.mkdir(parents=True, exist_ok=True)
environment = dict(os.environ, HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
environment["PATH"] = str(Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32")
for name in ["PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "CONDA_PREFIX"]:
    environment.pop(name, None)
checks = []
fixtures = destination / "fixtures"
fixtures.mkdir(exist_ok=True)
rate = 48000
signal = (0.2 * np.sin(2 * np.pi * 440 * np.arange(rate) / rate)).astype(np.float32)
for extension in ["wav", "flac", "ogg"]:
    sf.write(fixtures / f"codec.{extension}", signal, rate)
for extension, codec in [("mp3", "libmp3lame"), ("m4a", "aac"), ("aac", "aac")]:
    with av.open(str(fixtures / f"codec.{extension}"), mode="w") as output:
        stream = output.add_stream(codec, rate=rate)
        stream.layout = "mono"
        frame = av.AudioFrame.from_ndarray(
            signal[None, :], format="fltp", layout="mono"
        )
        frame.sample_rate = rate
        for packet in stream.encode(frame):
            output.mux(packet)
        for packet in stream.encode(None):
            output.mux(packet)


def worker(name, request, data=None):
    folder = destination / name
    folder.mkdir(exist_ok=True)
    if data is not None:
        np.save(folder / "input.npy", data, allow_pickle=False)
        request["input"] = str(folder / "input.npy")
    path = folder / "request.json"
    path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
    completed = subprocess.run(
        [str(exe), "--worker", str(path)], cwd=folder, env=environment, timeout=300
    )
    response = json.loads((folder / "result.json").read_text(encoding="utf-8"))
    assert completed.returncode == 0 and response["ok"], response
    checks.append(name)
    print(name, "OK", flush=True)
    return response, np.load(folder / "output.npy") if (
        folder / "output.npy"
    ).exists() else None


for extension in ["mp3", "aac", "m4a", "wav", "flac", "ogg"]:
    fixture = fixtures / f"codec.{extension}"
    info, samples = worker(
        "decode-" + extension, dict(action="load", path=str(fixture))
    )
    assert np.isfinite(samples).all() and len(samples) > info["rate"] * 0.8

info, samples = worker(
    "spoken-fixture",
    dict(action="load", path=str(root / "artifacts/speech_fixture.wav")),
)
base, _ = worker(
    "whisper-base-offline",
    dict(action="transcribe", rate=info["rate"], model="base", language="en"),
    samples,
)
assert "speech" in base["text"].lower(), base
transcript, _ = worker(
    "whisper-turbo-offline",
    dict(action="transcribe", rate=info["rate"], model="large-v3-turbo", language="en"),
    samples,
)
assert "speech" in transcript["text"].lower(), transcript
report = dict(
    ok=True,
    checks=checks,
    turbo_transcript=transcript["text"],
    path=environment["PATH"],
    note="Workers use system-only PATH, no Python or virtual-environment variables, and offline models.",
)
(destination / "report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("Packaged worker checks passed", flush=True)
