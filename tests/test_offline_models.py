import numpy as np
import pytest

from voxloom import processing
from voxloom.speech import transcribe


@pytest.mark.parametrize("missing", (*processing.WHISPER_FILES, "vocabulary.txt"))
def test_partial_whisper_bundle_does_not_fall_back_to_download(
    tmp_path, monkeypatch, missing
):
    for name in (*processing.WHISPER_FILES, "vocabulary.txt"):
        if name != missing:
            (tmp_path / name).write_bytes(b"fixture")
    monkeypatch.setattr(processing, "model_directory", lambda _: tmp_path)
    assert not processing.whisper_ready("base")
    with pytest.raises(RuntimeError, match="Install its pack"):
        transcribe(np.zeros((16000, 1), dtype=np.float32), 16000, "base")


def test_turbo_accepts_json_vocabulary(tmp_path, monkeypatch):
    for name in (*processing.WHISPER_FILES, "vocabulary.json"):
        (tmp_path / name).write_bytes(b"fixture")
    monkeypatch.setattr(processing, "model_directory", lambda _: tmp_path)
    assert processing.whisper_ready("large-v3-turbo")
