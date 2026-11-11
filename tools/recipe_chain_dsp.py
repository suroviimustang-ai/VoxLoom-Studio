"""Bounded offline DSP for the user's experimental chain; not an app preset."""

import numpy as np
from scipy import ndimage, signal


def peaking(rate, frequency, gain, q):
    # RBJ Audio EQ Cookbook, W3C: https://www.w3.org/TR/audio-eq-cookbook/
    amplitude = 10 ** (gain / 40)
    omega = 2 * np.pi * frequency / rate
    alpha = np.sin(omega) / (2 * q)
    cosine = np.cos(omega)
    b = [1 + alpha * amplitude, -2 * cosine, 1 - alpha * amplitude]
    a = [1 + alpha / amplitude, -2 * cosine, 1 - alpha / amplitude]
    return np.array(b + a) / a[0]


def high_shelf(rate, frequency, gain):
    amplitude = 10 ** (gain / 40)
    omega = 2 * np.pi * frequency / rate
    cosine = np.cos(omega)
    term = 2 * np.sqrt(amplitude) * np.sin(omega) / np.sqrt(2)  # shelf slope S=1
    b = [
        amplitude * ((amplitude + 1) + (amplitude - 1) * cosine + term),
        -2 * amplitude * ((amplitude - 1) + (amplitude + 1) * cosine),
        amplitude * ((amplitude + 1) + (amplitude - 1) * cosine - term),
    ]
    a = [
        (amplitude + 1) - (amplitude - 1) * cosine + term,
        2 * ((amplitude - 1) - (amplitude + 1) * cosine),
        (amplitude + 1) - (amplitude - 1) * cosine - term,
    ]
    return np.array(b + a) / a[0]


def equalizer(rate):
    return np.vstack(
        [
            signal.butter(4, 88, btype="highpass", fs=rate, output="sos"),
            peaking(rate, 325, -3, 1.35),
            peaking(rate, 3150, 3.5, 1.1),
            high_shelf(rate, 8000, -4),
        ]
    )


def spectral_gate(data, noise, rate):
    """Stationary log-spectrum threshold, bounded -10..0 dB smoothed mask.

    Four neighboring FFT bins are averaged; this is an explicitly documented
    interpretation of '3-4 bands', not a universal plug-in parameter conversion.
    """
    fft, hop = 2048, 512
    floor = 10 ** (-10 / 20)
    block, context = 20 * rate, round(0.25 * rate)
    output = np.empty_like(data)
    mask_min, mask_max = 1.0, 0.0
    for channel in range(data.shape[1]):
        _, _, profile = signal.stft(
            noise[:, channel],
            fs=rate,
            nperseg=fft,
            noverlap=fft - hop,
            boundary=None,
            padded=False,
        )
        level = 20 * np.log10(np.maximum(np.abs(profile), 1e-10))
        threshold = np.mean(level, axis=1) + 1.5 * np.std(level, axis=1)
        for start in range(0, len(data), block):
            end = min(len(data), start + block)
            left = max(0, ((start - context) // hop) * hop)
            right = min(len(data), ((end + context + hop - 1) // hop) * hop)
            _, _, spectrum = signal.stft(
                data[left:right, channel],
                fs=rate,
                nperseg=fft,
                noverlap=fft - hop,
                boundary="zeros",
                padded=True,
            )
            level = 20 * np.log10(np.maximum(np.abs(spectrum), 1e-10))
            mask = floor + (1 - floor) * (level > threshold[:, None])
            mask = ndimage.uniform_filter1d(mask, 4, axis=0, mode="nearest")
            mask = ndimage.uniform_filter1d(mask, 5, axis=1, mode="nearest")
            mask = np.clip(mask, floor, 1.0)
            mask_min = min(mask_min, float(mask.min()))
            mask_max = max(mask_max, float(mask.max()))
            _, recovered = signal.istft(
                spectrum * mask, fs=rate, nperseg=fft, noverlap=fft - hop, boundary=True
            )
            output[start:end, channel] = recovered[start - left : end - left]
    assert mask_min >= floor - 1e-9 and mask_max <= 1 + 1e-9
    return output, dict(
        mask_min_db=float(20 * np.log10(mask_min)),
        mask_max_db=float(20 * np.log10(mask_max)),
    )


def verify_filters(rate):
    def response(sos, frequency):
        return float(
            20
            * np.log10(
                abs(
                    signal.sosfreqz(np.atleast_2d(sos), worN=[frequency], fs=rate)[1][0]
                )
            )
        )

    assert abs(response(peaking(rate, 325, -3, 1.35), 325) + 3) < 1e-7
    assert abs(response(peaking(rate, 3150, 3.5, 1.1), 3150) - 3.5) < 1e-7
    assert abs(response(high_shelf(rate, 8000, -4), rate / 2) - (-4)) < 1e-7
    hp = signal.butter(4, 88, btype="highpass", fs=rate, output="sos")
    assert abs(response(hp, 88) + 3.0103) < 0.001
    assert 23.9 < response(hp, 20) - response(hp, 10) < 24.2
    return {
        str(f): response(equalizer(rate), f)
        for f in [20, 44, 88, 325, 1000, 3150, 8000, 16000]
    }
