"""Independent adapters; model inference runs only in the worker process."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage, signal

from .audio import resample, validate

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
    bundled = resource_root() / "models" / name
    return bundled if bundled.is_dir() else writable_models() / name


def writable_models() -> Path:
    if not getattr(sys, "frozen", False):
        return resource_root() / "models"
    if sys.platform == "win32":
        return (
            Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
            / "VoxLoom"
            / "models"
        )
    if sys.platform == "darwin":
        return Path.home() / "Library/Caches/VoxLoom/models"
    return (
        Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
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
        return data.copy(), "Тишина: усиление не применено."
    if mode == "peak":
        gain = min(10 ** (target / 20) / peak, 10 ** (24 / 20))
        result = data * gain
        note = f"Пиковая нормировка: усиление {20 * np.log10(gain):+.1f} dB (максимум +24 dB)."
    elif mode == "lufs":
        import pyloudnorm as pyln

        if len(data) < rate * 0.4:
            raise ValueError(
                "Для LUFS нужен фрагмент не короче 0.4 с. Используйте пиковую нормировку."
            )
        if data.shape[1] > 5:
            raise ValueError(
                "LUFS поддерживает до 5 каналов; используйте пиковую нормировку."
            )
        measured = pyln.Meter(rate).integrated_loudness(data)
        if not np.isfinite(measured):
            return (
                data.copy(),
                "Уровень ниже порога измерения LUFS; усиление не применено.",
            )
        gain_db = np.clip(target - measured, -24, 24)
        result = data * 10 ** (gain_db / 20)
        result = linked_limiter(result, rate)
        actual = pyln.Meter(rate).integrated_loudness(result)
        note = f"LUFS: {measured:.1f} → {actual:.1f}; цель {target:.1f}. Лимитер: −1 dBFS (sample peak)."
    else:
        raise ValueError("Неизвестный режим нормировки.")
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
        raise ValueError("Степень очистки должна быть от 0 до 1.")
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
                "Нет модели DeepFilterNet3 в папке models. Выполните подготовку моделей."
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
        raise ValueError(f"Неизвестный метод: {method}")
    result = validate(result, rate)
    if result.shape != data.shape:
        raise RuntimeError("Модель изменила длину дорожки; результат отклонён.")
    return linked_limiter(result, rate)
