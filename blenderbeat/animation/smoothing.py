"""
BlenderBeat — Signal smoothing and processing.

Provides smoothing, remapping, spring dynamics, and easing
functions that transform raw audio signals into organic,
cinematic motion curves.
"""

import math
import numpy as np
from typing import Optional


def exponential_smooth(
    signal: np.ndarray,
    attack: float = 0.3,
    release: float = 0.1,
) -> np.ndarray:
    """
    Asymmetric exponential moving average.

    Uses fast attack (responds quickly to increases) and
    slow release (decays gradually), which makes audio-reactive
    motion feel snappy on hits but smooth on decay.

    Args:
        signal: Input signal [0, 1].
        attack: Attack coefficient (0–1, higher = faster attack).
        release: Release coefficient (0–1, higher = faster release).

    Returns:
        Smoothed signal.
    """
    output = np.zeros_like(signal)
    if len(signal) == 0:
        return output

    output[0] = signal[0]

    for i in range(1, len(signal)):
        if signal[i] > output[i - 1]:
            # Attack: rising signal
            alpha = attack
        else:
            # Release: falling signal
            alpha = release

        output[i] = alpha * signal[i] + (1.0 - alpha) * output[i - 1]

    return output


def moving_average(signal: np.ndarray, window_size: int = 5) -> np.ndarray:
    """Simple moving average smoothing."""
    if window_size < 2 or len(signal) < window_size:
        return signal.copy()

    kernel = np.ones(window_size) / window_size
    smoothed = np.convolve(signal, kernel, mode='same')
    return smoothed.astype(np.float32)


def spring_smooth(
    signal: np.ndarray,
    stiffness: float = 0.3,
    damping: float = 0.7,
) -> np.ndarray:
    """
    Spring dynamics simulation.

    Creates a physically-inspired motion where values overshoot
    slightly and oscillate before settling — gives a natural,
    bouncy feel to audio-reactive parameters.

    Args:
        signal: Input signal (target positions).
        stiffness: Spring stiffness (0–1). Higher = snappier.
        damping: Damping factor (0–1). Higher = less overshoot.

    Returns:
        Spring-filtered signal.
    """
    output = np.zeros_like(signal)
    if len(signal) == 0:
        return output

    position = signal[0]
    velocity = 0.0

    for i in range(len(signal)):
        target = signal[i]
        force = (target - position) * stiffness
        velocity = velocity * damping + force
        position += velocity
        output[i] = position

    # Normalize back to [0, 1] range
    if output.max() > output.min():
        output = np.clip(output, 0.0, None)
        max_val = max(output.max(), 1.0)
        output = output / max_val

    return output.astype(np.float32)


def remap_signal(
    signal: np.ndarray,
    in_min: float = 0.0,
    in_max: float = 1.0,
    out_min: float = 0.0,
    out_max: float = 1.0,
) -> np.ndarray:
    """
    Remap signal values from one range to another.

    Values outside in_min/in_max are clamped.
    """
    clamped = np.clip(signal, in_min, in_max)
    if in_max == in_min:
        return np.full_like(signal, out_min)

    t = (clamped - in_min) / (in_max - in_min)
    return (out_min + t * (out_max - out_min)).astype(np.float32)


def threshold_signal(
    signal: np.ndarray,
    threshold: float = 0.3,
    soft: bool = True,
) -> np.ndarray:
    """
    Apply a threshold to a signal.

    Args:
        signal: Input signal.
        threshold: Cutoff value.
        soft: If True, smoothly remap; if False, hard binary cutoff.

    Returns:
        Thresholded signal.
    """
    if soft:
        # Soft threshold: remap values above threshold to [0, 1]
        return remap_signal(signal, threshold, 1.0, 0.0, 1.0)
    else:
        return (signal > threshold).astype(np.float32)


def multiply_signal(signal: np.ndarray, factor: float) -> np.ndarray:
    """Multiply signal by a constant factor, clamped to [0, 1]."""
    return np.clip(signal * factor, 0.0, 1.0).astype(np.float32)


def power_curve(signal: np.ndarray, power: float = 2.0) -> np.ndarray:
    """
    Apply a power curve for non-linear response.

    power > 1: emphasizes peaks, suppresses quiet parts
    power < 1: compresses dynamic range
    """
    return np.power(np.clip(signal, 0.0, 1.0), power).astype(np.float32)


def ease_in_out(signal: np.ndarray) -> np.ndarray:
    """Apply smoothstep easing (cubic Hermite interpolation)."""
    x = np.clip(signal, 0.0, 1.0)
    return (3.0 * x * x - 2.0 * x * x * x).astype(np.float32)


def add_noise(
    signal: np.ndarray,
    amount: float = 0.05,
    seed: int = 0,
) -> np.ndarray:
    """
    Add controlled random noise to a signal.

    Useful for adding subtle organic variation.
    """
    rng = np.random.RandomState(seed)
    noise = rng.uniform(-amount, amount, size=len(signal))
    return np.clip(signal + noise, 0.0, 1.0).astype(np.float32)


def phase_offset(signal: np.ndarray, offset_frames: int) -> np.ndarray:
    """
    Shift a signal by N frames (circular).

    Useful for creating layered motion where different elements
    respond at slightly different times.
    """
    return np.roll(signal, offset_frames)


def process_signal(
    signal: np.ndarray,
    smooth_attack: float = 0.3,
    smooth_release: float = 0.1,
    remap_min: float = 0.0,
    remap_max: float = 1.0,
    multiply: float = 1.0,
    spring_enabled: bool = False,
    spring_stiffness: float = 0.3,
    spring_damping: float = 0.7,
    power: float = 1.0,
    noise_amount: float = 0.0,
    noise_seed: int = 0,
) -> np.ndarray:
    """
    Apply a full signal processing chain.

    This is the main entry point for transforming raw audio signals
    into smooth, organic animation curves.

    Pipeline:
        input → smooth → remap → multiply → spring → power → noise → output
    """
    output = signal.copy()

    # 1. Smoothing
    output = exponential_smooth(output, smooth_attack, smooth_release)

    # 2. Remap range
    if remap_min != 0.0 or remap_max != 1.0:
        output = remap_signal(output, 0.0, 1.0, remap_min, remap_max)

    # 3. Multiply (intensity)
    if multiply != 1.0:
        output = multiply_signal(output, multiply)

    # 4. Spring dynamics
    if spring_enabled:
        output = spring_smooth(output, spring_stiffness, spring_damping)

    # 5. Power curve
    if power != 1.0:
        output = power_curve(output, power)

    # 6. Noise
    if noise_amount > 0:
        output = add_noise(output, noise_amount, noise_seed)

    return output
