"""Offline FlexSED adapter. Event scores are not transcripts or separated audio."""

from __future__ import annotations

import gc
import math

import numpy as np

from .audio import resample, validate
from .processing import model_directory

FRAME_RATE = 25
COLORS = ("#a98bfa", "#69baff", "#f0a567", "#e58fb6", "#d3cd73", "#77c8a0")


def parse_queries(text: str) -> list[str]:
    queries = list(
        dict.fromkeys(part.strip() for part in text.split(";") if part.strip())
    )
    if not 1 <= len(queries) <= 6 or any(len(q) > 120 for q in queries):
        raise ValueError("Введите 1–6 событий через «;», каждое до 120 символов.")
    return queries


def available() -> bool:
    root = model_directory("flexsed")
    return all(
        (root / name).is_file()
        for name in (
            "flexsed_as.pt",
            "clap-text/config.json",
            "clap-text/model.safetensors",
            "clap-text/tokenizer.json",
            "manifest.json",
        )
    )


def score_regions(
    scores,
    duration,
    query,
    channel,
    threshold=0.5,
    min_seconds=0.12,
    gap_seconds=0.12,
    color=COLORS[0],
):
    """Merge frame runs without moving the final partial frame beyond the audio."""
    scores = np.asarray(scores, dtype=np.float32)
    if scores.ndim != 1 or not np.isfinite(scores).all():
        raise ValueError("Некорректные оценки FlexSED.")
    if not math.isfinite(duration) or duration <= 0 or not 0.05 <= threshold <= 0.95:
        raise ValueError("Некорректная длительность или порог событий.")
    mask = scores >= threshold
    edges = np.diff(np.pad(mask.astype(np.int8), (1, 1)))
    runs = list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))
    merged = []
    for a, b in runs:
        if merged and (a - merged[-1][1]) / FRAME_RATE <= gap_seconds + 1e-9:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    regions = []
    for a, b in merged:
        start, end = a / FRAME_RATE, min(duration, b / FRAME_RATE)
        if end - start + 1e-9 >= min_seconds:
            regions.append(
                dict(
                    start=start,
                    end=end,
                    label=query,
                    channel=channel,
                    score=float(scores[a:b].max()),
                    color=color,
                )
            )
    return regions


class FlexSED:
    def __init__(self, queries):
        if not available():
            raise RuntimeError(
                "Веса FlexSED / CLAP не установлены. Нужна сборка с FlexSED или запуск tools/prepare_flexsed.py."
            )
        import torch
        from transformers import ClapTextModelWithProjection, RobertaTokenizerFast

        from ._vendor.flexsed.sed_decoder import Decoder, TSED_Wrapper
        from ._vendor.flexsed.transformer import Dasheng_Encoder

        self.queries = parse_queries(";".join(queries))
        torch.set_num_threads(2)
        root = model_directory("flexsed")
        # Match upstream prompts and encode each independently (same padding behavior).
        tokenizer = RobertaTokenizerFast.from_pretrained(
            str(root / "clap-text"), local_files_only=True
        )
        clap = ClapTextModelWithProjection.from_pretrained(
            str(root / "clap-text"), local_files_only=True
        ).eval()
        with torch.inference_mode():
            embeddings = []
            for query in self.queries:
                prompt = f"The sound of {query.replace('_', ' ').capitalize()}"
                tokens = tokenizer([prompt], padding=True, return_tensors="pt")
                embeddings.append(clap(**tokens).text_embeds.unsqueeze(1))
            self.query = torch.cat(embeddings, dim=1)
        del clap, tokenizer
        gc.collect()
        encoder = Dasheng_Encoder(
            target_length=1008,
            patch_size=(64, 4),
            patch_stride=(64, 4),
            embed_dim=768,
            depth=12,
            num_heads=12,
        )
        decoder = Decoder(
            embed_dim=768, depth=6, num_heads=12, cls_dim=512, fusion="adaln"
        )
        self.model = TSED_Wrapper(encoder, decoder, [6, 7, 8, 9, 10, 11], False).eval()
        state = torch.load(
            root / "flexsed_as.pt", map_location="cpu", weights_only=True, mmap=True
        )
        self.model.load_state_dict(state["model"], strict=True)
        del state

    def predict(self, data, rate, threshold=0.5, channel=0):
        """channel=0 analyses channels independently; otherwise it is one-based."""
        import torch

        data = validate(data, rate)
        if not isinstance(channel, int) or not 0 <= channel <= data.shape[1]:
            raise ValueError("Выберите существующий канал.")
        if not 0.05 <= threshold <= 0.95:
            raise ValueError("Порог событий должен быть от 0.05 до 0.95.")
        duration = len(data) / rate
        channels = range(data.shape[1]) if channel == 0 else [channel - 1]
        regions, curves = [], []
        with torch.inference_mode():
            for ch in channels:
                audio = resample(data[:, ch], rate, 16000)
                blocks = []
                for start in range(0, len(audio), 160000):
                    segment = audio[start : start + 160000]
                    count = min(250, math.ceil(len(segment) / 640))
                    peak = float(np.max(np.abs(segment)))
                    if peak < 1e-9:
                        blocks.append(np.zeros((len(self.queries), count), np.float32))
                        continue
                    # Preserve upstream variable-length context. Pad only to one
                    # 40 ms frame, not to ten seconds: long synthetic silence changes attention.
                    padded = np.pad(
                        segment / (peak + 1e-9),
                        (0, max(640, count * 640) - len(segment)),
                    )
                    waveform = torch.from_numpy(padded.copy()).unsqueeze(0)
                    logits = self.model(
                        self.model.forward_to_spec(waveform), self.query
                    )
                    scores = torch.sigmoid(logits)[:, 0, :count].numpy().copy()
                    if (
                        scores.shape != (len(self.queries), count)
                        or not np.isfinite(scores).all()
                    ):
                        raise RuntimeError("Неожиданный выход FlexSED.")
                    blocks.append(scores)
                scores = np.concatenate(blocks, axis=1)
                for index, query in enumerate(self.queries):
                    regions += score_regions(
                        scores[index],
                        duration,
                        query,
                        ch + 1,
                        threshold,
                        color=COLORS[index],
                    )
                    curves.append(
                        dict(label=query, channel=ch + 1, scores=scores[index].tolist())
                    )
        regions.sort(key=lambda r: (r["start"], r["channel"], r["label"]))
        return dict(
            events=regions,
            queries=self.queries,
            threshold=threshold,
            duration=duration,
            frame_rate=FRAME_RATE,
            curves=curves,
            model="FlexSED AudioSet-Strong",
            score_kind="model_score_not_calibrated_probability",
        )


def detect_events(data, rate, queries, threshold=0.5, channel=0):
    return FlexSED(queries).predict(data, rate, threshold, channel)
