"""
BlenderBeat — Main audio analysis orchestrator.

Coordinates loading, frequency analysis, beat detection,
and section detection into a single analysis result.
"""

import numpy as np
from typing import Dict, Optional

from .loader import load_audio, AudioLoadError
from .frequency import analyze_frequencies
from .beat_detection import analyze_beats
from .utils import compute_rms, normalize_signal
from ..utils.performance import Timer


class AnalysisResult:
    """
    Container for all audio analysis data.

    All signal arrays are normalized to [0.0, 1.0] and indexed
    by analysis frame (hop-aligned). Use frame_to_time() to
    convert indices to seconds.
    """

    def __init__(self):
        # Metadata
        self.sample_rate: int = 0
        self.duration: float = 0.0
        self.hop_length: int = 512
        self.frame_length: int = 2048
        self.n_frames: int = 0

        # Beat data
        self.bpm: float = 120.0
        self.beat_times: np.ndarray = np.array([])
        self.downbeat_times: np.ndarray = np.array([])
        self.beat_intensities: list = []

        # Per-frame signals (all [0, 1] normalized)
        self.rms: np.ndarray = np.array([])
        self.sub_bass: np.ndarray = np.array([])
        self.bass: np.ndarray = np.array([])
        self.low_mid: np.ndarray = np.array([])
        self.mid: np.ndarray = np.array([])
        self.high_mid: np.ndarray = np.array([])
        self.treble: np.ndarray = np.array([])
        self.onset_strength: np.ndarray = np.array([])
        self.spectral_centroid: np.ndarray = np.array([])
        self.spectral_contrast: np.ndarray = np.array([])

        # Derived signals
        self.energy: np.ndarray = np.array([])        # Combined energy
        self.kick: np.ndarray = np.array([])           # Kick approximation
        self.snare: np.ndarray = np.array([])          # Snare approximation

        # Sections
        self.sections: Dict = {}

    def frame_to_time(self, frame_index: int) -> float:
        """Convert analysis frame index to time in seconds."""
        return frame_index * self.hop_length / self.sample_rate

    def time_to_frame(self, time_seconds: float) -> int:
        """Convert time in seconds to analysis frame index."""
        frame = int(time_seconds * self.sample_rate / self.hop_length)
        return min(frame, self.n_frames - 1)

    def get_value_at_time(self, signal_name: str, time_seconds: float) -> float:
        """Get a signal value at a specific time."""
        signal = getattr(self, signal_name, None)
        if signal is None or len(signal) == 0:
            return 0.0
        frame = self.time_to_frame(time_seconds)
        frame = max(0, min(frame, len(signal) - 1))
        return float(signal[frame])

    def get_signal(self, name: str) -> np.ndarray:
        """Get a signal array by name."""
        return getattr(self, name, np.array([]))

    def get_available_signals(self) -> list:
        """List all available signal names."""
        return [
            "rms", "sub_bass", "bass", "low_mid", "mid",
            "high_mid", "treble", "onset_strength",
            "spectral_centroid", "spectral_contrast",
            "energy", "kick", "snare",
        ]


def _compute_kick_signal(
    sub_bass: np.ndarray,
    bass: np.ndarray,
    onset_strength: np.ndarray,
) -> np.ndarray:
    """
    Approximate kick drum signal.

    Kicks have strong sub-bass + bass energy coinciding with
    sharp onsets.
    """
    # Combine low-frequency energy with onset detection
    low_freq = 0.6 * sub_bass + 0.4 * bass
    kick = low_freq * onset_strength

    # Normalize
    return normalize_signal(kick)


def _compute_snare_signal(
    mid: np.ndarray,
    high_mid: np.ndarray,
    onset_strength: np.ndarray,
) -> np.ndarray:
    """
    Approximate snare drum signal.

    Snares have strong mid/high-mid energy (the snap/crack)
    coinciding with onsets.
    """
    high_freq = 0.4 * mid + 0.6 * high_mid
    snare = high_freq * onset_strength

    return normalize_signal(snare)


def _compute_combined_energy(
    rms: np.ndarray,
    bass: np.ndarray,
    mid: np.ndarray,
    treble: np.ndarray,
) -> np.ndarray:
    """
    Compute a combined energy signal weighted across bands.
    """
    energy = 0.4 * rms + 0.3 * bass + 0.2 * mid + 0.1 * treble
    return normalize_signal(energy)


def analyze_audio(
    filepath: str,
    hop_length: int = 512,
    frame_length: int = 2048,
    user_bpm: Optional[float] = None,
) -> AnalysisResult:
    """
    Run the full audio analysis pipeline.

    Args:
        filepath: Path to audio file.
        hop_length: Hop size for STFT (smaller = higher resolution).
        frame_length: FFT window size.
        user_bpm: Optional user-specified BPM override.

    Returns:
        AnalysisResult with all extracted features.

    Raises:
        AudioLoadError: If the file cannot be loaded.
    """
    result = AnalysisResult()
    result.hop_length = hop_length
    result.frame_length = frame_length

    with Timer("Full audio analysis"):
        # Step 1: Load audio
        audio, sample_rate = load_audio(filepath)
        result.sample_rate = sample_rate
        result.duration = len(audio) / sample_rate
        print(f"[BlenderBeat] Audio: {result.duration:.1f}s, {sample_rate} Hz")

        # Step 2: RMS energy
        rms = compute_rms(audio, frame_length, hop_length)
        result.rms = normalize_signal(rms)
        result.n_frames = len(result.rms)

        # Step 3: Frequency analysis
        freq_data = analyze_frequencies(
            audio, sample_rate, frame_length, hop_length
        )

        result.sub_bass = freq_data["sub_bass"]
        result.bass = freq_data["bass"]
        result.low_mid = freq_data["low_mid"]
        result.mid = freq_data["mid"]
        result.high_mid = freq_data["high_mid"]
        result.treble = freq_data["treble"]
        result.onset_strength = freq_data["onset_strength"]
        result.spectral_centroid = freq_data["spectral_centroid"]
        result.spectral_contrast = freq_data["spectral_contrast"]

        # Step 4: Derived signals
        result.kick = _compute_kick_signal(
            result.sub_bass, result.bass, result.onset_strength
        )
        result.snare = _compute_snare_signal(
            result.mid, result.high_mid, result.onset_strength
        )
        result.energy = _compute_combined_energy(
            result.rms, result.bass, result.mid, result.treble
        )

        # Step 5: Beat detection
        beat_data = analyze_beats(
            audio, sample_rate,
            result.onset_strength, result.rms,
            hop_length, user_bpm,
        )

        result.bpm = beat_data["bpm"]
        result.beat_times = beat_data["beat_times"]
        result.downbeat_times = beat_data["downbeat_times"]
        result.beat_intensities = beat_data["beat_intensities"]
        result.sections = beat_data["sections"]

    print(f"[BlenderBeat] Analysis complete: BPM={result.bpm}, "
          f"beats={len(result.beat_times)}, frames={result.n_frames}")

    return result
