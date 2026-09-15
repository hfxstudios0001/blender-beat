"""
BlenderBeat — Preset definitions.

Phase 1 stub: defines the preset structure and the
Audio Sphere preset. Phase 3 will expand this with
save/load, multiple categories, and user presets.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

from ..animation.mapping import MappingPreset, get_default_audio_sphere_mappings


@dataclass
class VisualPreset:
    """
    Defines a complete visual configuration.

    A preset combines:
    - Geometry type and parameters
    - Material settings
    - Lighting settings
    - Camera settings
    - Default audio mappings
    """
    name: str = "Audio Sphere"
    description: str = ""
    category: str = "Abstract"

    # Geometry
    geometry_type: str = "audio_sphere"
    subdivisions: int = 3
    sphere_radius: float = 2.0
    bar_base_scale: float = 0.03
    bar_max_length: float = 2.0
    variation: float = 0.3

    # Material
    base_color: tuple = (0.0, 0.3, 0.6)
    emission_color: tuple = (0.0, 0.7, 1.0)
    max_emission: float = 15.0

    # Camera
    camera_distance: float = 8.0
    camera_height: float = 3.0
    camera_orbit_speed: float = 1.0
    camera_fov: float = 50.0

    # Lighting
    key_color: tuple = (0.6, 0.8, 1.0)
    fill_color: tuple = (0.2, 0.1, 0.4)
    rim_color: tuple = (1.0, 0.3, 0.1)
    key_intensity: float = 500.0

    # Audio mappings
    mapping_preset: Optional[MappingPreset] = None

    def get_mappings(self) -> MappingPreset:
        """Get the audio mapping preset for this visual."""
        if self.mapping_preset is not None:
            return self.mapping_preset
        return get_default_audio_sphere_mappings()


# --- Built-in Presets ---

PRESET_AUDIO_SPHERE = VisualPreset(
    name="Audio Sphere",
    description="Radial bars on an icosphere, reacting to bass with glow and rotation",
    category="Abstract",
    geometry_type="audio_sphere",
    subdivisions=3,
    sphere_radius=2.0,
    bar_base_scale=0.03,
    bar_max_length=2.0,
    variation=0.3,
    base_color=(0.02, 0.03, 0.05),
    emission_color=(0.0, 0.85, 1.0),
    max_emission=30.0,
    camera_distance=8.0,
    camera_height=3.0,
    camera_orbit_speed=1.0,
    camera_fov=50.0,
    key_color=(0.6, 0.8, 1.0),
    fill_color=(0.2, 0.1, 0.4),
    rim_color=(1.0, 0.3, 0.1),
    key_intensity=500.0,
)

PRESET_QUANTUM_FIELD = VisualPreset(
    name="Quantum Field",
    description="High-density organic wave field inspired by Eduard OV: luminous particles, harmonic concentric ripples, and macro bokeh",
    category="Cinematic Particles",
    geometry_type="quantum_field",
    subdivisions=4,
    sphere_radius=8.0,
    bar_base_scale=0.007,
    bar_max_length=1.5,
    variation=0.5,
    base_color=(0.008, 0.012, 0.02),
    emission_color=(0.6, 0.85, 1.0),
    max_emission=0.15,
    camera_distance=2.4,
    camera_height=0.42,
    camera_orbit_speed=0.2,
    camera_fov=52.0,
    key_color=(0.8, 0.95, 1.0),
    fill_color=(0.1, 0.2, 0.5),
    rim_color=(0.5, 0.85, 1.0),
    key_intensity=25.0,
)


PRESET_BLACK_HOLE_TUNNEL = VisualPreset(
    name="Infinite Black Hole Tunnel",
    description="Gigantic mechanical corridor with amber LED pulse rings leading to a black hole",
    category="Sci-Fi Tunnel",
    geometry_type="black_hole_tunnel",
    subdivisions=3,
    sphere_radius=4.2,
    bar_base_scale=0.03,
    bar_max_length=2.0,
    variation=0.3,
    base_color=(0.015, 0.018, 0.025),
    emission_color=(1.0, 0.45, 0.02),
    max_emission=30.0,
    camera_distance=0.0,
    camera_height=0.0,
    camera_orbit_speed=0.0,
    camera_fov=75.0,
    key_color=(1.0, 0.5, 0.1),
    fill_color=(0.1, 0.05, 0.02),
    rim_color=(1.0, 0.8, 0.4),
    key_intensity=120.0,
)


PRESET_COSMIC_BLOSSOM = VisualPreset(
    name="Cosmic Blossom",
    description="Multilayered alien cosmic flower organism with energy wave propagation and reflective temple environment",
    category="Sci-Fi Organism",
    geometry_type="cosmic_blossom",
    subdivisions=3,
    sphere_radius=3.5,
    bar_base_scale=0.03,
    bar_max_length=2.0,
    variation=0.3,
    base_color=(0.02, 0.02, 0.03),
    emission_color=(1.0, 0.78, 0.38),
    max_emission=45.0,
    camera_distance=0.0,
    camera_height=0.0,
    camera_orbit_speed=0.0,
    camera_fov=65.0,
    key_color=(1.0, 0.85, 0.5),
    fill_color=(0.05, 0.08, 0.15),
    rim_color=(1.0, 0.7, 0.3),
    key_intensity=150.0,
)


def get_preset(name: str) -> Optional[VisualPreset]:
    """Get a preset by name."""
    presets = {
        "Cosmic Blossom": PRESET_COSMIC_BLOSSOM,
        "Infinite Black Hole Tunnel": PRESET_BLACK_HOLE_TUNNEL,
        "Audio Sphere": PRESET_AUDIO_SPHERE,
        "Quantum Field": PRESET_QUANTUM_FIELD,
    }
    return presets.get(name)


def get_preset_names() -> List[str]:
    """Get list of available preset names."""
    return ["Cosmic Blossom", "Infinite Black Hole Tunnel", "Quantum Field", "Audio Sphere"]


def get_presets_by_category() -> Dict[str, List[str]]:
    """Get presets organized by category."""
    return {
        "Sci-Fi Organism": ["Cosmic Blossom"],
        "Sci-Fi Tunnel": ["Infinite Black Hole Tunnel"],
        "Cinematic Particles": ["Quantum Field"],
        "Abstract": ["Audio Sphere"],
    }
