"""
BlenderBeat — Audio file loader.

Loads WAV (and optionally FLAC/OGG via soundfile) audio files
into numpy arrays for analysis. Handles format detection,
channel conversion, and normalization.
"""

import os
import wave
import struct
import numpy as np
from typing import Tuple, Optional

from ..utils.performance import Timer
from .utils import to_mono, normalize_audio


class AudioLoadError(Exception):
    """Raised when audio loading fails."""
    pass


def load_wav_stdlib(filepath: str) -> Tuple[np.ndarray, int]:
    """
    Load a WAV file using Python's stdlib wave module.

    Returns:
        (audio_data, sample_rate): mono float32 audio and sample rate.
    """
    try:
        with wave.open(filepath, 'rb') as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()

            if n_frames == 0:
                raise AudioLoadError("WAV file contains no audio frames")

            raw_data = wf.readframes(n_frames)
    except wave.Error as e:
        raise AudioLoadError(f"Cannot read WAV file: {e}")

    # Convert raw bytes to numpy array based on sample width
    if sample_width == 1:
        # 8-bit unsigned
        audio = np.frombuffer(raw_data, dtype=np.uint8)
    elif sample_width == 2:
        # 16-bit signed
        audio = np.frombuffer(raw_data, dtype=np.int16)
    elif sample_width == 3:
        # 24-bit signed — no native numpy dtype, unpack manually
        n_samples = len(raw_data) // 3
        audio = np.zeros(n_samples, dtype=np.int32)
        for i in range(n_samples):
            # Little-endian 24-bit to 32-bit
            b = raw_data[i * 3:(i + 1) * 3]
            value = int.from_bytes(b, byteorder='little', signed=True)
            audio[i] = value
    elif sample_width == 4:
        # 32-bit signed
        audio = np.frombuffer(raw_data, dtype=np.int32)
    else:
        raise AudioLoadError(f"Unsupported sample width: {sample_width} bytes")

    # Reshape multi-channel audio
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels)

    # Convert to mono float32 [-1, 1]
    audio = to_mono(audio)
    audio = normalize_audio(audio)

    return audio, sample_rate


def load_wav_scipy(filepath: str) -> Tuple[np.ndarray, int]:
    """
    Load a WAV file using scipy.io.wavfile (if available).
    Handles more edge cases than stdlib wave.

    Returns:
        (audio_data, sample_rate): mono float32 audio and sample rate.
    """
    try:
        from scipy.io import wavfile
    except ImportError:
        raise AudioLoadError("scipy is not available; falling back to stdlib")

    try:
        sample_rate, audio = wavfile.read(filepath)
    except Exception as e:
        raise AudioLoadError(f"scipy could not read WAV: {e}")

    if audio.size == 0:
        raise AudioLoadError("WAV file contains no audio data")

    audio = to_mono(audio)
    audio = normalize_audio(audio)

    return audio, sample_rate


def load_audio_aud(filepath: str) -> Tuple[np.ndarray, int]:
    """
    Load an audio file (MP3, WAV, FLAC, OGG, etc.) using Blender's built-in aud module.
    """
    try:
        import aud
    except ImportError:
        raise AudioLoadError("Blender 'aud' module is not available")

    try:
        snd = aud.Sound(filepath)
        specs = snd.specs
        sample_rate = int(specs[0])
        raw_data = snd.data()
        if raw_data is None or len(raw_data) == 0:
            raise AudioLoadError(f"Audio file '{os.path.basename(filepath)}' contains no data")

        # Convert to mono float32
        audio = to_mono(raw_data)
        audio = normalize_audio(audio)
        return audio, sample_rate
    except Exception as e:
        raise AudioLoadError(f"Failed to read audio via Blender aud module: {e}")


def load_audio(filepath: str) -> Tuple[np.ndarray, int]:
    """
    Load an audio file, trying the best available backend.

    Supports: WAV, MP3, FLAC, OGG, etc.

    Attempts in order:
        1. Blender's built-in 'aud' engine (native support for MP3, WAV, FLAC, OGG)
        2. scipy.io.wavfile (fast WAV fallback)
        3. stdlib wave module (pure Python fallback)

    Returns:
        (audio_data, sample_rate): mono float32 normalized audio.

    Raises:
        AudioLoadError: If the file cannot be loaded.
    """
    if not os.path.exists(filepath):
        raise AudioLoadError(f"File not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()

    with Timer("Audio loading"):
        # 1. Try Blender's built-in aud engine (supports MP3, WAV, FLAC, OGG, etc.)
        try:
            audio, sr = load_audio_aud(filepath)
            print(f"[BlenderBeat] Loaded via aud: {len(audio)} samples, {sr} Hz ({ext})")
            return audio, sr
        except Exception as e:
            if ext in ('.mp3', '.flac', '.ogg'):
                raise AudioLoadError(f"Could not load {ext} file: {e}")

        # 2. Try scipy (for WAV)
        try:
            audio, sr = load_wav_scipy(filepath)
            print(f"[BlenderBeat] Loaded via scipy: {len(audio)} samples, {sr} Hz")
            return audio, sr
        except (AudioLoadError, Exception):
            pass

        # 3. Fall back to stdlib (for WAV)
        try:
            audio, sr = load_wav_stdlib(filepath)
            print(f"[BlenderBeat] Loaded via stdlib: {len(audio)} samples, {sr} Hz")
            return audio, sr
        except AudioLoadError:
            raise
        except Exception as e:
            raise AudioLoadError(f"Failed to load audio: {e}")


def get_audio_info(filepath: str) -> dict:
    """
    Get basic audio file metadata without loading full audio when possible.

    Returns dict with: channels, sample_rate, sample_width, n_frames, duration, file_size
    """
    if not os.path.exists(filepath):
        return {"error": f"File not found: {filepath}"}

    ext = os.path.splitext(filepath)[1].lower()

    # Try Blender aud module first (supports MP3, WAV, FLAC, OGG, etc.)
    try:
        import aud
        snd = aud.Sound(filepath)
        specs = snd.specs
        sample_rate = int(specs[0])
        n_channels = int(specs[1])
        length_frames = getattr(snd, 'length', 0)
        duration = (length_frames / sample_rate) if sample_rate > 0 else 0.0
        return {
            "channels": n_channels,
            "sample_rate": sample_rate,
            "sample_width": 2,
            "n_frames": length_frames,
            "duration": duration,
            "file_size": os.path.getsize(filepath),
        }
    except Exception:
        pass

    # Fallback to stdlib wave for WAV
    if ext in ('.wav', '.wave'):
        try:
            with wave.open(filepath, 'rb') as wf:
                return {
                    "channels": wf.getnchannels(),
                    "sample_rate": wf.getframerate(),
                    "sample_width": wf.getsampwidth(),
                    "n_frames": wf.getnframes(),
                    "duration": wf.getnframes() / wf.getframerate(),
                    "file_size": os.path.getsize(filepath),
                }
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Unsupported audio format: {ext}"}
