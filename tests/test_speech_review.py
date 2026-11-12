from types import SimpleNamespace

from voxloom.speech import review_segment, review_sequence


def segment(text, **overrides):
    fields = dict(
        text=text,
        start=0.0,
        end=5.0,
        avg_logprob=-0.3,
        no_speech_prob=0.01,
        compression_ratio=1.0,
    )
    fields.update(overrides)
    return SimpleNamespace(**fields)


def test_repeated_hallucination_is_not_exported_as_speech():
    result = review_segment(segment("Я не могу сказать, " * 8), 5.0)
    assert result["needs_review"] and "repetition" in result["review_reasons"]
    assert result["text"].startswith("[unintelligible")
    assert result["candidate_text"].startswith("Я не могу")


def test_natural_short_repetition_preserved():
    result = review_segment(segment("Да, да, сейчас проверим запись."), 5.0)
    assert not result["needs_review"]
    assert result["text"] == "Да, да, сейчас проверим запись."


def test_low_score_and_clipped_timestamps():
    result = review_segment(
        segment("Текст", start=-0.2, end=8.0, avg_logprob=-1.4), 5.0
    )
    assert result["needs_review"]
    assert (result["start"], result["end"]) == (0.0, 5.0)


def test_repetition_across_timestamp_boundaries():
    items = [review_segment(segment("Что?", start=i, end=i + 1), 6.0) for i in range(6)]
    reviewed = review_sequence(items)
    assert all(
        s["needs_review"] and "repeated_segments" in s["review_reasons"]
        for s in reviewed
    )


def test_separate_natural_sentences_are_preserved():
    items = [
        review_segment(segment(s), 5.0) for s in ["Да.", "Сейчас проверим.", "Да."]
    ]
    assert not any(s["needs_review"] for s in review_sequence(items))
