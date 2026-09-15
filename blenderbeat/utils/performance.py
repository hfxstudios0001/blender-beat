"""
BlenderBeat — Performance utilities.

Timing, memory tracking, and performance budgeting helpers.
"""

import time
import functools
from typing import Optional, Callable


class Timer:
    """Simple context-manager timer for profiling code blocks."""

    def __init__(self, label: str = "Operation"):
        self.label = label
        self.elapsed: float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self._start
        print(f"[BlenderBeat] {self.label}: {self.elapsed:.3f}s")


def timed(label: Optional[str] = None):
    """Decorator that prints execution time of a function."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _label = label or func.__name__
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            print(f"[BlenderBeat] {_label}: {elapsed:.3f}s")
            return result
        return wrapper
    return decorator


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def remap(
    value: float,
    in_min: float, in_max: float,
    out_min: float, out_max: float,
) -> float:
    """Remap a value from one range to another."""
    if in_max == in_min:
        return out_min
    t = (value - in_min) / (in_max - in_min)
    return out_min + t * (out_max - out_min)
