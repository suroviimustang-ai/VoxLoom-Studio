import numpy as np

from tools.recipe_chain_dsp import spectral_gate, verify_filters


def test_declared_filter_response():
    verify_filters(44100)


def test_gate_preserves_samples_and_block_boundaries_with_empty_noise_profile():
    rng = np.random.default_rng(67)
    data = rng.normal(0, 0.05, (44100 * 21 + 137, 1)).astype(np.float32)
    result, _ = spectral_gate(data, np.zeros((44100 * 2, 1), dtype=np.float32), 44100)
    assert result.shape == data.shape
    np.testing.assert_allclose(result, data, atol=3e-7, rtol=1e-5)


def test_noise_is_attenuated_with_bounded_mask():
    rng = np.random.default_rng(12)
    data = rng.normal(0, 0.01, (44100 * 3, 1)).astype(np.float32)
    result, mask = spectral_gate(data, data[:44100], 44100)
    assert -10.000001 <= mask["mask_min_db"] <= mask["mask_max_db"] <= 0.000001
    assert 0.25 < np.linalg.norm(result) / np.linalg.norm(data) < 0.85
    assert np.isfinite(result).all()
