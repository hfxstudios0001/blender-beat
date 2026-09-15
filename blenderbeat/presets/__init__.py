"""
BlenderBeat — Presets Package.

Registers all built-in presets in the PresetRegistry.
"""

from .base import BasePreset
from .registry import PresetRegistry
from .black_hole_tunnel import InfiniteBlackHoleTunnelPreset
from .cosmic_blossom import CosmicBlossomPreset
from .light_grid import InfiniteLightGridPreset

# Register presets
PresetRegistry.register(InfiniteBlackHoleTunnelPreset)
PresetRegistry.register(CosmicBlossomPreset)
PresetRegistry.register(InfiniteLightGridPreset)

__all__ = [
    "BasePreset",
    "PresetRegistry",
    "InfiniteBlackHoleTunnelPreset",
    "CosmicBlossomPreset",
    "InfiniteLightGridPreset",
]
