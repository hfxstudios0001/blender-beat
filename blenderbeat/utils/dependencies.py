"""
BlenderBeat — Dependency checking and installation.

Handles checking for optional dependencies (scipy, soundfile)
and auto-installing them into Blender's bundled Python if the user consents.
"""

import subprocess
import sys
import importlib
from typing import Optional, Tuple


# Cache availability checks so we don't re-probe every call
_dependency_cache: dict = {}


def is_available(module_name: str) -> bool:
    """Check if a Python module is importable."""
    if module_name in _dependency_cache:
        return _dependency_cache[module_name]

    try:
        importlib.import_module(module_name)
        _dependency_cache[module_name] = True
        return True
    except ImportError:
        _dependency_cache[module_name] = False
        return False


def install_package(package_name: str) -> Tuple[bool, str]:
    """
    Install a pip package into Blender's Python environment.

    Returns:
        (success: bool, message: str)
    """
    python_exe = sys.executable

    try:
        # Ensure pip is available
        subprocess.check_call(
            [python_exe, "-m", "ensurepip"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        pass  # ensurepip may already be set up

    try:
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", package_name, "--quiet"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            # Clear cache so the next is_available check sees the new module
            _dependency_cache.pop(package_name, None)
            return True, f"Successfully installed {package_name}"
        else:
            return False, f"pip install failed: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, f"Installation of {package_name} timed out (120s)"
    except Exception as e:
        return False, f"Installation error: {str(e)}"


def ensure_scipy() -> Tuple[bool, str]:
    """
    Ensure scipy is available. Install if missing.

    Returns:
        (available: bool, message: str)
    """
    if is_available("scipy"):
        return True, "scipy is already available"

    return install_package("scipy")


def get_analysis_backend() -> str:
    """
    Determine which audio analysis backend to use.

    Returns:
        'scipy' if scipy is available, 'numpy' otherwise.
    """
    if is_available("scipy"):
        return "scipy"
    return "numpy"


def check_all_dependencies() -> dict:
    """
    Check availability of all optional dependencies.

    Returns:
        Dictionary with dependency name → availability status.
    """
    deps = {
        "numpy": is_available("numpy"),       # Should always be True in Blender
        "scipy": is_available("scipy"),
        "soundfile": is_available("soundfile"),
    }
    return deps
