"""
BlenderBeat — Signal Drift: Dual-Tone Spectral Shader.

Creates BB_Mat_SignalDrift — authentic reference-matched shader:
1. Deep Violet → Electric Blue → Cyan Chromatic Horizon
   - World-space X / phase gradient matching reference image:
     * Left side (-X): Deep luminous violet / purple
     * Right side (+X): Electric neon cyan / aqua
     * Audio peak impact: White-hot core desaturation
2. Dynamic CRT / Analog Scan Lines
   - World Z sinusoidal intensity masking
3. Audio Energy & Ghost Echo Decay
   - Gated by `bb_frag_energy` and `bb_ghost_factor`
"""

import bpy


def create_signal_drift_material(
    name: str = "BB_Mat_SignalDrift",
    min_glow: float = 3.0,
    peak_emission: float = 90.0,
    scan_line_density: float = 80.0,
    scan_line_strength: float = 0.45,
) -> bpy.types.Material:
    """
    Construct the reference-accurate spectral emission shader.
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (1700, 0)

    emission = nodes.new('ShaderNodeEmission')
    emission.location = (1450, 0)

    # ── Attribute Inputs ──────────────────────────────────────────────
    attr_energy = nodes.new('ShaderNodeAttribute')
    attr_energy.location = (-1200, 400)
    attr_energy.attribute_name = "bb_frag_energy"
    attr_energy.attribute_type = 'GEOMETRY'

    attr_phase = nodes.new('ShaderNodeAttribute')
    attr_phase.location = (-1200, 200)
    attr_phase.attribute_name = "bb_frag_phase"
    attr_phase.attribute_type = 'GEOMETRY'

    attr_ghost = nodes.new('ShaderNodeAttribute')
    attr_ghost.location = (-1200, 0)
    attr_ghost.attribute_name = "bb_ghost_factor"
    attr_ghost.attribute_type = 'GEOMETRY'

    audio_val = nodes.new('ShaderNodeValue')
    audio_val.location = (-1200, -200)
    audio_val.name = "BB_SDriftAudioEmission"
    audio_val.label = "Audio Emission"
    audio_val.outputs[0].default_value = 1.0

    # ── CRT Scan Line Masking ─────────────────────────────────────────
    geom = nodes.new('ShaderNodeNewGeometry')
    geom.location = (-1200, -500)

    sep_pos = nodes.new('ShaderNodeSeparateXYZ')
    sep_pos.location = (-950, -500)
    links.new(geom.outputs['Position'], sep_pos.inputs['Vector'])

    # Sinusoidal scan lines along Z
    scan_mult = nodes.new('ShaderNodeMath')
    scan_mult.location = (-750, -500)
    scan_mult.operation = 'MULTIPLY'
    scan_mult.inputs[1].default_value = float(scan_line_density)
    links.new(sep_pos.outputs['Z'], scan_mult.inputs[0])

    scan_sin = nodes.new('ShaderNodeMath')
    scan_sin.location = (-550, -500)
    scan_sin.operation = 'SINE'
    links.new(scan_mult.outputs['Value'], scan_sin.inputs[0])

    scan_remap = nodes.new('ShaderNodeMath')
    scan_remap.location = (-350, -500)
    scan_remap.operation = 'MULTIPLY_ADD'
    scan_remap.inputs[1].default_value = 0.5
    scan_remap.inputs[2].default_value = 0.5
    links.new(scan_sin.outputs['Value'], scan_remap.inputs[0])

    # Scan line mix: lerp(1.0, pattern, strength)
    scan_mask = nodes.new('ShaderNodeMath')
    scan_mask.location = (-150, -500)
    scan_mask.operation = 'MULTIPLY_ADD'
    scan_mask.inputs[1].default_value = -float(scan_line_strength)
    scan_mask.inputs[2].default_value = 1.0
    links.new(scan_remap.outputs['Value'], scan_mask.inputs[0])

    # ── Combined Energy Modulation ────────────────────────────────────
    audio_boost = nodes.new('ShaderNodeMath')
    audio_boost.location = (-750, 200)
    audio_boost.operation = 'MULTIPLY'
    links.new(attr_energy.outputs['Fac'], audio_boost.inputs[0])
    links.new(audio_val.outputs[0], audio_boost.inputs[1])

    # Base minimum visibility (so silhouette is always readable)
    energy_base = nodes.new('ShaderNodeMath')
    energy_base.location = (-550, 200)
    energy_base.operation = 'ADD'
    energy_base.inputs[1].default_value = 0.45
    links.new(audio_boost.outputs['Value'], energy_base.inputs[0])

    # Multiply by ghost factor
    ghost_mult = nodes.new('ShaderNodeMath')
    ghost_mult.location = (-350, 200)
    ghost_mult.operation = 'MULTIPLY'
    links.new(energy_base.outputs['Value'], ghost_mult.inputs[0])
    links.new(attr_ghost.outputs['Fac'], ghost_mult.inputs[1])

    # Multiply by CRT scan lines
    final_factor = nodes.new('ShaderNodeMath')
    final_factor.location = (-150, 200)
    final_factor.operation = 'MULTIPLY'
    links.new(ghost_mult.outputs['Value'], final_factor.inputs[0])
    links.new(scan_mask.outputs['Value'], final_factor.inputs[1])

    # ── Dual-Tone Color Palette (Violet to Cyan) ──────────────────────
    # Position X mapped from [-0.3, 0.3] -> [0, 1]
    x_remap = nodes.new('ShaderNodeMapRange')
    x_remap.location = (-750, -200)
    x_remap.inputs['From Min'].default_value = -0.35
    x_remap.inputs['From Max'].default_value = 0.35
    x_remap.inputs['To Min'].default_value = 0.0
    x_remap.inputs['To Max'].default_value = 1.0
    links.new(sep_pos.outputs['X'], x_remap.inputs['Value'])

    # Color Ramp: Violet -> Deep Electric Blue -> Neon Cyan -> White
    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (-450, -200)
    cr_elements = color_ramp.color_ramp.elements
    # Stop 0: Deep Violet
    cr_elements[0].position = 0.0
    cr_elements[0].color = (0.35, 0.02, 0.95, 1.0)
    # Stop 1: Electric Neon Cyan
    cr_elements[1].position = 1.0
    cr_elements[1].color = (0.0, 0.75, 1.0, 1.0)
    # Add intermediate Indigo
    mid_elem = color_ramp.color_ramp.elements.new(0.45)
    mid_elem.color = (0.10, 0.15, 0.98, 1.0)
    links.new(x_remap.outputs['Result'], color_ramp.inputs['Fac'])

    # White-hot core blend on extreme kick energy (>0.75)
    white_thresh = nodes.new('ShaderNodeMath')
    white_thresh.location = (150, 100)
    white_thresh.operation = 'SUBTRACT'
    white_thresh.inputs[1].default_value = 0.75
    links.new(attr_energy.outputs['Fac'], white_thresh.inputs[0])

    white_scale = nodes.new('ShaderNodeMath')
    white_scale.location = (350, 100)
    white_scale.operation = 'MULTIPLY'
    white_scale.inputs[1].default_value = 4.0
    links.new(white_thresh.outputs['Value'], white_scale.inputs[0])

    white_clamp = nodes.new('ShaderNodeClamp')
    white_clamp.location = (550, 100)
    white_clamp.inputs['Min'].default_value = 0.0
    white_clamp.inputs['Max'].default_value = 0.9
    links.new(white_scale.outputs['Value'], white_clamp.inputs['Value'])

    mix_white = nodes.new('ShaderNodeMix')
    mix_white.data_type = 'RGBA'
    mix_white.location = (850, -100)
    mix_white.inputs['B'].default_value = (1.0, 1.0, 1.0, 1.0)
    links.new(white_clamp.outputs['Result'], mix_white.inputs['Factor'])
    links.new(color_ramp.outputs['Color'], mix_white.inputs['A'])

    links.new(mix_white.outputs['Result'], emission.inputs['Color'])

    # ── Emission Strength ─────────────────────────────────────────────
    range_span = max(peak_emission - min_glow, 1.0)
    strength_scale = nodes.new('ShaderNodeMath')
    strength_scale.location = (850, 200)
    strength_scale.operation = 'MULTIPLY'
    strength_scale.inputs[1].default_value = range_span
    links.new(final_factor.outputs['Value'], strength_scale.inputs[0])

    strength_final = nodes.new('ShaderNodeMath')
    strength_final.location = (1100, 200)
    strength_final.operation = 'ADD'
    strength_final.inputs[1].default_value = min_glow
    links.new(strength_scale.outputs['Value'], strength_final.inputs[0])

    links.new(strength_final.outputs['Value'], emission.inputs['Strength'])
    links.new(emission.outputs['Emission'], output.inputs['Surface'])

    mat.use_backface_culling = False
    return mat
