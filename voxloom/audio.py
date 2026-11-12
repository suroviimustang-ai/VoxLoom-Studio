"""Audio contracts: float32 [samples, channels], immutable source, sample bounds."""

from __future__ import annotations

import math
import os
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from .i18n import tr

MAX_DECODE_BYTES = 1536 * 1024**2


def validate(data: np.ndarray, rate: int) -> np.ndarray:
    data = np.asarray(data, dtype=np.float32)
    if data.ndim == 1:
        data = data[:, None]
    if data.ndim != 2 or not len(data) or not 1 <= data.shape[1] <= 8:
        raise ValueError(tr("A non-empty recording with 1–8 channels is required."))
    if not 8000 <= rate <= 384000 or not np.isfinite(data).all():
        raise ValueError(tr("Invalid sample rate or audio values."))
    return np.ascontiguousarray(data)


def load_audio(path: str) -> tuple[np.ndarray, int]:
    # libsndfile preserves Vorbis granule positions/sample counts that FFmpeg
    # may trim at the opening packet; prefer it for formats it decodes.
    try:
        handle = sf.SoundFile(path)
    except (sf.LibsndfileError, OSError):
        handle = None
    if handle is not None:
        with handle:
            if not 1 <= handle.channels <= 8 or not 8000 <= handle.samplerate <= 384000:
                raise ValueError(tr("Supported: 1–8 channels, 8–384 kHz sample rate."))
            if handle.frames * handle.channels * 4 > MAX_DECODE_BYTES:
                raise ValueError(
                    tr(
                        "This recording exceeds the 1.5 GB decoded PCM limit. Split the file first."
                    )
                )
            rate = handle.samplerate
            return validate(handle.read(dtype="float32", always_2d=True), rate), rate
    import av

    blocks, total = [], 0
    with av.open(path) as container:
        if not container.streams.audio:
            raise ValueError(tr("The file has no audio track."))
        stream = container.streams.audio[0]
        rate = stream.codec_context.sample_rate
        channels = stream.codec_context.channels
        if not rate or not 1 <= channels <= 8:
            raise ValueError(tr("Between 1 and 8 channels are supported."))
        resampler = av.AudioResampler(
            format="fltp", layout=stream.codec_context.layout, rate=rate
        )
        for frame in container.decode(stream):
            for converted in resampler.resample(frame):
                block = converted.to_ndarray().T.copy()
                total += block.nbytes
                if total > MAX_DECODE_BYTES:
                    raise ValueError(
                        tr(
                            "This recording exceeds the 1.5 GB decoded PCM limit. Split the file first."
                        )
                    )
                blocks.append(block)
        for converted in resampler.resample(None):
            block = converted.to_ndarray().T.copy()
            total += block.nbytes
            if total > MAX_DECODE_BYTES:
                raise ValueError(
                    tr(
                        "This recording exceeds the 1.5 GB decoded PCM limit. Split the file first."
                    )
                )
            blocks.append(block)
    if not blocks:
        raise ValueError(tr("The file contains no decodable audio samples."))
    return validate(np.concatenate(blocks), rate), rate


def resample(data: np.ndarray, source: int, target: int) -> np.ndarray:
    if source == target:
        return np.asarray(data, dtype=np.float32)
    divisor = math.gcd(source, target)
    return resample_poly(data, target // divisor, source // divisor, axis=0).astype(
        np.float32
    )


def bounds(start: float, end: float, rate: int, length: int) -> tuple[int, int]:
    if not math.isfinite(start) or not math.isfinite(end):
        raise ValueError(tr("Invalid selection boundaries."))
    a, b = max(0, round(start * rate)), min(length, round(end * rate))
    if a >= b:
        raise ValueError(tr("Select a non-empty fragment."))
    return a, b


def save_audio(path: str, data: np.ndarray, rate: int) -> None:
    """Atomic export; original is protected by the caller."""
    data = validate(data, rate)
    dest = Path(path)
    formats = {".wav": "WAV", ".flac": "FLAC", ".ogg": "OGG"}
    fmt = formats.get(dest.suffix.lower())
    if not fmt:
        raise ValueError(tr("Export formats: WAV, FLAC or OGG."))
    fd, temporary = tempfile.mkstemp(suffix=dest.suffix, dir=dest.parent)
    os.close(fd)
    try:
        sf.write(
            temporary,
            data,
            rate,
            format=fmt,
            subtype="VORBIS" if fmt == "OGG" else "PCM_24",
        )
        os.replace(temporary, dest)
    finally:
        Path(temporary).unlink(missing_ok=True)


def mono_for_speech(data: np.ndarray) -> np.ndarray:
    # Pick the strongest channel; averaging antiphase stereo can erase speech.
    energy = np.mean(np.square(data, dtype=np.float64), axis=0)
    return data[:, int(np.argmax(energy))].copy()
