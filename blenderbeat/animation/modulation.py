"""
BlenderBeat — Modulation System.

A reusable audio-visual modulation framework.
Computes final visual parameters by combining:
    final_value = base + (audio_mod * audio_weight) + (beat_impulse * beat_weight) + (lfo_mod * lfo_weight) + (random_mod * random_weight)

Features:
- Attack / Release envelope smoothing
- Custom response curves (linear, exponential, power, log)
- Multi-waveform LFO (Sine, Triangle, Saw, Square)
- Deterministic Perlin-like smoothed random drift
- Invert and clamp bounds
"""

import math
import numpy as np
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


class ResponseCurve:
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    SMOOTHSTEP = "smoothstep"


@dataclass
class LFOConfig:
    """Low Frequency Oscillator parameters."""
    enabled: bool = False
    frequency: float = 0.5  # Cycles per loop or second
    waveform: str = "sine"  # 'sine', 'triangle', 'saw', 'square'
    amplitude: float = 1.0
    phase: float = 0.0

    def evaluate(self, t: float) -> float:
        """Evaluate LFO at normalized phase t [0, 1]."""
        if not self.enabled:
            return 0.0
        phase = (t * self.frequency + self.phase) % 1.0
        if self.waveform == "sine":
            return math.sin(phase * 2.0 * math.pi) * self.amplitude
        elif self.waveform == "triangle":
            return (4.0 * abs(phase - 0.5) - 1.0) * self.amplitude
        elif self.waveform == "saw":
            return (2.0 * phase - 1.0) * self.amplitude
        elif self.waveform == "square":
            return (1.0 if phase < 0.5 else -1.0) * self.amplitude
        return 0.0


@dataclass
class ModulationTarget:
    """
    Defines how a parameter is modulated by audio, LFO, beat, and randomness.
    """
    name: str
    base_value: float = 0.0
    min_value: float = -1e6
    max_value: float = 1e6

    # Audio modulation
    audio_source: str = "bass"
    audio_weight: float = 1.0
    audio_power: float = 1.0
    invert_audio: bool = False

    # Smoothing
    smooth_attack: float = 0.3
    smooth_release: float = 0.1

    # Beat impulse
    beat_impulse_weight: float = 0.0
    beat_decay: float = 0.05

    # LFO
    lfo: LFOConfig = field(default_factory=LFOConfig)
    lfo_weight: float = 0.0

    # Randomness
    random_weight: float = 0.0
    random_seed: int = 42

    def apply_response_curve(self, val: float, curve: str = ResponseCurve.LINEAR) -> float:
        """Apply non-linear shaping to normalized [0, 1] audio signal."""
        val = np.clip(val, 0.0, 1.0)
        if curve == ResponseCurve.EXPONENTIAL:
            return float(val ** 2.0)
        elif curve == ResponseCurve.LOGARITHMIC:
            return float(math.log1p(val * (math.e - 1.0)))
        elif curve == ResponseCurve.SMOOTHSTEP:
            return float(val * val * (3.0 - 2.0 * val))
        return float(val)


def compute_modulated_signal(
    target: ModulationTarget,
    audio_signal: np.ndarray,
    total_frames: int,
    fps: float = 30.0,
    bpm: float = 120.0,
    curve: str = ResponseCurve.LINEAR,
) -> np.ndarray:
    """
    Compute frame-by-frame modulated signal values.
    Returns np.ndarray of length total_frames.
    """
    output = np.zeros(total_frames, dtype=np.float32)

    # 1. Audio signal processing
    if len(audio_signal) > 0:
        # Interpolate audio signal to total_frames
        if len(audio_signal) != total_frames:
            x_old = np.linspace(0, 1, len(audio_signal))
            x_new = np.linspace(0, 1, total_frames)
            audio = np.interp(x_new, x_old, audio_signal)
        else:
            audio = audio_signal.copy()

        # Invert if required
        if target.invert_audio:
            audio = 1.0 - audio

        # Exponential attack/release smoothing
        smoothed_audio = np.zeros_like(audio)
        curr = audio[0]
        for i in range(total_frames):
            target_val = audio[i]
            alpha = target.smooth_attack if target_val > curr else target.smooth_release
            curr = alpha * target_val + (1.0 - alpha) * curr
            smoothed_audio[i] = curr

        # Power curve
        if target.audio_power != 1.0:
            smoothed_audio = np.power(np.clip(smoothed_audio, 0.0, 1.0), target.audio_power)
    else:
        smoothed_audio = np.zeros(total_frames, dtype=np.float32)

    # 2. LFO array
    lfo_vals = np.zeros(total_frames, dtype=np.float32)
    if target.lfo.enabled and target.lfo_weight != 0.0:
        for f in range(total_frames):
            t = f / total_frames
            lfo_vals[f] = target.lfo.evaluate(t) * target.lfo_weight

    # 3. Random drift
    rand_vals = np.zeros(total_frames, dtype=np.float32)
    if target.random_weight != 0.0:
        rng = np.random.RandomState(target.random_seed)
        # Low frequency noise filtered
        coarse = rng.uniform(-1.0, 1.0, size=max(4, total_frames // 15))
        x_coarse = np.linspace(0, 1, len(coarse))
        x_fine = np.linspace(0, 1, total_frames)
        rand_vals = np.interp(x_fine, x_coarse, coarse) * target.random_weight

    # 4. Combine: base + audio + lfo + random
    output = (
        target.base_value
        + (smoothed_audio * target.audio_weight)
        + lfo_vals
        + rand_vals
    )

    return np.clip(output, target.min_value, target.max_value).astype(np.float32)
