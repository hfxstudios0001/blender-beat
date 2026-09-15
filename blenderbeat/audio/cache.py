"""
BlenderBeat — Analysis cache.

Saves and loads audio analysis results as JSON files
so the expensive analysis only runs once per audio file.
"""

import json
import os
import hashlib
import numpy as np
from typing import Optional

from .analyzer import AnalysisResult


def _get_cache_path(audio_filepath: str) -> str:
    """
    Generate a cache file path based on the audio file path.

    Cache is stored alongside the audio file as:
        <audio_name>.blenderbeat_cache.json
    """
    base = os.path.splitext(audio_filepath)[0]
    return base + ".blenderbeat_cache.json"


def _file_hash(filepath: str) -> str:
    """Compute a quick hash of a file (first 64KB + file size)."""
    hasher = hashlib.md5()
    file_size = os.path.getsize(filepath)
    hasher.update(str(file_size).encode())

    with open(filepath, 'rb') as f:
        # Hash first 64KB for speed
        chunk = f.read(65536)
        hasher.update(chunk)

    return hasher.hexdigest()


def save_analysis(result: AnalysisResult, audio_filepath: str) -> str:
    """
    Save analysis results to a JSON cache file.

    Returns:
        Path to the cache file.
    """
    cache_path = _get_cache_path(audio_filepath)

    data = {
        "version": 1,
        "audio_file": os.path.basename(audio_filepath),
        "audio_hash": _file_hash(audio_filepath),

        # Metadata
        "sample_rate": result.sample_rate,
        "duration": result.duration,
        "hop_length": result.hop_length,
        "frame_length": result.frame_length,
        "n_frames": result.n_frames,
        "bpm": result.bpm,

        # Beat data (as lists for JSON)
        "beat_times": result.beat_times.tolist(),
        "downbeat_times": result.downbeat_times.tolist(),
        "beat_intensities": result.beat_intensities,

        # Per-frame signals — downsample to reduce file size
        # Store every Nth frame based on total frames
        "signals": _pack_signals(result),

        # Sections
        "sections": result.sections,
    }

    with open(cache_path, 'w') as f:
        json.dump(data, f, indent=None, separators=(',', ':'))

    file_size = os.path.getsize(cache_path)
    print(f"[BlenderBeat] Cache saved: {cache_path} ({file_size / 1024:.0f} KB)")

    return cache_path


def _pack_signals(result: AnalysisResult) -> dict:
    """
    Pack signal arrays for JSON serialization.

    Quantizes float values to reduce file size.
    """
    signals = {}

    for name in result.get_available_signals():
        arr = result.get_signal(name)
        if len(arr) > 0:
            # Quantize to 3 decimal places to save space
            signals[name] = [round(float(v), 3) for v in arr]

    return signals


def load_analysis(audio_filepath: str) -> Optional[AnalysisResult]:
    """
    Load analysis results from cache if available and valid.

    Returns:
        AnalysisResult if cache is valid, None otherwise.
    """
    cache_path = _get_cache_path(audio_filepath)

    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        print(f"[BlenderBeat] Cache file corrupted, will re-analyze")
        return None

    # Version check
    if data.get("version") != 1:
        print(f"[BlenderBeat] Cache version mismatch, will re-analyze")
        return None

    # Verify the audio file hasn't changed
    if os.path.exists(audio_filepath):
        current_hash = _file_hash(audio_filepath)
        if data.get("audio_hash") != current_hash:
            print(f"[BlenderBeat] Audio file changed, will re-analyze")
            return None

    # Reconstruct AnalysisResult
    result = AnalysisResult()
    result.sample_rate = data["sample_rate"]
    result.duration = data["duration"]
    result.hop_length = data["hop_length"]
    result.frame_length = data["frame_length"]
    result.n_frames = data["n_frames"]
    result.bpm = data["bpm"]

    result.beat_times = np.array(data["beat_times"])
    result.downbeat_times = np.array(data["downbeat_times"])
    result.beat_intensities = data["beat_intensities"]

    # Unpack signals
    signals = data.get("signals", {})
    for name in result.get_available_signals():
        if name in signals:
            setattr(result, name, np.array(signals[name], dtype=np.float32))

    result.sections = data.get("sections", {})

    print(f"[BlenderBeat] Loaded from cache: {cache_path}")
    return result


def is_cache_valid(audio_filepath: str) -> bool:
    """Check if a valid cache exists for the given audio file."""
    cache_path = _get_cache_path(audio_filepath)

    if not os.path.exists(cache_path):
        return False

    if not os.path.exists(audio_filepath):
        return False

    try:
        with open(cache_path, 'r') as f:
            data = json.load(f)

        if data.get("version") != 1:
            return False

        current_hash = _file_hash(audio_filepath)
        return data.get("audio_hash") == current_hash

    except Exception:
        return False


def clear_cache(audio_filepath: str) -> bool:
    """Delete the cache file for a given audio file."""
    cache_path = _get_cache_path(audio_filepath)
    if os.path.exists(cache_path):
        os.remove(cache_path)
        return True
    return False
