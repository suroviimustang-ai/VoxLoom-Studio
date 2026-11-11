from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass
from itertools import groupby

import numpy as np

from .audio import mono_for_speech, resample
from .processing import model_directory


@dataclass
class Region:
    start: float
    end: float
    text: str = ""

    def as_dict(self):
        return asdict(self)


def review_segment(part, duration: float) -> dict:
    """Flag suspicious output; these heuristics cannot establish transcription accuracy."""
    text = part.text.strip()
    words = re.findall(r"\w+", text.lower())
    reasons = []
    if any(sum(1 for _ in group) >= 6 for _, group in groupby(words)):
        reasons.append("repetition")
    for size in range(3, min(7, len(words) // 3 + 1)):
        counts = Counter(
            tuple(words[i : i + size]) for i in range(len(words) - size + 1)
        )
        if (
            counts
            and max(counts.values()) >= 3
            and max(counts.values()) * size >= 0.45 * len(words)
        ):
            if "repetition" not in reasons:
                reasons.append("repetition")
            break
    if part.avg_logprob < -1.0:
        reasons.append("low_model_score")
    if part.no_speech_prob >= 0.6:
        reasons.append("possible_non_speech")
    if getattr(part, "compression_ratio", 0) > 2.4:
        reasons.append("high_compression")
    start = max(0.0, min(float(part.start), duration))
    end = max(start, min(float(part.end), duration))
    if len(text) > 45 * max(0.5, end - start):
        reasons.append("implausible_text_rate")
    return dict(
        start=start,
        end=end,
        text="[неразборчиво — требуется прослушивание]" if reasons else text,
        candidate_text=text if reasons else "",
        needs_review=bool(reasons),
        review_reasons=reasons,
        avg_logprob=float(part.avg_logprob),
        no_speech_prob=float(part.no_speech_prob),
    )


def review_sequence(segments: list[dict]) -> list[dict]:
    """Whisper can repeat a sentence across separate timestamped segments."""

    def key(record):
        return tuple(
            re.findall(r"\w+", (record.get("candidate_text") or record["text"]).lower())
        )

    for _, group in groupby(segments, key=key):
        run = list(group)
        if len(run) < 3:
            continue
        for record in run:
            if not record.get("candidate_text"):
                record["candidate_text"] = record["text"]
            record["needs_review"] = True
            record["text"] = "[неразборчиво — требуется прослушивание]"
            if "repeated_segments" not in record.setdefault("review_reasons", []):
                record["review_reasons"].append("repeated_segments")
    return segments


def detect(
    data: np.ndarray,
    rate: int,
    threshold: float = 0.5,
    silence_ms: int = 350,
    min_speech_ms: int = 200,
) -> list[Region]:
    from faster_whisper.vad import VadOptions, get_speech_timestamps

    # Union per-channel VAD: do not lose speech on a quieter microphone.
    intervals = []
    for channel in data.T:
        audio = resample(channel, rate, 16000)
        chunks = get_speech_timestamps(
            audio,
            VadOptions(
                threshold=threshold,
                min_speech_duration_ms=min_speech_ms,
                min_silence_duration_ms=silence_ms,
                speech_pad_ms=100,
                max_speech_duration_s=30,
            ),
        )
        intervals.extend(
            (c["start"] / 16000, min(len(data) / rate, c["end"] / 16000))
            for c in chunks
        )
    merged: list[Region] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1].end:
            merged[-1].end = max(merged[-1].end, end)
        elif end > start:
            merged.append(Region(start, end))
    return merged


def transcribe(
    data: np.ndarray, rate: int, model: str = "small", language: str = "ru"
) -> dict:
    from .processing import whisper_ready

    if not whisper_ready(model):
        raise RuntimeError(
            f"Комплект Whisper {model} отсутствует или повреждён. Установите пакет через «Модели → Установить пакет»."
        )
    from ctranslate2 import get_supported_compute_types
    from faster_whisper import WhisperModel

    path = model_directory(f"whisper-{model}")
    compute = "int8" if "int8" in get_supported_compute_types("cpu") else "float32"
    engine = WhisperModel(
        str(path),
        device="cpu",
        compute_type=compute,
        cpu_threads=4,
        local_files_only=True,
    )
    audio = resample(mono_for_speech(data), rate, 16000)
    parts, info = engine.transcribe(
        audio,
        language=None if language == "auto" else language,
        beam_size=5,
        temperature=0,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    segments = review_sequence(
        [review_segment(p, len(audio) / 16000) for p in parts if p.text.strip()]
    )
    return {
        "text": " ".join(p["text"] for p in segments),
        "language": info.language,
        "segments": segments,
        "review_count": sum(s["needs_review"] for s in segments),
    }
