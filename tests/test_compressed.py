"""Verify actual encoded inputs, including AAC and MP3, through bundled PyAV."""

import av
import numpy as np
import pytest

from voxloom.audio import load_audio


@pytest.mark.parametrize(
    "extension,codec", [("mp3", "libmp3lame"), ("m4a", "aac"), ("aac", "aac")]
)
def test_encoded_input(tmp_path, extension, codec):
    rate = 48000
    signal = (0.2 * np.sin(2 * np.pi * 440 * np.arange(rate) / rate)).astype(
        np.float32
    )[None, :]
    path = tmp_path / f"тест.{extension}"
    with av.open(str(path), mode="w") as output:
        stream = output.add_stream(codec, rate=rate)
        stream.layout = "mono"
        frame = av.AudioFrame.from_ndarray(signal, format="fltp", layout="mono")
        frame.sample_rate = rate
        for packet in stream.encode(frame):
            output.mux(packet)
        for packet in stream.encode(None):
            output.mux(packet)
    data, sr = load_audio(str(path))
    assert sr == rate and data.shape[1] == 1
    assert abs(len(data) - rate) < 4096 and np.max(np.abs(data)) > 0.1
