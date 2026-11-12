"""Independent adapters; model inference runs only in the worker process."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage, signal

from .audio import resample, validate
from .i18n import tr

WHISPER_MODELS = ("base", "small", "large-v3-turbo")
WHISPER_FILES = ("model.bin", "config.json", "tokenizer.json")


def whisper_ready(name: str) -> bool:
    directory = model_directory(f"whisper-{name}")
    return (
        name in WHISPER_MODELS
        and all((directory / filename).is_file() for filename in WHISPER_FILES)
        and any(
            (directory / filename).is_file()
            for filename in ("vocabulary.txt", "vocabulary.json")
        )
    )


def resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def model_directory(name: str) -> Path:
    from .modelpacks import installed_directory

    installed = installed_directory(writable_models(), name)
    if installed is not None:
        return installed
    bundled = resource_root() / "models" / name
    return bundled if bundled.is_dir() else writable_models() / name


def writable_models() -> Path:
    override = os.environ.get("VOXLOOM_MODEL_HOME")
    if override:
        path = Path(override).expanduser()
        if not path.is_absolute():
            raise ValueError(tr("VOXLOOM_MODEL_HOME must be an absolute path"))
        return path
    if not getattr(sys, "frozen", False):
        return resource_root() / "models"
    if sys.platform == "win32":
        return (
            Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
            / "VoxLoom"
            / "models"
        )
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/VoxLoom/models"
    return (
        Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
        / "voxloom/models"
    )


def linked_limiter(data: np.ndarray, rate: int, ceiling_db: float = -1.0) -> np.ndarray:
    """Sample peak limiter adapted from SpeechCleaner; channels share one gain."""
    ceiling = 10 ** (ceiling_db / 20)
    peak = np.max(np.abs(data), axis=1)
    if np.max(peak) <= ceiling:
        return data.copy()
    size = min(max(1, round(rate * 0.005)), len(data))
    envelope = ndimage.maximum_filter1d(peak, size=size, origin=-(size // 2))
    instant = np.minimum(1, ceiling / np.maximum(envelope, 1e-12))
    coefficient = np.exp(-1 / (rate * 0.06))
    b, a = [1 - coefficient], [1, -coefficient]
    release, _ = signal.lfilter(b, a, instant, zi=signal.lfilter_zi(b, a) * instant[0])
    return (data * np.minimum(instant, release)[:, None]).astype(np.float32)


def normalize(
    data: np.ndarray, rate: int, mode: str, target: float
) -> tuple[np.ndarray, str]:
    peak = float(np.max(np.abs(data)))
    if peak < 1e-9:
        return data.copy(), tr("Silence: no gain applied.")
    if mode == "peak":
        gain = min(10 ** (target / 20) / peak, 10 ** (24 / 20))
        result = data * gain
        note = tr(
            "Peak normalization: {v0:+.1f} dB gain (maximum +24 dB).",
            v0=20 * np.log10(gain),
        )
    elif mode == "lufs":
        import pyloudnorm as pyln

        if len(data) < rate * 0.4:
            raise ValueError(
                tr(
                    "LUFS requires at least 0.4 seconds. Use peak normalization for shorter selections."
                )
            )
        if data.shape[1] > 5:
            raise ValueError(
                tr(
                    "LUFS supports up to 5 channels; use peak normalization for more channels."
                )
            )
        measured = pyln.Meter(rate).integrated_loudness(data)
        if not np.isfinite(measured):
            return (
                data.copy(),
                tr(
                    "The level is below the LUFS measurement threshold; no gain applied."
                ),
            )
        gain_db = np.clip(target - measured, -24, 24)
        result = data * 10 ** (gain_db / 20)
        result = linked_limiter(result, rate)
        actual = pyln.Meter(rate).integrated_loudness(result)
        note = tr(
            "LUFS: {v0:.1f} → {v1:.1f}; target {v2:.1f}. Limiter: −1 dBFS (sample peak).",
            v0=measured,
            v1=actual,
            v2=target,
        )
    else:
        raise ValueError(tr("Unknown normalization mode."))
    return result.astype(np.float32), note


def denoise(
    data: np.ndarray,
    rate: int,
    method: str,
    strength: float = 0.8,
    noise: np.ndarray | None = None,
) -> np.ndarray:
    data = validate(data, rate)
    if not 0 <= strength <= 1:
        raise ValueError(tr("Cleanup strength must be between 0 and 1."))
    if method == "spectral":
        import noisereduce as nr

        result = nr.reduce_noise(
            y=data.T,
            sr=rate,
            stationary=noise is not None,
            y_noise=None if noise is None else noise.T,
            prop_decrease=strength,
            n_fft=1024,
            n_jobs=1,
        ).T
    elif method == "dsp":
        sos = signal.butter(2, 70, "highpass", fs=rate, output="sos")
        result = (
            signal.sosfiltfilt(sos, data, axis=0) if len(data) > 16 else data.copy()
        )
        for freq in range(50, 301, 50):
            b, a = signal.iirnotch(freq, 30, fs=rate)
            if len(data) > 12:
                result = signal.filtfilt(b, a, result, axis=0)
        result = strength * result + (1 - strength) * data
    elif method == "rnnoise":
        from .rnnoise_native import process

        channels = []
        for channel in data.T:
            x = resample(channel, rate, 48000)
            # RNNoise uses 480-sample frames and one-frame algorithmic delay.
            delay = 480
            padded = np.pad(x, (0, delay + (-len(x) % 480)))
            y = process(padded)
            y = y[delay : delay + len(x)]
            y = resample(y, 48000, rate)
            channels.append(np.pad(y, (0, max(0, len(data) - len(y))))[: len(data)])
        result = np.column_stack(channels) * strength + data * (1 - strength)
    elif method == "deepfilter":
        import torch
        from df.enhance import enhance, init_df

        directory = model_directory("DeepFilterNet3")
        if not (directory / "config.ini").is_file():
            raise RuntimeError(
                tr(
                    "DeepFilterNet3 is missing. Install its pack via Models → Install pack."
                )
            )
        torch.set_num_threads(2)
        model, state, _ = init_df(
            model_base_dir=str(directory), log_file=None, log_level="ERROR"
        )
        channels = []
        for channel in data.T:
            x = resample(channel, rate, state.sr())
            # Bound neural activations for long recordings. Context is discarded
            # so every output sample keeps its original timeline coordinate.
            y = np.empty_like(x)
            block, context = 24 * state.sr(), state.sr()
            for start in range(0, len(x), block):
                end = min(len(x), start + block)
                left, right = max(0, start - context), min(len(x), end + context)
                with torch.inference_mode():
                    enhanced = (
                        enhance(
                            model,
                            state,
                            torch.from_numpy(x[left:right].copy())[None, :],
                            pad=True,
                        )
                        .cpu()
                        .numpy()[0]
                    )
                y[start:end] = enhanced[start - left : end - left]
            y = resample(y, state.sr(), rate)
            channels.append(np.pad(y, (0, max(0, len(data) - len(y))))[: len(data)])
        result = np.column_stack(channels) * strength + data * (1 - strength)
    else:
        raise ValueError(tr("Unknown method: {v0}", v0=method))
    result = validate(result, rate)
    if result.shape != data.shape:
        raise RuntimeError(
            tr("The model changed the track length; the result was rejected.")
        )
    return linked_limiter(result, rate)
