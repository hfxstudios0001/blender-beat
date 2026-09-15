"""
BlenderBeat — Shader node tree builders.

Creates audio-reactive materials with emission, color cycling,
and procedural effects. Designed for both Eevee and Cycles.
"""

import bpy
import math
from typing import Optional, Tuple

from ..animation.baking import get_prop_name, create_driver


def _clear_shader_nodes(material: bpy.types.Material):
    """Remove all nodes from a material's node tree."""
    if material.node_tree is None:
        return
    for node in list(material.node_tree.nodes):
        material.node_tree.nodes.remove(node)


def create_audio_reactive_material(
    name: str = "BB_AudioMaterial",
    base_color: Tuple[float, float, float] = (0.0, 0.5, 1.0),
    emission_color: Tuple[float, float, float] = (0.0, 0.8, 1.0),
    max_emission_strength: float = 15.0,
) -> bpy.types.Material:
    """
    Create an audio-reactive emissive material.

    Features:
    - Base Principled BSDF with metallic finish
    - Emission driven by audio (bb_emission_strength)
    - Color gradient from base to emission color
    - Fresnel rim glow effect
    - Works in both Eevee and Cycles

    Args:
        name: Material name.
        base_color: RGB base color (0-1).
        emission_color: RGB emission color (0-1).
        max_emission_strength: Maximum emission brightness.

    Returns:
        The created material.
    """
    # Get or create material
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)

    mat.use_nodes = True
    _clear_shader_nodes(mat)

    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links

    # --- Material Output ---
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 0)

    # --- Principled BSDF ---
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (400, 100)
    principled.inputs['Base Color'].default_value = (*base_color, 1.0)
    principled.inputs['Metallic'].default_value = 0.8
    principled.inputs['Roughness'].default_value = 0.3
    principled.inputs['Specular IOR Level'].default_value = 0.8

    # --- Emission Shader ---
    emission = nodes.new('ShaderNodeEmission')
    emission.location = (400, -200)
    emission.inputs['Color'].default_value = (*emission_color, 1.0)
    emission.inputs['Strength'].default_value = 5.0

    # --- Add Shader (Principled + Emission) ---
    # Additive blending ensures high metallic specular reflections are preserved
    # while emission glows cleanly at wave crests
    add_shader = nodes.new('ShaderNodeAddShader')
    add_shader.location = (600, 0)

    links.new(principled.outputs['BSDF'], add_shader.inputs[0])
    links.new(emission.outputs['Emission'], add_shader.inputs[1])
    links.new(add_shader.outputs['Shader'], output.inputs['Surface'])

    # --- Fresnel for rim glow ---
    fresnel = nodes.new('ShaderNodeFresnel')
    fresnel.location = (200, -100)
    fresnel.inputs['IOR'].default_value = 1.5

    # Mix factor: blend between principled and emission based on fresnel + audio
    # Math: max(fresnel, audio_emission * 0.7)
    fresnel_mix = nodes.new('ShaderNodeMath')
    fresnel_mix.location = (400, -50)
    fresnel_mix.operation = 'MAXIMUM'
    links.new(fresnel.outputs['Fac'], fresnel_mix.inputs[0])
    fresnel_mix.inputs[1].default_value = 0.3  # Will be driven by audio


    # --- Color Ramp for gradient effect ---
    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (0, -300)

    # Set up a nice cyan → white gradient
    ramp = color_ramp.color_ramp
    ramp.elements[0].color = (*emission_color, 1.0)
    ramp.elements[0].position = 0.0

    # Brighter emission at high values
    bright_color = tuple(min(1.0, c * 1.5) for c in emission_color)
    ramp.elements[1].color = (*bright_color, 1.0)
    ramp.elements[1].position = 1.0

    # Connect ramp output to emission color
    links.new(color_ramp.outputs['Color'], emission.inputs['Color'])

    # --- Value node for audio input ---
    # This value will be driven by bb_emission_strength
    audio_value = nodes.new('ShaderNodeValue')
    audio_value.location = (-200, -200)
    audio_value.outputs[0].default_value = 0.5
    audio_value.label = "Audio Emission"
    audio_value.name = "BB_AudioEmission"

    # --- Per-Instance Stochastic Glow Attribute (Polyfjord Style) ---
    # Samples 'bb_glow' attribute stored on points/instances from Geometry Nodes
    attr_node = nodes.new('ShaderNodeAttribute')
    attr_node.location = (-400, -350)
    attr_node.attribute_name = "bb_glow"
    attr_node.attribute_type = 'GEOMETRY'

    # Polyfjord styling: non-glowing bars (bb_glow=0) remain dark metallic,
    # glowing bars ignite into intense emission.
    # total_emission = (audio_value * 0.05) + (attr.fac * 2.0)
    ambient_emission = nodes.new('ShaderNodeMath')
    ambient_emission.location = (-200, -200)
    ambient_emission.operation = 'MULTIPLY'
    ambient_emission.inputs[1].default_value = 0.05
    links.new(audio_value.outputs[0], ambient_emission.inputs[0])

    attr_mult = nodes.new('ShaderNodeMath')
    attr_mult.location = (-200, -350)
    attr_mult.operation = 'MULTIPLY'
    attr_mult.inputs[1].default_value = 2.5
    links.new(attr_node.outputs['Fac'], attr_mult.inputs[0])

    total_emission = nodes.new('ShaderNodeMath')
    total_emission.location = (0, -250)
    total_emission.operation = 'ADD'
    links.new(ambient_emission.outputs['Value'], total_emission.inputs[0])
    links.new(attr_mult.outputs['Value'], total_emission.inputs[1])

    # Audio value drives: emission strength, mix factor, and color ramp
    # Emission strength = total_emission * max_strength
    emission_multiply = nodes.new('ShaderNodeMath')
    emission_multiply.location = (200, -300)
    emission_multiply.operation = 'MULTIPLY'
    emission_multiply.inputs[1].default_value = max_emission_strength
    links.new(total_emission.outputs['Value'], emission_multiply.inputs[0])
    links.new(emission_multiply.outputs['Value'], emission.inputs['Strength'])

    # Drive fresnel mix intensity
    links.new(total_emission.outputs['Value'], fresnel_mix.inputs[1])

    # Drive color ramp position
    links.new(total_emission.outputs['Value'], color_ramp.inputs['Fac'])

    # Configure for Eevee compatibility
    _configure_eevee_settings(mat)

    print(f"[BlenderBeat] Material created: {name}")
    return mat


