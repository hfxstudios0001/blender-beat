"""
BlenderBeat — Input validation utilities.

Validates audio files, numeric ranges, and Blender state
before operations proceed.
"""

import os
from typing import Tuple, Optional


# Supported audio formats and their expected extensions
SUPPORTED_AUDIO_EXTENSIONS = {'.wav', '.wave', '.mp3', '.flac', '.ogg'}
EXTENDED_AUDIO_EXTENSIONS = {'.wav', '.wave', '.mp3', '.flac', '.ogg'}
MP3_EXTENSIONS = {'.mp3'}

# Limits
MAX_AUDIO_DURATION_SECONDS = 3600  # 1 hour
MIN_AUDIO_DURATION_SECONDS = 1.0
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB
MIN_BPM = 30
MAX_BPM = 300
MIN_LOOP_BARS = 1
MAX_LOOP_BARS = 128
MIN_SEED = 0
MAX_SEED = 999999
MIN_COMPLEXITY = 0.0
MAX_COMPLEXITY = 1.0


def validate_audio_file(filepath: str) -> Tuple[bool, str]:
    """
    Validate that an audio file exists, is readable, and has a supported format.

    Returns:
        (valid: bool, message: str)
    """
    if not filepath:
        return False, "No audio file selected"

    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"

    if not os.path.isfile(filepath):
        return False, f"Path is not a file: {filepath}"

    ext = os.path.splitext(filepath)[1].lower()

    if ext not in SUPPORTED_AUDIO_EXTENSIONS:
        return False, (
            f"Unsupported format: {ext}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))}"
        )

    # Check file size
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return False, "Audio file is empty (0 bytes)"

    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        return False, f"File too large: {size_mb:.0f} MB (max {max_mb:.0f} MB)"

    return True, "Audio file is valid"


def validate_bpm(bpm: float) -> Tuple[bool, str]:
    """Validate BPM value."""
    if bpm < MIN_BPM or bpm > MAX_BPM:
        return False, f"BPM must be between {MIN_BPM} and {MAX_BPM}, got {bpm}"
    return True, "BPM is valid"


def validate_loop_bars(bars: int) -> Tuple[bool, str]:
    """Validate loop bar count."""
    if bars < MIN_LOOP_BARS or bars > MAX_LOOP_BARS:
        return False, f"Loop bars must be between {MIN_LOOP_BARS} and {MAX_LOOP_BARS}"
    return True, "Loop bars valid"


def validate_seed(seed: int) -> Tuple[bool, str]:
    """Validate random seed."""
    if seed < MIN_SEED or seed > MAX_SEED:
        return False, f"Seed must be between {MIN_SEED} and {MAX_SEED}"
    return True, "Seed valid"


def validate_render_settings(
    resolution_x: int,
    resolution_y: int,
    fps: int,
) -> Tuple[bool, str]:
    """Validate render settings."""
    if resolution_x < 64 or resolution_x > 7680:
        return False, f"Resolution X must be between 64 and 7680, got {resolution_x}"
    if resolution_y < 64 or resolution_y > 4320:
        return False, f"Resolution Y must be between 64 and 4320, got {resolution_y}"
    if fps < 1 or fps > 120:
        return False, f"FPS must be between 1 and 120, got {fps}"
    return True, "Render settings valid"


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to MM:SS or HH:MM:SS."""
    if seconds < 0:
        return "0:00"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes >= 60:
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
