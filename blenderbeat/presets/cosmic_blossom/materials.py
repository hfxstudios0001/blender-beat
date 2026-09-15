"""
BlenderBeat — Cosmic Blossom Materials.

Creates the high-end materials matching the reference image:
- Faceted translucent crystal glass petals with champagne tint, specular highlights, and internal reflections
- Brushed cosmic gold rim frame
- Obsidian mirror platform reflecting the flower and illuminated causeway
- Blinding white/golden energy core and animated energy veins
- Vertical celestial light beam
- Sparkling diamond shards
"""

import bpy
from typing import Dict, Any


def create_cosmic_blossom_materials(
    palette_name: str = "CELESTIAL_GOLD",
    palette: str = None,
) -> Dict[str, bpy.types.Material]:
    if palette is not None:
        palette_name = palette

    palettes = {
        'CELESTIAL_GOLD': {
            'crystal_tint': (1.0, 0.94, 0.84, 1.0),
            'gold_metal': (1.0, 0.82, 0.42, 1.0),
            'dark_metal': (0.02, 0.02, 0.03, 1.0),
            'energy_base': (1.0, 0.60, 0.18),
            'energy_core': (1.0, 0.98, 0.92),
            'mirror_color': (0.008, 0.008, 0.012, 1.0),
        },
        'CYBER_CYAN': {
            'crystal_tint': (0.85, 0.96, 1.0, 1.0),
            'gold_metal': (0.1, 0.85, 1.0, 1.0),
            'dark_metal': (0.02, 0.04, 0.06, 1.0),
            'energy_base': (0.0, 0.75, 1.0),
            'energy_core': (0.85, 1.0, 1.0),
            'mirror_color': (0.01, 0.02, 0.04, 1.0),
        },
        'AMETHYST_VOID': {
            'crystal_tint': (0.95, 0.85, 1.0, 1.0),
            'gold_metal': (0.88, 0.35, 0.95, 1.0),
            'dark_metal': (0.03, 0.02, 0.05, 1.0),
            'energy_base': (0.75, 0.05, 0.95),
            'energy_core': (1.0, 0.85, 1.0),
            'mirror_color': (0.02, 0.01, 0.03, 1.0),
        },
        'SOLAR_CRIMSON': {
            'crystal_tint': (1.0, 0.88, 0.82, 1.0),
            'gold_metal': (1.0, 0.45, 0.15, 1.0),
            'dark_metal': (0.05, 0.02, 0.02, 1.0),
            'energy_base': (1.0, 0.18, 0.02),
            'energy_core': (1.0, 0.92, 0.75),
            'mirror_color': (0.03, 0.01, 0.01, 1.0),
        },
        'ARCTIC_DIAMOND': {
            'crystal_tint': (0.92, 0.96, 1.0, 1.0),
            'gold_metal': (0.85, 0.92, 1.0, 1.0),
            'dark_metal': (0.03, 0.03, 0.04, 1.0),
            'energy_base': (0.45, 0.80, 1.0),
            'energy_core': (1.0, 1.0, 1.0),
            'mirror_color': (0.01, 0.01, 0.02, 1.0),
        },
    }
    p = palettes.get(palette_name, palettes['CELESTIAL_GOLD'])

    mats = {}
    mats['crystal'] = _create_crystal_petal_material("BB_Mat_BlossomCrystal", p['crystal_tint'], p['gold_metal'])
    mats['gold'] = _create_cosmic_metal_material("BB_Mat_BlossomGold", p['gold_metal'])
    mats['dark_frame'] = _create_dark_frame_material("BB_Mat_BlossomDarkFrame", p['dark_metal'])
    mats['energy_vein'] = _create_energy_vein_material("BB_Mat_BlossomVein", p['energy_base'], p['energy_core'])
    mats['core'] = _create_core_energy_material("BB_Mat_BlossomCore", p['energy_base'], p['energy_core'])
    mats['mirror'] = _create_mirror_platform_material("BB_Mat_BlossomMirror", p['mirror_color'])
    mats['beam'] = _create_light_beam_material("BB_Mat_BlossomBeam", p['energy_core'])
    mats['shard'] = _create_floating_shard_material("BB_Mat_BlossomShard", p['crystal_tint'], p['energy_core'])

    return mats