def setup_material_drivers(
    obj: bpy.types.Object,
    material: bpy.types.Material,
):
    """
    Connect baked audio properties on the object to the material's
    shader node inputs via drivers.
    """
    tree = material.node_tree
    if tree is None:
        return

    # Find the audio value node
    audio_node = tree.nodes.get("BB_AudioEmission")
    if audio_node is None:
        print("[BlenderBeat] Warning: BB_AudioEmission node not found in material")
        return

    # Drive the Value node output from bb_emission_strength
    prop_name = get_prop_name("emission_strength")
    if prop_name in obj:
        try:
            data_path = f'nodes["BB_AudioEmission"].outputs[0].default_value'

            # Remove existing driver
            try:
                tree.driver_remove(data_path)
            except Exception:
                pass

            driver_fc = tree.driver_add(data_path)
            driver = driver_fc.driver
            driver.type = 'SCRIPTED'
            driver.expression = 'var'

            var = driver.variables.new()
            var.name = "var"
            var.type = 'SINGLE_PROP'
            var.targets[0].id = obj
            var.targets[0].data_path = f'["{prop_name}"]'

            print(f"[BlenderBeat] Material driver: {prop_name} → emission")
        except Exception as e:
            print(f"[BlenderBeat] Material driver failed: {e}")


def _configure_eevee_settings(material: bpy.types.Material):
    """
    Configure material settings for optimal Eevee rendering.

    Sets blend mode, shadow mode, and other Eevee-specific properties.
    """
    # Eevee-specific settings (Blender 4.x+)
    try:
        material.surface_render_method = 'DITHERED'
    except (AttributeError, TypeError):
        pass

    try:
        material.use_backface_culling = False
    except (AttributeError, TypeError):
        pass


def create_world_material() -> bpy.types.World:
    """
    Create a dark world environment with audio-driven emission.

    Returns the world data-block.
    """
    world = bpy.data.worlds.get("BB_World")
    if world is None:
        world = bpy.data.worlds.new("BB_World")

    world.use_nodes = True
    tree = world.node_tree
    nodes = tree.nodes
    links = tree.links

    # Clear existing
    for node in list(nodes):
        nodes.remove(node)

    # World Output
    output = nodes.new('ShaderNodeOutputWorld')
    output.location = (400, 0)

    # Background shader
    background = nodes.new('ShaderNodeBackground')
    background.location = (200, 0)
    background.inputs['Color'].default_value = (0.0, 0.01, 0.02, 1.0)
    background.inputs['Strength'].default_value = 0.05

    links.new(background.outputs['Background'], output.inputs['Surface'])

    # Volume scatter for atmospheric effect (subtle fog)
    volume_scatter = nodes.new('ShaderNodeVolumeScatter')
    volume_scatter.location = (200, -200)
    volume_scatter.inputs['Color'].default_value = (0.1, 0.2, 0.4, 1.0)
    volume_scatter.inputs['Density'].default_value = 0.005
    volume_scatter.inputs['Anisotropy'].default_value = 0.3

    links.new(volume_scatter.outputs['Volume'], output.inputs['Volume'])

    bpy.context.scene.world = world
    print("[BlenderBeat] World material created")

    return world
