"""
BlenderBeat — Frequency band extraction.

Computes STFT-based spectrograms and extracts energy in
standard frequency bands (sub-bass, bass, low-mid, mid, high-mid, treble).
Also computes spectral centroid and onset strength.
"""

import numpy as np
from typing import Dict, List, Tuple

from .utils import apply_hann_window, normalize_signal
from ..utils.performance import Timer


# Standard frequency band definitions (Hz)
FREQUENCY_BANDS = {
    "sub_bass":  (20,    60),
    "bass":      (60,    250),
    "low_mid":   (250,   500),
    "mid":       (500,   2000),
    "high_mid":  (2000,  4000),
    "treble":    (4000,  20000),
}


def compute_stft(
    audio: np.ndarray,
    sample_rate: int,
    frame_length: int = 2048,
    hop_length: int = 512,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute Short-Time Fourier Transform using numpy.

    Args:
        audio: Mono float32 audio.
        sample_rate: Sample rate in Hz.
        frame_length: FFT window size.
        hop_length: Hop between windows.

    Returns:
        (magnitude_spectrogram, frequencies):
            magnitude_spectrogram: shape [n_freq_bins, n_frames]
            frequencies: array of frequency values for each bin
    """
    # Pad audio for complete frames
    pad_length = frame_length // 2
    padded = np.pad(audio, (pad_length, pad_length), mode='constant')

    n_frames = 1 + (len(padded) - frame_length) // hop_length
    n_fft_bins = frame_length // 2 + 1

    magnitude = np.zeros((n_fft_bins, n_frames), dtype=np.float32)

    # Precompute Hann window
    window = np.hanning(frame_length).astype(np.float32)

    for i in range(n_frames):
        start = i * hop_length
        end = start + frame_length
        frame = padded[start:end] * window

        # Real FFT — only positive frequencies
        spectrum = np.fft.rfft(frame)
        magnitude[:, i] = np.abs(spectrum).astype(np.float32)

    frequencies = np.fft.rfftfreq(frame_length, d=1.0 / sample_rate)

    return magnitude, frequencies


def extract_band_energy(
    magnitude: np.ndarray,
    frequencies: np.ndarray,
    low_hz: float,
    high_hz: float,
) -> np.ndarray:
    """
    Extract energy in a specific frequency band across all frames.

    Args:
        magnitude: [n_freq_bins, n_frames] spectrogram.
        frequencies: Frequency value for each bin.
        low_hz: Lower frequency bound.
        high_hz: Upper frequency bound.

    Returns:
        Energy per frame (1D array).
    """
    # Find bin indices within the frequency range
    band_mask = (frequencies >= low_hz) & (frequencies < high_hz)

    if not np.any(band_mask):
        return np.zeros(magnitude.shape[1], dtype=np.float32)

    # Sum squared magnitudes in the band
    band_energy = np.sum(magnitude[band_mask, :] ** 2, axis=0)
    return band_energy.astype(np.float32)


def extract_all_bands(
    magnitude: np.ndarray,
    frequencies: np.ndarray,
) -> Dict[str, np.ndarray]:
    """
    Extract energy for all standard frequency bands.

    Returns:
        Dictionary mapping band name → normalized energy array [0, 1].
    """
    bands = {}
    for band_name, (low_hz, high_hz) in FREQUENCY_BANDS.items():
        energy = extract_band_energy(magnitude, frequencies, low_hz, high_hz)
        bands[band_name] = normalize_signal(energy)

    return bands


def compute_spectral_centroid(
    magnitude: np.ndarray,
    frequencies: np.ndarray,
) -> np.ndarray:
    """
    Compute spectral centroid per frame (perceived brightness).

    The centroid is the weighted mean of frequencies, where
    magnitudes are the weights.
    """
    # Avoid division by zero
    total_energy = np.sum(magnitude, axis=0)
    total_energy = np.maximum(total_energy, 1e-10)

    centroid = np.sum(magnitude * frequencies[:, np.newaxis], axis=0) / total_energy
    return centroid.astype(np.float32)


def compute_onset_strength(
    magnitude: np.ndarray,
) -> np.ndarray:
    """
    Compute onset strength as the positive half-wave-rectified
    flux (difference in spectral energy between frames).

    This detects sudden increases in energy — transients, attacks.
    """
    # Spectral flux: difference between consecutive frames
    diff = np.diff(magnitude, axis=1)

    # Half-wave rectify (keep only increases)
    diff = np.maximum(diff, 0)

    # Sum across frequency bins
    onset = np.sum(diff, axis=0)

    # Prepend a zero for frame alignment
    onset = np.concatenate([[0], onset])

    return normalize_signal(onset.astype(np.float32))


def compute_spectral_contrast(
    magnitude: np.ndarray,
    frequencies: np.ndarray,
    n_bands: int = 6,
) -> np.ndarray:
    """
    Compute simplified spectral contrast.

    Measures the difference between peaks and valleys in each sub-band.
    Returns mean contrast per frame.
    """
    n_frames = magnitude.shape[1]
    freq_min = frequencies[1]  # Skip DC
    freq_max = frequencies[-1]

    # Create logarithmically spaced band edges
    band_edges = np.logspace(
        np.log10(max(freq_min, 20)),
        np.log10(min(freq_max, 20000)),
        n_bands + 1,
    )

    contrast_sum = np.zeros(n_frames, dtype=np.float32)

    for i in range(n_bands):
        band_mask = (frequencies >= band_edges[i]) & (frequencies < band_edges[i + 1])
        if not np.any(band_mask):
            continue

        band_mag = magnitude[band_mask, :]

        # Top 20% energy (peaks) vs bottom 20% (valleys)
        sorted_mag = np.sort(band_mag, axis=0)
        n_bins = sorted_mag.shape[0]
        top_k = max(1, n_bins // 5)

        peaks = np.mean(sorted_mag[-top_k:, :], axis=0)
        valleys = np.mean(sorted_mag[:top_k, :], axis=0)

        contrast_sum += (peaks - valleys)

    return normalize_signal(contrast_sum)


def analyze_frequencies(
    audio: np.ndarray,
    sample_rate: int,
    frame_length: int = 2048,
    hop_length: int = 512,
) -> Dict[str, np.ndarray]:
    """
    Complete frequency analysis pipeline.

    Returns dict containing:
        - Band energies (sub_bass, bass, low_mid, mid, high_mid, treble)
        - spectral_centroid
        - onset_strength
        - spectral_contrast
        - magnitude (raw spectrogram for further analysis)
        - frequencies (frequency axis)
    """
    with Timer("Frequency analysis"):
        magnitude, frequencies = compute_stft(
            audio, sample_rate, frame_length, hop_length
        )

        result = extract_all_bands(magnitude, frequencies)

        result["spectral_centroid"] = normalize_signal(
            compute_spectral_centroid(magnitude, frequencies)
        )
        result["onset_strength"] = compute_onset_strength(magnitude)
        result["spectral_contrast"] = compute_spectral_contrast(
            magnitude, frequencies
        )

        # Store raw data for beat detection
        result["_magnitude"] = magnitude
        result["_frequencies"] = frequencies

    return result
