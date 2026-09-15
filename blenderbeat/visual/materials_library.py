"""
BlenderBeat — Reusable Procedural Materials Library.

Provides production-grade shader materials for sci-fi, industrial,
and cinematic visualizers:
- MAT_DARK_METAL: Deep gunmetal brushed chrome with micro-roughness
- MAT_CHROME: Ultra-reflective mirror chrome
- MAT_LED_AMBER: Intense warm amber/gold emission with core bloom
- MAT_LED_WHITE: High-intensity daylight white LED emission
- MAT_VOID_BLACK_HOLE: Pure zero-albedo light-absorbing singularity shader
"""

import bpy
from typing import Tuple


def create_dark_metal_material(name: str = "BB_Mat_DarkMetal") -> bpy.types.Material:
    """Glossy dark gunmetal/carbon with procedural micro-noise roughness."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)

    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (200, 0)
    principled.inputs['Base Color'].default_value = (0.008, 0.009, 0.012, 1.0)
    principled.inputs['Metallic'].default_value = 0.96
    principled.inputs['Roughness'].default_value = 0.20
    principled.inputs['Specular IOR Level'].default_value = 0.95

    # Micro noise on roughness
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-200, -100)
    noise.inputs['Scale'].default_value = 45.0
    noise.inputs['Detail'].default_value = 8.0
    noise.inputs['Roughness'].default_value = 0.7

    map_range = nodes.new('ShaderNodeMapRange')
    map_range.location = (0, -100)
    map_range.inputs['From Min'].default_value = 0.0
    map_range.inputs['From Max'].default_value = 1.0
    map_range.inputs['To Min'].default_value = 0.15
    map_range.inputs['To Max'].default_value = 0.35
    links.new(noise.outputs['Fac'], map_range.inputs['Value'])
    links.new(map_range.outputs['Result'], principled.inputs['Roughness'])

    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    return mat


def create_chrome_material(name: str = "BB_Mat_Chrome") -> bpy.types.Material:
    """Mirror-like chrome with faint cool tint."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)

    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (100, 0)
    principled.inputs['Base Color'].default_value = (0.92, 0.94, 0.98, 1.0)
    principled.inputs['Metallic'].default_value = 1.0
    principled.inputs['Roughness'].default_value = 0.03
    principled.inputs['Specular IOR Level'].default_value = 1.0

    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    return mat


