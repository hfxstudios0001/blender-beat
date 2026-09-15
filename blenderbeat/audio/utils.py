"""
BlenderBeat — Audio utility functions.

Common DSP helpers used by the analysis pipeline:
windowing, normalization, frame/time conversion.
"""

import math
import numpy as np
from typing import Optional


def to_mono(audio_data: np.ndarray) -> np.ndarray:
    """Convert multi-channel audio to mono by averaging channels."""
    if audio_data.ndim == 1:
        return audio_data
    # Average across channels (axis=1 for shape [samples, channels])
    return audio_data.mean(axis=1)


def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
    """
    Normalize audio to float32 in range [-1.0, 1.0].

    Handles int16, int32, float32, float64 input formats.
    """
    if audio_data.dtype == np.float32:
        peak = np.abs(audio_data).max()
        if peak > 0:
            return audio_data / peak
        return audio_data

    if audio_data.dtype == np.float64:
        audio_data = audio_data.astype(np.float32)
        peak = np.abs(audio_data).max()
        if peak > 0:
            return audio_data / peak
        return audio_data

    if audio_data.dtype == np.int16:
        return audio_data.astype(np.float32) / 32768.0

    if audio_data.dtype == np.int32:
        return audio_data.astype(np.float32) / 2147483648.0

    if audio_data.dtype == np.uint8:
        return (audio_data.astype(np.float32) - 128.0) / 128.0

    # Generic fallback
    audio_float = audio_data.astype(np.float32)
    peak = np.abs(audio_float).max()
    if peak > 0:
        return audio_float / peak
    return audio_float


def normalize_signal(signal: np.ndarray) -> np.ndarray:
    """Normalize a signal to [0.0, 1.0] range."""
    min_val = signal.min()
    max_val = signal.max()
    if max_val == min_val:
        return np.zeros_like(signal)
    return (signal - min_val) / (max_val - min_val)


def frames_to_time(
    frame_indices: np.ndarray,
    sample_rate: int,
    hop_length: int,
) -> np.ndarray:
    """Convert analysis frame indices to time in seconds."""
    return frame_indices.astype(np.float64) * hop_length / sample_rate


def time_to_frames(
    times: np.ndarray,
    sample_rate: int,
    hop_length: int,
) -> np.ndarray:
    """Convert times in seconds to analysis frame indices."""
    return (times * sample_rate / hop_length).astype(int)


def time_to_blender_frame(
    time_seconds: float,
    fps: float,
) -> int:
    """Convert time in seconds to Blender frame number."""
    return int(round(time_seconds * fps))


def blender_frame_to_time(
    frame: int,
    fps: float,
) -> float:
    """Convert Blender frame number to time in seconds."""
    return frame / fps


def compute_rms(audio_data: np.ndarray, frame_length: int, hop_length: int) -> np.ndarray:
    """
    Compute RMS energy per frame.

    Args:
        audio_data: Mono audio as float32.
        frame_length: Window size in samples.
        hop_length: Hop size in samples.

    Returns:
        RMS values per frame.
    """
    # Pad audio to ensure complete last frame
    pad_length = frame_length // 2
    padded = np.pad(audio_data, (pad_length, pad_length), mode='constant')

    num_frames = 1 + (len(padded) - frame_length) // hop_length
    rms = np.zeros(num_frames, dtype=np.float32)

    for i in range(num_frames):
        start = i * hop_length
        end = start + frame_length
        frame = padded[start:end]
        rms[i] = np.sqrt(np.mean(frame ** 2))

    return rms


def apply_hann_window(frame: np.ndarray) -> np.ndarray:
    """Apply a Hann window to an audio frame."""
    n = len(frame)
    window = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(n) / n))
    return frame * window


def hz_to_mel(hz: float) -> float:
    """Convert frequency in Hz to Mel scale."""
    return 2595.0 * math.log10(1.0 + hz / 700.0)


def mel_to_hz(mel: float) -> float:
    """Convert Mel scale to frequency in Hz."""
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)
