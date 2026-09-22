"""
BlenderBeat — Presets Package.

Registers all built-in presets in the PresetRegistry.
"""

from .base import BasePreset
from .registry import PresetRegistry
from .black_hole_tunnel import InfiniteBlackHoleTunnelPreset
from .cosmic_blossom import CosmicBlossomPreset
from .light_grid import InfiniteLightGridPreset
from .neon_city import NeonSignalCityPreset
from .pulse_tunnel import PulseTunnelPreset

# Register presets
PresetRegistry.register(InfiniteBlackHoleTunnelPreset)
PresetRegistry.register(CosmicBlossomPreset)
PresetRegistry.register(InfiniteLightGridPreset)
PresetRegistry.register(NeonSignalCityPreset)
PresetRegistry.register(PulseTunnelPreset)

__all__ = [
    "BasePreset",
    "PresetRegistry",
    "InfiniteBlackHoleTunnelPreset",
    "CosmicBlossomPreset",
    "InfiniteLightGridPreset",
    "NeonSignalCityPreset",
    "PulseTunnelPreset",
]