def create_amber_led_material(
    name: str = "BB_Mat_AmberLED",
    color_mode: str = "SPECTRUM",
    custom_color: Tuple[float, float, float] = (0.0, 0.8, 1.0),
    min_glow: float = 0.02,
    peak_emission: float = 35.0,
) -> bpy.types.Material:
    """
    ASUS Aura Sync inspired music-reactive LED emission shader.

    Features:
    1. Multi-Color Aura Sync Modes:
       - 'SPECTRUM': Flowing rainbow chromatic wave using HSV Hue node
       - 'RED': Deep crimson into blinding white-hot laser core
       - 'CYAN': Cyberpunk electric cyan into white core
       - 'VIOLET': Neon synthwave violet into hot pink/white
       - 'AMBER': Warm classic industrial gold/amber
       - 'WHITE': Pure icy arctic diamond white
       - 'CUSTOM': User custom RGB color
    2. Dynamic Opacity / Beat Reactivity:
       - Resting rings drop smoothly to min_glow (e.g. 0.02, nearly black)
       - Kick/bass hits trigger explosive bloom up to peak_emission (e.g. 35.0)
    3. Uses 'bb_ring_glow', 'bb_ring_phase', and 'bb_bar_flicker' Geometry attributes.
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (1400, 0)

    emission = nodes.new('ShaderNodeEmission')
    emission.location = (1100, 0)

    # ── Per-Ring Attribute Inputs (GEOMETRY domain for realized instances) ─
    attr_glow = nodes.new('ShaderNodeAttribute')
    attr_glow.location = (-800, 200)
    attr_glow.attribute_name = "bb_ring_glow"
    attr_glow.attribute_type = 'GEOMETRY'

    attr_phase = nodes.new('ShaderNodeAttribute')
    attr_phase.location = (-800, 0)
    attr_phase.attribute_name = "bb_ring_phase"
    attr_phase.attribute_type = 'GEOMETRY'

    attr_flicker = nodes.new('ShaderNodeAttribute')
    attr_flicker.location = (-800, -200)
    attr_flicker.attribute_name = "bb_bar_flicker"
    attr_flicker.attribute_type = 'GEOMETRY'

    # Global Audio Emission Baseline (driven by bb_emission_strength)
    audio_val = nodes.new('ShaderNodeValue')
    audio_val.location = (-800, -400)
    audio_val.name = "BB_AudioEmission"
    audio_val.label = "Audio Emission"
    audio_val.outputs[0].default_value = 1.0

    # ── Combine: shockwave glow + random bar flicker ───────────────────
    glow_max = nodes.new('ShaderNodeMath')
    glow_max.location = (-550, 100)
    glow_max.operation = 'MAXIMUM'
    links.new(attr_glow.outputs['Fac'], glow_max.inputs[0])
    links.new(attr_flicker.outputs['Fac'], glow_max.inputs[1])

    # Dynamic Audio Energy (energy = max(glow, flicker) * global_audio)
    combined_energy = nodes.new('ShaderNodeMath')
    combined_energy.location = (-350, 50)
    combined_energy.operation = 'MULTIPLY'
    links.new(glow_max.outputs['Value'], combined_energy.inputs[0])
    links.new(audio_val.outputs[0], combined_energy.inputs[1])

    # Nonlinear contrast curve: energy^1.8 (quiet parts drop to near zero, beats pop)
    contrast_pow = nodes.new('ShaderNodeMath')
    contrast_pow.location = (-150, 50)
    contrast_pow.operation = 'POWER'
    contrast_pow.inputs[1].default_value = 1.8
    links.new(combined_energy.outputs['Value'], contrast_pow.inputs[0])

    # ── Aura Sync Color Pipeline ──────────────────────────────────────
    if color_mode == 'SPECTRUM':
        # Rainbow spectrum traveling down tunnel:
        # 3.0 full chromatic loops from front to back of corridor
        phase_mult = nodes.new('ShaderNodeMath')
        phase_mult.location = (-350, -150)
        phase_mult.operation = 'MULTIPLY'
        phase_mult.inputs[1].default_value = 3.0
        links.new(attr_phase.outputs['Fac'], phase_mult.inputs[0])

        # Audio beat hue shift: beat pulses shift the entire color spectrum forward
        glow_hue = nodes.new('ShaderNodeMath')
        glow_hue.location = (-350, -300)
        glow_hue.operation = 'MULTIPLY'
        glow_hue.inputs[1].default_value = 0.5
        links.new(contrast_pow.outputs['Value'], glow_hue.inputs[0])

        hue_add = nodes.new('ShaderNodeMath')
        hue_add.location = (-150, -200)
        hue_add.operation = 'ADD'
        links.new(phase_mult.outputs['Value'], hue_add.inputs[0])
        links.new(glow_hue.outputs['Value'], hue_add.inputs[1])

        # Modulo 1.0 (seamless color loop)
        hue_mod = nodes.new('ShaderNodeMath')
        hue_mod.location = (50, -200)
        hue_mod.operation = 'MODULO'
        hue_mod.inputs[1].default_value = 1.0
        links.new(hue_add.outputs['Value'], hue_mod.inputs[0])

        # HSV to RGB (Hue, Saturation=1.0, Value=1.0)
        hsv_node = nodes.new('ShaderNodeCombineColor')
        hsv_node.mode = 'HSV'
        hsv_node.location = (250, -200)
        hsv_node.inputs['Red'].default_value = 0.0     # Hue
        hsv_node.inputs['Green'].default_value = 1.0   # Full vivid saturation
        hsv_node.inputs['Blue'].default_value = 1.0    # Full brightness
        links.new(hue_mod.outputs['Value'], hsv_node.inputs['Red'])

        # White core blend: only blend to white on top 20% of beat peak
        core_sub = nodes.new('ShaderNodeMath')
        core_sub.location = (250, 50)
        core_sub.operation = 'SUBTRACT'
        core_sub.inputs[1].default_value = 0.65
        links.new(contrast_pow.outputs['Value'], core_sub.inputs[0])

        core_fac = nodes.new('ShaderNodeMath')
        core_fac.location = (450, 50)
        core_fac.operation = 'MULTIPLY'
        core_fac.inputs[1].default_value = 2.85  # (1.0 - 0.65) * 2.85 ≈ 1.0
        links.new(core_sub.outputs['Value'], core_fac.inputs[0])

        core_clamp = nodes.new('ShaderNodeClamp')
        core_clamp.location = (650, 50)
        core_clamp.inputs['Min'].default_value = 0.0
        core_clamp.inputs['Max'].default_value = 0.8
        links.new(core_fac.outputs['Value'], core_clamp.inputs['Value'])

        core_mix = nodes.new('ShaderNodeMix')
        core_mix.data_type = 'RGBA'
        core_mix.location = (850, -100)
        core_mix.inputs['A'].default_value = (1.0, 1.0, 1.0, 1.0)
        core_mix.inputs['B'].default_value = (1.0, 1.0, 1.0, 1.0)  # White laser core
        links.new(hsv_node.outputs['Color'], core_mix.inputs['A'])
        links.new(core_clamp.outputs['Result'], core_mix.inputs['Factor'])
        links.new(core_mix.outputs['Result'], emission.inputs['Color'])

    else:
        # Curated palette presets
        palette_map = {
            'RED': ((0.95, 0.02, 0.02), (1.0, 0.35, 0.15), (1.0, 0.95, 0.90)),
            'CYAN': ((0.01, 0.75, 1.0), (0.35, 0.95, 1.0), (0.95, 1.0, 1.0)),
            'VIOLET': ((0.65, 0.02, 0.98), (0.95, 0.20, 0.85), (1.0, 0.90, 1.0)),
            'AMBER': ((1.0, 0.32, 0.01), (1.0, 0.65, 0.08), (1.0, 0.92, 0.55)),
            'WHITE': ((0.55, 0.75, 1.0), (0.85, 0.92, 1.0), (1.0, 1.0, 1.0)),
            'CUSTOM': (
                (custom_color[0] * 0.7, custom_color[1] * 0.7, custom_color[2] * 0.7),
                (custom_color[0], custom_color[1], custom_color[2]),
                (1.0, 1.0, 1.0),
            ),
        }
        base_c, mid_c, core_c = palette_map.get(color_mode, palette_map['AMBER'])

        color_ramp = nodes.new('ShaderNodeValToRGB')
        color_ramp.location = (250, 150)
        ramp = color_ramp.color_ramp
        ramp.elements[0].color = (*base_c, 1.0)
        ramp.elements[0].position = 0.0
        mid_el = ramp.elements.new(0.45)
        mid_el.color = (*mid_c, 1.0)
        ramp.elements[-1].color = (*core_c, 1.0)
        ramp.elements[-1].position = 1.0

        links.new(contrast_pow.outputs['Value'], color_ramp.inputs['Fac'])
        links.new(color_ramp.outputs['Color'], emission.inputs['Color'])

    # ── Emission Strength / Opacity Control ───────────────────────────
    # Strength = min_glow + (contrast_pow * (peak_emission - min_glow))
    range_span = max(peak_emission - min_glow, 1.0)
    glow_scaler = nodes.new('ShaderNodeMath')
    glow_scaler.location = (400, -300)
    glow_scaler.operation = 'MULTIPLY'
    glow_scaler.inputs[1].default_value = range_span
    links.new(contrast_pow.outputs['Value'], glow_scaler.inputs[0])

    strength_add = nodes.new('ShaderNodeMath')
    strength_add.location = (650, -300)
    strength_add.operation = 'ADD'
    strength_add.inputs[1].default_value = min_glow
    links.new(glow_scaler.outputs['Value'], strength_add.inputs[0])

    links.new(strength_add.outputs['Value'], emission.inputs['Strength'])

    # Output to surface
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    return mat


def create_black_hole_void_material(name: str = "BB_Mat_BlackHoleVoid") -> bpy.types.Material:
    """
    Pure light-absorbing black hole event horizon material.
    Has zero roughness, zero specular, zero emission, and absolute 0.0 albedo.
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)

    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.0, 0.0, 0.0, 1.0)
    principled.inputs['Roughness'].default_value = 1.0
    principled.inputs['Specular IOR Level'].default_value = 0.0
    principled.inputs['Metallic'].default_value = 0.0

    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    return mat
