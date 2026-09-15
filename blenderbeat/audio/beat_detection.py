"""
BlenderBeat — BPM and beat detection.

Estimates tempo via auto-correlation of onset strength,
detects beat positions via peak picking, estimates downbeats,
and detects basic song structure (drops, builds, energy regions).
"""

import numpy as np
from typing import Dict, List, Tuple, Optional

from .utils import normalize_signal, compute_rms
from ..utils.performance import Timer


def estimate_bpm(
    onset_strength: np.ndarray,
    sample_rate: int,
    hop_length: int,
    min_bpm: float = 60.0,
    max_bpm: float = 200.0,
) -> float:
    """
    Estimate BPM using auto-correlation of onset strength.

    Args:
        onset_strength: Onset strength envelope.
        sample_rate: Audio sample rate.
        hop_length: Hop size used in analysis.
        min_bpm: Minimum plausible BPM.
        max_bpm: Maximum plausible BPM.

    Returns:
        Estimated BPM.
    """
    # Frame rate of the onset signal
    frame_rate = sample_rate / hop_length

    # Convert BPM bounds to lag bounds (in frames)
    min_lag = int(frame_rate * 60.0 / max_bpm)
    max_lag = int(frame_rate * 60.0 / min_bpm)

    # Ensure we have enough data
    if len(onset_strength) < max_lag * 2:
        max_lag = len(onset_strength) // 2

    if min_lag >= max_lag or max_lag <= 0:
        return 120.0  # Default fallback

    # Auto-correlation
    onset_centered = onset_strength - np.mean(onset_strength)
    correlation = np.correlate(onset_centered, onset_centered, mode='full')
    correlation = correlation[len(correlation) // 2:]  # Keep positive lags only

    # Search for peak in valid BPM range
    search_region = correlation[min_lag:max_lag + 1]
    if len(search_region) == 0:
        return 120.0

    peak_index = np.argmax(search_region) + min_lag
    bpm = 60.0 * frame_rate / peak_index

    # Sanity check — try to find if half or double tempo is more plausible
    # by checking peaks at those lags
    half_lag = peak_index * 2
    double_lag = peak_index // 2

    if half_lag < len(correlation):
        half_bpm = 60.0 * frame_rate / half_lag
        if min_bpm <= half_bpm <= max_bpm:
            # If the half-tempo peak is strong, we might have doubled
            if correlation[half_lag] > correlation[peak_index] * 0.8:
                bpm = half_bpm

    return round(bpm, 1)


def detect_beats(
    onset_strength: np.ndarray,
    sample_rate: int,
    hop_length: int,
    bpm: float,
) -> np.ndarray:
    """
    Detect beat positions using onset strength peak picking
    guided by the estimated BPM.

    Returns:
        Array of beat times in seconds.
    """
    frame_rate = sample_rate / hop_length
    expected_beat_frames = frame_rate * 60.0 / bpm

    # Adaptive threshold: local median + factor
    # Use a window roughly 2x the expected beat interval
    window_size = int(expected_beat_frames * 2)
    window_size = max(window_size, 8)

    beats = []
    last_beat_frame = -expected_beat_frames  # Allow first beat immediately

    # Minimum distance between beats (70% of expected interval)
    min_distance = int(expected_beat_frames * 0.7)

    for i in range(len(onset_strength)):
        # Skip if too close to last beat
        if i - last_beat_frame < min_distance:
            continue

        # Local window for threshold calculation
        win_start = max(0, i - window_size)
        win_end = min(len(onset_strength), i + window_size)
        local_window = onset_strength[win_start:win_end]

        threshold = np.median(local_window) + 0.1 * np.std(local_window)
        threshold = max(threshold, 0.05)  # Minimum absolute threshold

        # Check if current frame is a local peak above threshold
        if onset_strength[i] > threshold:
            # Verify it's a local maximum (higher than neighbors)
            is_peak = True
            for offset in range(1, min(4, min_distance)):
                if i - offset >= 0 and onset_strength[i] < onset_strength[i - offset]:
                    is_peak = False
                    break
                if i + offset < len(onset_strength) and onset_strength[i] < onset_strength[i + offset]:
                    is_peak = False
                    break

            if is_peak:
                beats.append(i)
                last_beat_frame = i

    # Convert frame indices to times
    beat_times = np.array(beats, dtype=np.float64) * hop_length / sample_rate
    return beat_times


def refine_beats_to_grid(
    beat_times: np.ndarray,
    bpm: float,
    duration: float,
) -> np.ndarray:
    """
    Snap detected beats to a regular grid based on BPM.

    This produces a cleaner, more musically regular beat track
    while preserving detected beat locations as guides.
    """
    if len(beat_times) == 0:
        # Generate grid from scratch
        beat_interval = 60.0 / bpm
        n_beats = int(duration / beat_interval)
        return np.arange(n_beats) * beat_interval

    beat_interval = 60.0 / bpm

    # Find the best grid offset by testing different phase offsets
    best_offset = 0.0
    best_score = float('inf')

    for candidate_offset in beat_times[:min(8, len(beat_times))]:
        # Build a grid starting from this offset
        grid_start = candidate_offset % beat_interval
        grid = np.arange(grid_start, duration, beat_interval)

        # Score: mean distance from detected beats to nearest grid point
        if len(grid) > 0:
            score = 0.0
            for bt in beat_times:
                distances = np.abs(grid - bt)
                score += np.min(distances)
            score /= len(beat_times)

            if score < best_score:
                best_score = score
                best_offset = grid_start

    # Generate the final grid
    grid_beats = np.arange(best_offset, duration, beat_interval)
    return grid_beats


def detect_downbeats(
    beat_times: np.ndarray,
    beats_per_bar: int = 4,
) -> np.ndarray:
    """
    Estimate downbeat (bar start) positions.

    Simple heuristic: every Nth beat is a downbeat.
    """
    if len(beat_times) == 0:
        return np.array([])

    downbeat_indices = np.arange(0, len(beat_times), beats_per_bar)
    return beat_times[downbeat_indices]


def detect_sections(
    rms_energy: np.ndarray,
    onset_strength: np.ndarray,
    sample_rate: int,
    hop_length: int,
    duration: float,
) -> Dict[str, list]:
    """
    Detect basic song sections based on energy patterns.

    Returns dict with:
        - drops: [(start_time, end_time, confidence), ...]
        - builds: [(start_time, end_time, confidence), ...]
        - breaks: [(start_time, end_time, confidence), ...]
        - high_energy: [(start_time, end_time), ...]
        - low_energy: [(start_time, end_time), ...]
        - silence: [(start_time, end_time), ...]
    """
    frame_rate = sample_rate / hop_length
    n_frames = len(rms_energy)

    # Smoothed energy for section detection (long window)
    window_size = int(frame_rate * 4.0)  # 4-second smoothing
    if window_size < 1:
        window_size = 1
    smoothed = np.convolve(
        rms_energy,
        np.ones(window_size) / window_size,
        mode='same',
    )

    # Normalize
    if smoothed.max() > 0:
        smoothed_norm = smoothed / smoothed.max()
    else:
        smoothed_norm = smoothed

    # Energy thresholds
    high_threshold = 0.6
    low_threshold = 0.2
    silence_threshold = 0.05

    sections = {
        "drops": [],
        "builds": [],
        "breaks": [],
        "high_energy": [],
        "low_energy": [],
        "silence": [],
    }

    # Detect energy regions
    _detect_energy_regions(
        smoothed_norm, frame_rate, sections,
        high_threshold, low_threshold, silence_threshold,
    )

    # Detect drops: sharp energy increase
    _detect_drops(smoothed_norm, frame_rate, sections)

    # Detect builds: gradually rising energy
    _detect_builds(smoothed_norm, frame_rate, sections)

    return sections


def _detect_energy_regions(
    energy: np.ndarray,
    frame_rate: float,
    sections: dict,
    high_thresh: float,
    low_thresh: float,
    silence_thresh: float,
):
    """Detect contiguous high/low/silence energy regions."""
    n = len(energy)
    i = 0

    while i < n:
        if energy[i] >= high_thresh:
            start = i
            while i < n and energy[i] >= high_thresh * 0.8:
                i += 1
            end = i
            if (end - start) / frame_rate > 1.0:  # At least 1 second
                sections["high_energy"].append((
                    start / frame_rate,
                    end / frame_rate,
                ))
        elif energy[i] <= silence_thresh:
            start = i
            while i < n and energy[i] <= silence_thresh * 1.5:
                i += 1
            end = i
            if (end - start) / frame_rate > 0.5:
                sections["silence"].append((
                    start / frame_rate,
                    end / frame_rate,
                ))
        elif energy[i] <= low_thresh:
            start = i
            while i < n and energy[i] <= low_thresh * 1.2:
                i += 1
            end = i
            if (end - start) / frame_rate > 1.0:
                sections["low_energy"].append((
                    start / frame_rate,
                    end / frame_rate,
                ))
        else:
            i += 1


def _detect_drops(energy: np.ndarray, frame_rate: float, sections: dict):
    """Detect drops: sudden large increase in energy."""
    # Look at energy derivative
    diff = np.diff(energy)

    # Smooth the derivative slightly
    kernel = np.ones(int(frame_rate * 0.5)) / int(max(1, frame_rate * 0.5))
    if len(kernel) > 1 and len(diff) > len(kernel):
        diff_smooth = np.convolve(diff, kernel, mode='same')
    else:
        diff_smooth = diff

    # Find sharp positive spikes
    threshold = np.std(diff_smooth) * 2.0
    if threshold < 0.01:
        return

    i = 0
    while i < len(diff_smooth):
        if diff_smooth[i] > threshold:
            start = i
            # Find the end of the spike
            while i < len(diff_smooth) and diff_smooth[i] > threshold * 0.3:
                i += 1
            end = i

            confidence = min(1.0, float(diff_smooth[start:end].max() / threshold))
            sections["drops"].append((
                start / frame_rate,
                end / frame_rate,
                round(confidence, 2),
            ))
        else:
            i += 1


def _detect_builds(energy: np.ndarray, frame_rate: float, sections: dict):
    """Detect builds: gradually rising energy over 2+ seconds."""
    min_build_frames = int(frame_rate * 2.0)
    if min_build_frames < 4:
        return

    # Moving linear regression slope over windows
    window = int(frame_rate * 4.0)
    if window < 4 or window > len(energy):
        return

    i = 0
    while i < len(energy) - window:
        segment = energy[i:i + window]

        # Simple linear trend: correlation with ramp
        ramp = np.linspace(0, 1, len(segment))
        correlation = np.corrcoef(segment, ramp)[0, 1]

        if correlation > 0.7:  # Strong upward trend
            # Extend the build region
            start = i
            while i < len(energy) - window:
                seg = energy[i:i + window]
                r = np.linspace(0, 1, len(seg))
                corr = np.corrcoef(seg, r)[0, 1]
                if corr < 0.5:
                    break
                i += window // 4

            confidence = min(1.0, abs(float(correlation)))
            sections["builds"].append((
                start / frame_rate,
                i / frame_rate,
                round(confidence, 2),
            ))
        else:
            i += window // 2


def analyze_beats(
    audio: np.ndarray,
    sample_rate: int,
    onset_strength: np.ndarray,
    rms_energy: np.ndarray,
    hop_length: int = 512,
    user_bpm: Optional[float] = None,
) -> Dict:
    """
    Full beat analysis pipeline.

    Returns dict containing:
        - bpm
        - beat_times
        - downbeat_times
        - beat_intensities
        - sections
    """
    with Timer("Beat detection"):
        duration = len(audio) / sample_rate

        # BPM estimation
        if user_bpm and user_bpm > 0:
            bpm = user_bpm
            print(f"[BlenderBeat] Using user-specified BPM: {bpm}")
        else:
            bpm = estimate_bpm(onset_strength, sample_rate, hop_length)
            print(f"[BlenderBeat] Estimated BPM: {bpm}")

        # Beat detection
        raw_beats = detect_beats(onset_strength, sample_rate, hop_length, bpm)

        # Refine to grid
        beat_times = refine_beats_to_grid(raw_beats, bpm, duration)

        # Downbeats
        downbeat_times = detect_downbeats(beat_times)

        # Beat intensities: onset strength at each beat position
        beat_intensities = []
        frame_rate = sample_rate / hop_length
        for bt in beat_times:
            frame_idx = int(bt * frame_rate)
            frame_idx = min(frame_idx, len(onset_strength) - 1)
            beat_intensities.append(float(onset_strength[frame_idx]))

        # Section detection
        sections = detect_sections(
            rms_energy, onset_strength,
            sample_rate, hop_length, duration,
        )

    return {
        "bpm": bpm,
        "beat_times": beat_times,
        "downbeat_times": downbeat_times,
        "beat_intensities": beat_intensities,
        "sections": sections,
    }
