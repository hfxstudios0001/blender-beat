"""
BlenderBeat — Seamless loop logic.

Calculates musically-aligned loop boundaries and ensures
animation data can loop seamlessly using crossfade blending
and periodic function alignment.
"""

import math
import numpy as np
from typing import Tuple


def calculate_loop_duration(
    bpm: float,
    loop_bars: int = 8,
    beats_per_bar: int = 4,
) -> float:
    """
    Calculate loop duration in seconds based on musical timing.

    Args:
        bpm: Beats per minute.
        loop_bars: Number of bars in the loop.
        beats_per_bar: Beats per bar (time signature numerator).

    Returns:
        Loop duration in seconds.
    """
    total_beats = loop_bars * beats_per_bar
    seconds_per_beat = 60.0 / bpm
    return total_beats * seconds_per_beat


def calculate_loop_frames(
    bpm: float,
    fps: float,
    loop_bars: int = 8,
    beats_per_bar: int = 4,
) -> int:
    """
    Calculate loop duration in Blender frames.

    Rounds to nearest integer frame.
    """
    duration = calculate_loop_duration(bpm, loop_bars, beats_per_bar)
    return int(round(duration * fps))


def get_loop_info(
    bpm: float,
    fps: float,
    loop_bars: int = 8,
    beats_per_bar: int = 4,
    full_song: bool = False,
    total_duration: float = 0.0,
) -> dict:
    """
    Get comprehensive loop timing information.

    Returns dict with all relevant loop metrics.
    """
    if full_song and total_duration > 0.0:
        duration = total_duration
        n_frames = max(1, int(round(duration * fps)))
        total_beats = int(round((duration / 60.0) * bpm))
    else:
        total_beats = loop_bars * beats_per_bar
        duration = calculate_loop_duration(bpm, loop_bars, beats_per_bar)
        n_frames = calculate_loop_frames(bpm, fps, loop_bars, beats_per_bar)

    seconds_per_beat = 60.0 / bpm if bpm > 0 else 0.5
    frames_per_beat = seconds_per_beat * fps

    return {
        "bpm": bpm,
        "fps": fps,
        "loop_bars": loop_bars,
        "beats_per_bar": beats_per_bar,
        "total_beats": total_beats,
        "duration_seconds": duration,
        "total_frames": n_frames,
        "seconds_per_beat": seconds_per_beat,
        "frames_per_beat": frames_per_beat,
        "start_frame": 1,
        "end_frame": n_frames,
    }



def crossfade_loop_signal(
    signal: np.ndarray,
    blend_frames: int = 15,
) -> np.ndarray:
    """
    Apply crossfade blending at loop boundaries to ensure seamlessness.

    Blends the last `blend_frames` of the signal with the first
    `blend_frames` so that the end value transitions smoothly
    into the start value.

    Args:
        signal: Input signal array (one loop's worth of frames).
        blend_frames: Number of frames for the crossfade zone.

    Returns:
        Signal with seamless loop boundaries.
    """
    if len(signal) < blend_frames * 2:
        blend_frames = len(signal) // 4

    if blend_frames < 2:
        return signal.copy()

    output = signal.copy()

    for i in range(blend_frames):
        # t goes from 0 to 1 across the blend zone
        t = i / blend_frames

        # Smooth blend using cosine interpolation
        blend = 0.5 * (1.0 - math.cos(math.pi * t))

        # At the end of the loop, blend toward the start value
        end_idx = len(output) - blend_frames + i
        if end_idx < len(output):
            start_val = output[i]
            end_val = output[end_idx]
            # Blend end toward start
            output[end_idx] = end_val * (1.0 - blend) + start_val * blend

    return output


def make_periodic_value(
    frame: int,
    total_frames: int,
    amplitude: float = 1.0,
    phase: float = 0.0,
    frequency: float = 1.0,
) -> float:
    """
    Generate a periodic value that is mathematically guaranteed
    to loop seamlessly over total_frames.

    Uses sin() with the period matched to the loop length.

    Args:
        frame: Current frame number.
        total_frames: Total frames in the loop.
        amplitude: Peak value.
        phase: Phase offset in radians.
        frequency: Number of complete cycles per loop.

    Returns:
        Periodic value.
    """
    t = (frame / total_frames) * 2.0 * math.pi * frequency + phase
    return amplitude * math.sin(t)


def make_periodic_array(
    total_frames: int,
    amplitude: float = 1.0,
    phase: float = 0.0,
    frequency: float = 1.0,
) -> np.ndarray:
    """
    Generate a full array of periodic values for a loop.

    Returns array of length total_frames.
    """
    frames = np.arange(total_frames)
    t = (frames / total_frames) * 2.0 * np.pi * frequency + phase
    return (amplitude * np.sin(t)).astype(np.float32)


def align_signal_to_loop(
    signal: np.ndarray,
    analysis_hop_length: int,
    analysis_sample_rate: int,
    loop_start_time: float,
    loop_duration: float,
    target_frames: int,
    fps: float,
) -> np.ndarray:
    """
    Extract and resample a segment of the analysis signal
    to match the Blender loop frame count.

    Args:
        signal: Full analysis signal array.
        analysis_hop_length: Hop length used during analysis.
        analysis_sample_rate: Sample rate of the analyzed audio.
        loop_start_time: Start time of the loop in seconds.
        loop_duration: Duration of the loop in seconds.
        target_frames: Number of Blender frames in the loop.
        fps: Blender frames per second.

    Returns:
        Resampled signal array of length target_frames.
    """
    frame_rate = analysis_sample_rate / analysis_hop_length

    # Convert loop boundaries to analysis frame indices
    start_idx = int(loop_start_time * frame_rate)
    end_idx = int((loop_start_time + loop_duration) * frame_rate)

    # Clamp to valid range
    start_idx = max(0, start_idx)
    end_idx = min(len(signal), end_idx)

    if end_idx <= start_idx:
        return np.zeros(target_frames, dtype=np.float32)

    # Extract the loop segment
    segment = signal[start_idx:end_idx]

    if len(segment) == 0:
        return np.zeros(target_frames, dtype=np.float32)

    # Resample to match Blender frame count using linear interpolation
    x_old = np.linspace(0, 1, len(segment))
    x_new = np.linspace(0, 1, target_frames)
    resampled = np.interp(x_new, x_old, segment)

    return resampled.astype(np.float32)
