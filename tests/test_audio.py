import numpy as np
import pytest

from voxloom.audio import (
    bounds,
    load_audio,
    mono_for_speech,
    resample,
    save_audio,
    validate,
)
from voxloom.processing import denoise, linked_limiter, normalize


@pytest.fixture
def audio():
    rate = 16000
    t = np.arange(rate * 2) / rate
    x = 0.2 * np.sin(2 * np.pi * 440 * t)
    return np.column_stack([x, -x]).astype(np.float32), rate


@pytest.mark.parametrize("extension", ["wav", "flac", "ogg"])
def test_roundtrip_formats(tmp_path, audio, extension):
    x, rate = audio
    path = tmp_path / f"запись.{extension}"
    save_audio(str(path), x, rate)
    y, sr = load_audio(str(path))
    assert sr == rate and y.shape == x.shape and np.isfinite(y).all()
    assert np.sqrt(np.mean((x - y) ** 2)) < 0.02


def test_invalid_audio_and_selection(audio):
    x, rate = audio
    with pytest.raises(ValueError):
        validate(np.zeros((0, 1)), rate)
    with pytest.raises(ValueError):
        validate(np.array([[np.nan]]), rate)
    with pytest.raises(ValueError):
        bounds(2, 1, rate, len(x))
    assert bounds(-1, 100, rate, len(x)) == (0, len(x))


def test_antiphase_speech_not_cancelled(audio):
    x, _ = audio
    assert np.max(np.abs(mono_for_speech(x))) > 0.19


def test_resampling_duration(audio):
    x, rate = audio
    assert resample(x, rate, 48000).shape == (96000, 2)


@pytest.mark.parametrize("method", ["spectral", "dsp", "rnnoise"])
def test_denoisers_preserve_source_shape_and_channels(audio, method):
    x, rate = audio
    copy = x.copy()
    result = denoise(x, rate, method)
    np.testing.assert_array_equal(x, copy)
    assert result.shape == x.shape and np.isfinite(result).all()
    assert np.max(np.abs(result)) <= 1


def test_stationary_gate_reduces_known_noise():
    rng = np.random.default_rng(42)
    noise = rng.normal(0, 0.03, (48000, 1)).astype(np.float32)
    result = denoise(noise, 16000, "spectral", 0.95, noise=noise[:16000])
    assert np.sqrt(np.mean(result**2)) < 0.75 * np.sqrt(np.mean(noise**2))


def test_normalization_silence_short_and_peak(audio):
    x, rate = audio
    silence = np.zeros_like(x)
    y, _ = normalize(silence, rate, "peak", -1)
    assert np.array_equal(y, silence)
    y, _ = normalize(x, rate, "peak", -3)
    assert abs(np.max(abs(y)) - 10 ** (-3 / 20)) < 1e-6
    with pytest.raises(ValueError):
        normalize(x[:100], rate, "lufs", -16)


def test_limiter_links_channels_and_keeps_ceiling():
    rng = np.random.default_rng(15)
    left = rng.normal(0, 1, 16000).astype(np.float32)
    audio = np.column_stack([left, left * 0.3])
    out = linked_limiter(audio, 16000)
    assert np.max(abs(out)) <= 10 ** (-1 / 20) + 1e-6
    np.testing.assert_allclose(out[:, 1], out[:, 0] * 0.3, atol=1e-7)


def test_lufs_target(audio):
    import pyloudnorm as pyln

    x, rate = audio
    result, note = normalize(x, rate, "lufs", -20)
    assert abs(pyln.Meter(rate).integrated_loudness(result) + 20) < 0.1
