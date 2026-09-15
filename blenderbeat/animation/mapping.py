"""
BlenderBeat — Audio-to-Visual mapping definitions.

Defines which audio signals can drive which visual parameters,
and the default mappings for Phase 1's Audio Sphere preset.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


# Available audio source signals
AUDIO_SOURCES = [
    ("bass", "Bass", "Low frequency energy (60-250 Hz)"),
    ("sub_bass", "Sub Bass", "Deep low frequency energy (20-60 Hz)"),
    ("kick", "Kick", "Kick drum approximation"),
    ("snare", "Snare", "Snare drum approximation"),
    ("low_mid", "Low Mid", "Low-mid frequency energy (250-500 Hz)"),
    ("mid", "Mid", "Mid frequency energy (500-2000 Hz)"),
    ("high_mid", "High Mid", "High-mid frequency energy (2-4 kHz)"),
    ("treble", "Treble", "High frequency energy (4-20 kHz)"),
    ("energy", "Energy", "Overall combined energy"),
    ("rms", "RMS", "Root mean square loudness"),
    ("onset_strength", "Onset", "Transient/attack strength"),
    ("spectral_centroid", "Brightness", "Spectral centroid (perceived brightness)"),
]

# Available visual target parameters
VISUAL_TARGETS = [
    ("scale", "Scale", "Object/instance scale"),
    ("scale_x", "Scale X", "Scale on X axis only"),
    ("scale_y", "Scale Y", "Scale on Y axis only"),
    ("scale_z", "Scale Z", "Scale on Z axis only"),
    ("rotation_z", "Rotation Z", "Rotation around Z axis"),
    ("emission_strength", "Emission", "Material emission brightness"),
    ("emission_color_shift", "Color Shift", "Hue shift on emission color"),
    ("displacement", "Displacement", "Geometry displacement amount"),
    ("camera_shake", "Camera Shake", "Camera shake intensity"),
    ("camera_zoom", "Camera Zoom", "Camera focal length / distance"),
    ("light_intensity", "Light Intensity", "Key light brightness"),
    ("world_emission", "World Glow", "World environment emission"),
    ("roughness", "Roughness", "Material roughness"),
    ("metallic", "Metallic", "Material metallic value"),
]


@dataclass
class AudioMapping:
    """
    A single audio-to-visual mapping.

    Defines how an audio signal drives a visual parameter
    through a processing chain.
    """
    source: str = "bass"          # Audio signal name
    target: str = "scale"         # Visual parameter name
    strength: float = 1.0         # Mapping intensity (multiplier)
    smooth_attack: float = 0.4    # Attack speed (0-1)
    smooth_release: float = 0.1   # Release speed (0-1)
    remap_min: float = 0.0        # Output minimum
    remap_max: float = 1.0        # Output maximum
    spring_enabled: bool = False  # Use spring dynamics
    spring_stiffness: float = 0.3
    spring_damping: float = 0.7
    power: float = 1.0            # Power curve exponent
    invert: bool = False          # Invert the signal


@dataclass
class MappingPreset:
    """
    A collection of audio mappings that define the full
    audio-visual relationship for a visualizer.
    """
    name: str = "Default"
    mappings: List[AudioMapping] = field(default_factory=list)


def get_default_audio_sphere_mappings() -> MappingPreset:
    """
    Default audio mapping preset for the Audio Sphere visualizer.

    Creates a musically rich mapping where:
    - Bass drives radial scale (bars extend on bass hits)
    - Kick adds camera shake
    - Mid drives emission glow
    - Treble drives rotation
    - Energy drives world glow
    - Onset drives light flashes
    """
    return MappingPreset(
        name="Audio Sphere",
        mappings=[
            # Bass → radial bar scale (main visual driver)
            AudioMapping(
                source="bass",
                target="scale",
                strength=1.0,
                smooth_attack=0.5,
                smooth_release=0.08,
                remap_min=0.2,
                remap_max=1.0,
                spring_enabled=True,
                spring_stiffness=0.4,
                spring_damping=0.65,
                power=1.5,
            ),
            # Kick → camera shake
            AudioMapping(
                source="kick",
                target="camera_shake",
                strength=0.6,
                smooth_attack=0.8,
                smooth_release=0.05,
                remap_min=0.0,
                remap_max=0.5,
            ),
            # Kick/Onset → camera zoom punch (Polyfjord beat zoom)
            AudioMapping(
                source="kick",
                target="camera_zoom",
                strength=1.0,
                smooth_attack=0.9,
                smooth_release=0.08,
                remap_min=0.0,
                remap_max=1.0,
                spring_enabled=True,
                spring_stiffness=0.5,
                spring_damping=0.6,
            ),
            # Mid → emission glow
            AudioMapping(
                source="mid",
                target="emission_strength",
                strength=1.0,
                smooth_attack=0.3,
                smooth_release=0.12,
                remap_min=0.1,
                remap_max=1.0,
            ),
            # Treble → rotation
            AudioMapping(
                source="treble",
                target="rotation_z",
                strength=0.8,
                smooth_attack=0.2,
                smooth_release=0.15,
                remap_min=0.0,
                remap_max=0.5,
                spring_enabled=True,
                spring_stiffness=0.2,
                spring_damping=0.8,
            ),
            # Energy → world brightness
            AudioMapping(
                source="energy",
                target="world_emission",
                strength=0.5,
                smooth_attack=0.15,
                smooth_release=0.08,
                remap_min=0.02,
                remap_max=0.3,
            ),
            # Onset → light flash
            AudioMapping(
                source="onset_strength",
                target="light_intensity",
                strength=1.0,
                smooth_attack=0.9,
                smooth_release=0.04,
                remap_min=0.3,
                remap_max=1.0,
                power=2.0,
            ),
        ],
    )


def get_mapping_by_target(
    preset: MappingPreset,
    target: str,
) -> Optional[AudioMapping]:
    """Find a mapping by its target parameter name."""
    for m in preset.mappings:
        if m.target == target:
            return m
    return None


def get_mappings_by_source(
    preset: MappingPreset,
    source: str,
) -> List[AudioMapping]:
    """Find all mappings using a specific audio source."""
    return [m for m in preset.mappings if m.source == source]
