"""
BlenderBeat — Infinite Light Grid: LED Emission Material.

Creates BB_Mat_GridLED — a production-grade emission shader for the
square light grid tunnel with per-pipe stochastic beat reactivity and
Aura Sync color management.

Each square frame has 4 pipes (top, bottom, left, right).
On audio beat impacts:
- Beat energy triggers stochastic subset selection: 1 pipe, 2 pipes,
  or rarely all 4 pipes ignite per frame.
- Unlit pipes stay dark or drop to minimal resting glow.
- Occasional random full frames burst with bright flashes.
- Aura Sync SPECTRUM provides chromatic gradients down the tunnel.
"""

import bpy
from typing import Tuple


def create_grid_led_material(
    name: str = "BB_Mat_GridLED",
    color_mode: str = "SPECTRUM",
    custom_color: Tuple[float, float, float] = (0.0, 0.8, 1.0),
    min_glow: float = 0.2,
    peak_emission: float = 65.0,
) -> bpy.types.Material:
    """
    Aura Sync LED emission shader for the Infinite Light Grid.

    Args:
        name: Material name
        color_mode: Aura Sync mode (SPECTRUM/RED/CYAN/VIOLET/AMBER/WHITE/CUSTOM)
        custom_color: RGB tuple for CUSTOM mode
        min_glow: Resting emission strength (dim/subtle)
        peak_emission: Maximum emission on beat impact

    Returns:
        bpy.types.Material
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
    emission.location = (1150, 0)

    # ── Per-Geometry Attribute Inputs ─────────────────────────────────
    attr_glow = nodes.new('ShaderNodeAttribute')
    attr_glow.location = (-1300, 300)
    attr_glow.attribute_name = "bb_frame_glow"
    attr_glow.attribute_type = 'GEOMETRY'

    attr_phase = nodes.new('ShaderNodeAttribute')
    attr_phase.location = (-1300, 100)
    attr_phase.attribute_name = "bb_frame_phase"
    attr_phase.attribute_type = 'GEOMETRY'

    attr_flicker = nodes.new('ShaderNodeAttribute')
    attr_flicker.location = (-1300, -100)
    attr_flicker.attribute_name = "bb_edge_flicker"
    attr_flicker.attribute_type = 'GEOMETRY'

    # Global Audio Emission driver node (driven by BB_Visualizer['bb_emission_strength'])
    audio_val = nodes.new('ShaderNodeValue')
    audio_val.location = (-1300, -300)
    audio_val.name = "BB_GridAudioEmission"
    audio_val.label = "Audio Emission"
    audio_val.outputs[0].default_value = 1.0

    # ── Calculate Pipe Quadrant (0, 1, 2, 3) from Object Local Coordinates ───
    # Local XY angle: atan2(Y, X)
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-1300, -500)

    sep_xyz = nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.location = (-1100, -500)
    links.new(tex_coord.outputs['Object'], sep_xyz.inputs['Vector'])

    atan2_node = nodes.new('ShaderNodeMath')
    atan2_node.location = (-900, -500)
    atan2_node.operation = 'ARCTAN2'
    links.new(sep_xyz.outputs['Y'], atan2_node.inputs[0])
    links.new(sep_xyz.outputs['X'], atan2_node.inputs[1])

    # (angle / (2*pi)) + 0.5 -> [0, 1]
    angle_norm = nodes.new('ShaderNodeMath')
    angle_norm.location = (-720, -500)
    angle_norm.operation = 'MULTIPLY_ADD'
    angle_norm.inputs[1].default_value = 1.0 / (2.0 * 3.14159265)
    angle_norm.inputs[2].default_value = 0.5
    links.new(atan2_node.outputs['Value'], angle_norm.inputs[0])

    # Discretize into 4 pipe quadrants: floor(norm * 4.0) -> {0, 1, 2, 3}
    pipe_mult4 = nodes.new('ShaderNodeMath')
    pipe_mult4.location = (-540, -500)
    pipe_mult4.operation = 'MULTIPLY'
    pipe_mult4.inputs[1].default_value = 4.0
    links.new(angle_norm.outputs['Value'], pipe_mult4.inputs[0])

    pipe_id_node = nodes.new('ShaderNodeMath')
    pipe_id_node.location = (-360, -500)
    pipe_id_node.operation = 'FLOOR'
    links.new(pipe_mult4.outputs['Value'], pipe_id_node.inputs[0])

    # ── Per-Pipe Stochastic Hash ───────────────────────────────────────
    phase_scale = nodes.new('ShaderNodeMath')
    phase_scale.location = (-360, -300)
    phase_scale.operation = 'MULTIPLY'
    phase_scale.inputs[1].default_value = 73.19
    links.new(attr_phase.outputs['Fac'], phase_scale.inputs[0])

    pipe_scale = nodes.new('ShaderNodeMath')
    pipe_scale.location = (-200, -500)
    pipe_scale.operation = 'MULTIPLY'
    pipe_scale.inputs[1].default_value = 17.31
    links.new(pipe_id_node.outputs['Value'], pipe_scale.inputs[0])

    comb_pos = nodes.new('ShaderNodeCombineXYZ')
    comb_pos.location = (-20, -400)
    links.new(phase_scale.outputs['Value'], comb_pos.inputs['X'])
    links.new(pipe_scale.outputs['Value'], comb_pos.inputs['Y'])
    comb_pos.inputs['Z'].default_value = 0.5

    pipe_noise = nodes.new('ShaderNodeTexWhiteNoise')
    pipe_noise.noise_dimensions = '3D'
    pipe_noise.location = (160, -400)
    links.new(comb_pos.outputs['Vector'], pipe_noise.inputs['Vector'])

    # Secondary hash for whole-frame strobe
    frame_noise = nodes.new('ShaderNodeTexWhiteNoise')
    frame_noise.noise_dimensions = '1D'
    frame_noise.location = (160, -600)
    links.new(phase_scale.outputs['Value'], frame_noise.inputs['W'])

    # Whole frame burst: if frame_noise < 0.12 (~12% of frames), whole square fires
    whole_frame_gate = nodes.new('ShaderNodeMath')
    whole_frame_gate.location = (360, -600)
    whole_frame_gate.operation = 'LESS_THAN'
    whole_frame_gate.inputs[1].default_value = 0.12
    links.new(frame_noise.outputs['Value'], whole_frame_gate.inputs[0])

    # Per-pipe stochastic threshold:
    # Quiet frames (attr_glow = 0): threshold is 0.72 (most pipes dark)
    # Beat impact (attr_glow = 1.0): threshold drops to 0.27 (pipes ignite)
    thresh_calc = nodes.new('ShaderNodeMath')
    thresh_calc.location = (160, -220)
    thresh_calc.operation = 'MULTIPLY_ADD'
    thresh_calc.inputs[1].default_value = -0.45  # Slope
    thresh_calc.inputs[2].default_value = 0.72   # Base threshold
    links.new(attr_glow.outputs['Fac'], thresh_calc.inputs[0])

    pipe_gate = nodes.new('ShaderNodeMath')
    pipe_gate.location = (360, -350)
    pipe_gate.operation = 'GREATER_THAN'
    links.new(pipe_noise.outputs['Value'], pipe_gate.inputs[0])
    links.new(thresh_calc.outputs['Value'], pipe_gate.inputs[1])

    # Either individual pipe fires OR whole frame fires
    active_pipe_mask = nodes.new('ShaderNodeMath')
    active_pipe_mask.location = (540, -450)
    active_pipe_mask.operation = 'MAXIMUM'
    links.new(pipe_gate.outputs['Value'], active_pipe_mask.inputs[0])
    links.new(whole_frame_gate.outputs['Value'], active_pipe_mask.inputs[1])

    # ── Energy and Contrast Processing ─────────────────────────────────
    # Multiply frame shockwave glow by the active pipe mask
    pipe_energized = nodes.new('ShaderNodeMath')
    pipe_energized.location = (160, 200)
    pipe_energized.operation = 'MULTIPLY'
    links.new(attr_glow.outputs['Fac'], pipe_energized.inputs[0])
    links.new(active_pipe_mask.outputs['Value'], pipe_energized.inputs[1])

    # Add edge flicker (also gated by active pipe mask or whole frame)
    flicker_gated = nodes.new('ShaderNodeMath')
    flicker_gated.location = (340, 100)
    flicker_gated.operation = 'MULTIPLY'
    links.new(attr_flicker.outputs['Fac'], flicker_gated.inputs[0])
    links.new(active_pipe_mask.outputs['Value'], flicker_gated.inputs[1])

    glow_with_flicker = nodes.new('ShaderNodeMath')
    glow_with_flicker.location = (500, 200)
    glow_with_flicker.operation = 'MAXIMUM'
    links.new(pipe_energized.outputs['Value'], glow_with_flicker.inputs[0])
    links.new(flicker_gated.outputs['Value'], glow_with_flicker.inputs[1])

    # Multiply by audio emission driver
    combined_energy = nodes.new('ShaderNodeMath')
    combined_energy.location = (660, 200)
    combined_energy.operation = 'MULTIPLY'
    links.new(glow_with_flicker.outputs['Value'], combined_energy.inputs[0])
    links.new(audio_val.outputs[0], combined_energy.inputs[1])

    # Nonlinear contrast curve: energy^1.6
    contrast_pow = nodes.new('ShaderNodeMath')
    contrast_pow.location = (800, 200)
    contrast_pow.operation = 'POWER'
    contrast_pow.inputs[1].default_value = 1.6
    links.new(combined_energy.outputs['Value'], contrast_pow.inputs[0])

    # ── Aura Sync Color Pipeline ───────────────────────────────────────
    if color_mode == 'SPECTRUM':
        # Rainbow spectrum cycling down tunnel
        phase_mult = nodes.new('ShaderNodeMath')
        phase_mult.location = (160, 20)
        phase_mult.operation = 'MULTIPLY'
        phase_mult.inputs[1].default_value = 3.0  # 3 chromatic loops along tunnel
        links.new(attr_phase.outputs['Fac'], phase_mult.inputs[0])

        # Beat hue shift
        beat_hue = nodes.new('ShaderNodeMath')
        beat_hue.location = (160, -100)
        beat_hue.operation = 'MULTIPLY'
        beat_hue.inputs[1].default_value = 0.25
        links.new(contrast_pow.outputs['Value'], beat_hue.inputs[0])

        hue_add = nodes.new('ShaderNodeMath')
        hue_add.location = (340, -50)
        hue_add.operation = 'ADD'
        links.new(phase_mult.outputs['Value'], hue_add.inputs[0])
        links.new(beat_hue.outputs['Value'], hue_add.inputs[1])

        # Modulo 1.0 for seamless hue cycle
        hue_mod = nodes.new('ShaderNodeMath')
        hue_mod.location = (520, -50)
        hue_mod.operation = 'MODULO'
        hue_mod.inputs[1].default_value = 1.0
        links.new(hue_add.outputs['Value'], hue_mod.inputs[0])

        # HSV to RGB
        hsv_node = nodes.new('ShaderNodeCombineColor')
        hsv_node.mode = 'HSV'
        hsv_node.location = (700, -50)
        hsv_node.inputs['Red'].default_value = 0.0
        hsv_node.inputs['Green'].default_value = 1.0
        hsv_node.inputs['Blue'].default_value = 1.0
        links.new(hue_mod.outputs['Value'], hsv_node.inputs['Red'])

        # White-hot core blend only on extreme peak energy (> 0.8)
        core_sub = nodes.new('ShaderNodeMath')
        core_sub.location = (850, 50)
        core_sub.operation = 'SUBTRACT'
        core_sub.inputs[1].default_value = 0.80
        links.new(contrast_pow.outputs['Value'], core_sub.inputs[0])

        core_fac = nodes.new('ShaderNodeMath')
        core_fac.location = (980, 50)
        core_fac.operation = 'MULTIPLY'
        core_fac.inputs[1].default_value = 3.5
        links.new(core_sub.outputs['Value'], core_fac.inputs[0])

        core_clamp = nodes.new('ShaderNodeClamp')
        core_clamp.location = (1080, 50)
        core_clamp.inputs['Min'].default_value = 0.0
        core_clamp.inputs['Max'].default_value = 0.60
        links.new(core_fac.outputs['Value'], core_clamp.inputs['Value'])

        core_mix = nodes.new('ShaderNodeMix')
        core_mix.data_type = 'RGBA'
        core_mix.location = (1080, -100)
        core_mix.inputs['A'].default_value = (1.0, 1.0, 1.0, 1.0)
        core_mix.inputs['B'].default_value = (1.0, 1.0, 1.0, 1.0)
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
        base_c, mid_c, core_c = palette_map.get(color_mode, palette_map['WHITE'])

        color_ramp = nodes.new('ShaderNodeValToRGB')
        color_ramp.location = (700, -50)
        ramp = color_ramp.color_ramp
        ramp.elements[0].color = (*base_c, 1.0)
        ramp.elements[0].position = 0.0
        mid_el = ramp.elements.new(0.45)
        mid_el.color = (*mid_c, 1.0)
        ramp.elements[-1].color = (*core_c, 1.0)
        ramp.elements[-1].position = 1.0

        links.new(contrast_pow.outputs['Value'], color_ramp.inputs['Fac'])
        links.new(color_ramp.outputs['Color'], emission.inputs['Color'])

    # ── Emission Strength Control ──────────────────────────────────────
    # Active pipes scale up to peak_emission. Inactive pipes stay at min_glow.
    range_span = max(peak_emission - min_glow, 1.0)
    glow_scaler = nodes.new('ShaderNodeMath')
    glow_scaler.location = (950, 200)
    glow_scaler.operation = 'MULTIPLY'
    glow_scaler.inputs[1].default_value = range_span
    links.new(contrast_pow.outputs['Value'], glow_scaler.inputs[0])

    strength_add = nodes.new('ShaderNodeMath')
    strength_add.location = (1080, 200)
    strength_add.operation = 'ADD'
    strength_add.inputs[1].default_value = min_glow
    links.new(glow_scaler.outputs['Value'], strength_add.inputs[0])

    links.new(strength_add.outputs['Value'], emission.inputs['Strength'])

    # Material Output
    links.new(emission.outputs['Emission'], output.inputs['Surface'])

    print(f"[BlenderBeat] Grid LED material created: mode={color_mode}, "
          f"min_glow={min_glow}, peak={peak_emission}")
    return mat