def _create_crystal_petal_material(name: str, tint: tuple, rim_color: tuple) -> bpy.types.Material:
    """
    Translucent glass crystal with subtle refraction, champagne tint,
    and delicate internal specular glints.
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()

    out = tree.nodes.new('ShaderNodeOutputMaterial')
    out.location = (900, 0)

    principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (500, 0)
    principled.inputs['Base Color'].default_value = tint
    principled.inputs['Metallic'].default_value = 0.05
    principled.inputs['Roughness'].default_value = 0.04
    principled.inputs['IOR'].default_value = 1.52

    if 'Transmission Weight' in principled.inputs:
        principled.inputs['Transmission Weight'].default_value = 0.82
    elif 'Transmission' in principled.inputs:
        principled.inputs['Transmission'].default_value = 0.82

    # Subtle fresnel edge emission to give crystal self-illumination matching the reference
    fresnel = tree.nodes.new('ShaderNodeFresnel')
    fresnel.location = (100, 200)
    fresnel.inputs['IOR'].default_value = 1.6

    emit_crystal = tree.nodes.new('ShaderNodeEmission')
    emit_crystal.location = (300, 200)
    emit_crystal.inputs['Color'].default_value = (1.0, 0.88, 0.65, 1.0)
    emit_crystal.inputs['Strength'].default_value = 0.5

    mix_shader = tree.nodes.new('ShaderNodeMixShader')
    mix_shader.location = (700, 0)
    tree.links.new(fresnel.outputs['Fac'], mix_shader.inputs['Fac'])
    tree.links.new(principled.outputs['BSDF'], mix_shader.inputs[1])
    tree.links.new(emit_crystal.outputs['Emission'], mix_shader.inputs[2])

    tree.links.new(mix_shader.outputs['Shader'], out.inputs['Surface'])
    return mat


def _create_cosmic_metal_material(name: str, metal_color: tuple) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()

    out = tree.nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)

    principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (250, 0)
    principled.inputs['Base Color'].default_value = metal_color
    principled.inputs['Metallic'].default_value = 1.0
    principled.inputs['Roughness'].default_value = 0.12

    tree.links.new(principled.outputs['BSDF'], out.inputs['Surface'])
    return mat


def _create_dark_frame_material(name: str, dark_color: tuple) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()

    out = tree.nodes.new('ShaderNodeOutputMaterial')
    out.location = (500, 0)

    principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (200, 0)
    principled.inputs['Base Color'].default_value = dark_color
    principled.inputs['Metallic'].default_value = 0.95
    principled.inputs['Roughness'].default_value = 0.22

    tree.links.new(principled.outputs['BSDF'], out.inputs['Surface'])
    return mat


def _create_energy_vein_material(
    name: str,
    base_color: tuple,
    core_color: tuple,
) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()

    out = tree.nodes.new('ShaderNodeOutputMaterial')
    out.location = (1100, 0)

    emission = tree.nodes.new('ShaderNodeEmission')
    emission.location = (800, 0)

    attr = tree.nodes.new('ShaderNodeAttribute')
    attr.location = (-400, 100)
    attr.attribute_name = "bb_petal_energy"
    attr.attribute_type = 'GEOMETRY'

    audio_val = tree.nodes.new('ShaderNodeValue')
    audio_val.name = "BB_AudioEmission"
    audio_val.label = "Audio Emission"
    audio_val.location = (-400, -100)
    audio_val.outputs[0].default_value = 1.0

    mult = tree.nodes.new('ShaderNodeMath')
    mult.location = (-150, 0)
    mult.operation = 'MULTIPLY'
    tree.links.new(attr.outputs['Fac'], mult.inputs[0])
    tree.links.new(audio_val.outputs[0], mult.inputs[1])

    pwr = tree.nodes.new('ShaderNodeMath')
    pwr.location = (50, 0)
    pwr.operation = 'POWER'
    pwr.inputs[1].default_value = 1.3
    tree.links.new(mult.outputs['Value'], pwr.inputs[0])

    ramp = tree.nodes.new('ShaderNodeValToRGB')
    ramp.location = (300, 100)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*base_color, 1.0)
    el_mid = ramp.color_ramp.elements.new(0.5)
    el_mid.color = (*core_color, 1.0)
    ramp.color_ramp.elements[-1].position = 1.0
    ramp.color_ramp.elements[-1].color = (1.0, 1.0, 1.0, 1.0)
    tree.links.new(pwr.outputs['Value'], ramp.inputs['Fac'])
    tree.links.new(ramp.outputs['Color'], emission.inputs['Color'])

    strength_scale = tree.nodes.new('ShaderNodeMath')
    strength_scale.location = (300, -100)
    strength_scale.operation = 'MULTIPLY'
    strength_scale.inputs[1].default_value = 12.0
    tree.links.new(pwr.outputs['Value'], strength_scale.inputs[0])

    strength_add = tree.nodes.new('ShaderNodeMath')
    strength_add.location = (500, -100)
    strength_add.operation = 'ADD'
    strength_add.inputs[1].default_value = 0.6
    tree.links.new(strength_scale.outputs['Value'], strength_add.inputs[0])
    tree.links.new(strength_add.outputs['Value'], emission.inputs['Strength'])

    tree.links.new(emission.outputs['Emission'], out.inputs['Surface'])
    return mat


def _create_core_energy_material(
    name: str,
    base_color: tuple,
    core_color: tuple,
) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()

    out = tree.nodes.new('ShaderNodeOutputMaterial')
    out.location = (800, 0)

    emission = tree.nodes.new('ShaderNodeEmission')
    emission.location = (500, 0)
    emission.inputs['Color'].default_value = (1.0, 0.96, 0.88, 1.0)

    audio_val = tree.nodes.new('ShaderNodeValue')
    audio_val.name = "BB_AudioEmission"
    audio_val.location = (0, 0)
    audio_val.outputs[0].default_value = 1.0

    strength = tree.nodes.new('ShaderNodeMath')
    strength.location = (250, 0)
    strength.operation = 'MULTIPLY'
    strength.inputs[1].default_value = 10.0
    tree.links.new(audio_val.outputs[0], strength.inputs[0])
    tree.links.new(strength.outputs['Value'], emission.inputs['Strength'])

    tree.links.new(emission.outputs['Emission'], out.inputs['Surface'])
    return mat


def _create_mirror_platform_material(name: str, mirror_color: tuple) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()

    out = tree.nodes.new('ShaderNodeOutputMaterial')
    out.location = (500, 0)

    principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (200, 0)
    principled.inputs['Base Color'].default_value = mirror_color
    principled.inputs['Metallic'].default_value = 0.95
    principled.inputs['Roughness'].default_value = 0.015
    principled.inputs['Specular IOR Level'].default_value = 1.0

    tree.links.new(principled.outputs['BSDF'], out.inputs['Surface'])
    return mat


def _create_light_beam_material(name: str, beam_color: tuple) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()

    out = tree.nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)

    emission = tree.nodes.new('ShaderNodeEmission')
    emission.location = (300, 0)
    emission.inputs['Color'].default_value = (*beam_color, 1.0)
    emission.inputs['Strength'].default_value = 6.0

    tree.links.new(emission.outputs['Emission'], out.inputs['Surface'])
    return mat


def _create_floating_shard_material(name: str, crystal_tint: tuple, core_color: tuple) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()

    out = tree.nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)

    emission = tree.nodes.new('ShaderNodeEmission')
    emission.location = (300, 0)
    emission.inputs['Color'].default_value = (*core_color, 1.0)
    emission.inputs['Strength'].default_value = 3.5

    tree.links.new(emission.outputs['Emission'], out.inputs['Surface'])
    return mat
