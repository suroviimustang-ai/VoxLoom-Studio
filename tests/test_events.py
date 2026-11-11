import numpy as np
import pytest

from voxloom.events import parse_queries, score_regions


def test_intervals_cross_chunk_boundary_without_time_drift():
    scores = np.zeros(508, np.float32)
    scores[246:255] = 0.8  # 9.84–10.20, across a ten-second model block.
    scores[500:] = 0.7
    events = score_regions(scores, 20.29, "Speech", 2)
    assert len(events) == 2
    assert events[0]["start"] == 9.84 and events[0]["end"] == 10.2
    assert events[1]["end"] == 20.29
    assert events[0]["channel"] == 2


def test_brief_gaps_merge_but_isolated_spike_is_rejected():
    scores = np.zeros(60, np.float32)
    scores[5:10] = 0.9
    scores[12:18] = 0.8
    scores[40] = 0.99
    events = score_regions(scores, 2.4, "Speech", 1)
    assert len(events) == 1
    assert events[0]["start"] == 0.2 and events[0]["end"] == 0.72
    assert score_regions(np.zeros(25), 1, "Speech", 1) == []


def test_queries_and_invalid_scores():
    assert parse_queries(" Speech; Whispering; Speech; ") == ["Speech", "Whispering"]
    for query in (";", ";".join(map(str, range(7))), "x" * 121):
        with pytest.raises(ValueError):
            parse_queries(query)
    with pytest.raises(ValueError):
        score_regions([np.nan], 1, "Speech", 1)


def test_short_tail_preserves_context_and_channels():
    import torch

    from voxloom.events import FlexSED

    lengths = []

    class FakeModel:
        def forward_to_spec(self, x):
            lengths.append(x.shape[-1])
            return x

        def __call__(self, x, query):
            return torch.full((1, 1, x.shape[-1] // 640), 2.0)

    engine = FlexSED.__new__(FlexSED)
    engine.queries = ["Speech"]
    engine.query = None
    engine.model = FakeModel()
    audio = np.ones((171200, 2), np.float32) * 0.1
    audio[:, 1] *= -1
    audio.setflags(write=False)
    result = engine.predict(audio, 16000)
    assert lengths == [160000, 11520, 160000, 11520]
    assert len(result["events"]) == 2
    assert [e["channel"] for e in result["events"]] == [1, 2]
    assert all(e["end"] == 10.7 for e in result["events"])
    assert np.all(audio[:, 0] == 0.1) and np.all(audio[:, 1] == -0.1)
