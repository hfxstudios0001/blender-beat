"""
BlenderBeat — Material creation helpers.

Wraps the shader_nodes module with higher-level functions
for creating materials from preset configurations.
"""

import bpy
from typing import Optional

from ..nodes.shader_nodes import (
    create_audio_reactive_material,
    setup_material_drivers,
    create_world_material,
)
from .presets import VisualPreset


def create_materials_from_preset(
    preset: VisualPreset,
) -> bpy.types.Material:
    """
    Create materials based on a visual preset.

    Returns the main material.
    """
    material = create_audio_reactive_material(
        name="BB_AudioMaterial",
        base_color=preset.base_color,
        emission_color=preset.emission_color,
        max_emission_strength=preset.max_emission,
    )

    # Create world
    create_world_material()

    return material


def apply_materials(
    obj: bpy.types.Object,
    material: bpy.types.Material,
):
    """Apply the material to the visualizer object and set up drivers."""
    # Assign material
    if len(obj.data.materials) == 0:
        obj.data.materials.append(material)
    else:
        obj.data.materials[0] = material

    # Set up audio drivers
    setup_material_drivers(obj, material)
