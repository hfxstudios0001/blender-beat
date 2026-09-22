"""
BlenderBeat — Pulse Tunnel: Shader Materials (Rebuilt for Radial Spokes).

Materials:
1. BB_Mat_PT_ChromeHull — Dark structural ring bands (near-invisible dark blue)
2. BB_Mat_PT_LEDPrimary — Hero audio-reactive RADIAL LED spokes with:
   - Per-segment ON/OFF gate via atan2(Y,X) angle index hash
   - Alternating Cyan vs Magenta based on angle index (even=cyan, odd=magenta)
   - Audio kick drives probability: more kick = more segments ON
   - White-hot override on peak transients (kick > 0.85)
   - Energy drives global emission brightness
3. BB_Mat_PT_GlowRing — Bright continuous cyan emission ring
"""

import bpy


# Color Palettes dictionary
PALETTES = {
    'CYBER_CYAN_MAGENTA': {
        'primary': (0.0, 0.9, 1.0),       # Electric Cyan
        'secondary': (1.0, 0.02, 0.8),    # Hot Magenta
        'halo': (0.0, 0.9, 1.0),
    },
    'NEON_TRON_CYAN': {
        'primary': (0.0, 0.85, 1.0),      # Electric Cyan
        'secondary': (0.1, 0.4, 1.0),     # Deep Cyber Blue
        'halo': (0.05, 0.9, 1.0),
    },
    'SYNTHWAVE_SUNSET': {
        'primary': (1.0, 0.05, 0.7),      # Hot Neon Pink/Magenta
        'secondary': (1.0, 0.5, 0.0),     # Solar Golden Orange
        'halo': (1.0, 0.1, 0.6),
    },
    'TOXIC_MATRIX': {
        'primary': (0.0, 1.0, 0.35),      # Cyber Emerald Green
        'secondary': (0.75, 1.0, 0.0),    # Acid Lime Yellow
        'halo': (0.0, 1.0, 0.4),
    },
    'SOLAR_INFERNO': {
        'primary': (1.0, 0.12, 0.02),     # Fiery Crimson Red
        'secondary': (1.0, 0.65, 0.0),    # Radiant Solar Amber
        'halo': (1.0, 0.25, 0.0),
    },
    'ARCTIC_WHITE': {
        'primary': (0.95, 0.98, 1.0),     # Ultra-bright Diamond White
        'secondary': (0.05, 0.5, 1.0),    # Sapphire Blue
        'halo': (0.9, 0.95, 1.0),
    },
}


def create_pulse_tunnel_materials(
    palette_name: str = 'CYBER_CYAN_MAGENTA',
    custom_primary: tuple = (0.0, 0.9, 1.0),
    custom_secondary: tuple = (1.0, 0.02, 0.8),
    glow_intensity: float = 35.0,
    resting_glow: float = 0.0,
) -> dict:
    """Construct all materials for the Pulse Tunnel preset.

    Args:
        palette_name: Palette enum name or 'CUSTOM_DUAL'
        custom_primary: RGB tuple for primary spokes if CUSTOM_DUAL
        custom_secondary: RGB tuple for secondary starburst/diamonds if CUSTOM_DUAL
        glow_intensity: Peak emission multiplier
        resting_glow: Base emission when quiet (0.0 = completely off)

    Returns:
        dict with keys: 'hull', 'led_primary', 'led_accent' (glow ring)
    """
    if palette_name == 'CUSTOM_DUAL':
        col_prim = custom_primary
        col_sec = custom_secondary
        col_halo = custom_primary
    else:
        pal = PALETTES.get(palette_name, PALETTES['CYBER_CYAN_MAGENTA'])
        col_prim = pal['primary']
        col_sec = pal['secondary']
        col_halo = pal['halo']

    mats = {}

    # ══════════════════════════════════════════════════════════════════
    # 1. Dark Chrome Hull — Structural Bands
    # ══════════════════════════════════════════════════════════════════
    mat_hull = _get_or_new("BB_Mat_PT_ChromeHull")
    mat_hull.use_nodes = True
    t = mat_hull.node_tree
    t.nodes.clear()

    out_h = t.nodes.new("ShaderNodeOutputMaterial")
    out_h.location = (600, 0)
    bsdf_h = t.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_h.location = (300, 0)
    bsdf_h.inputs["Base Color"].default_value = (0.005, 0.008, 0.015, 1.0)
    bsdf_h.inputs["Metallic"].default_value = 0.95
    bsdf_h.inputs["Roughness"].default_value = 0.35
    bsdf_h.inputs["Emission Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    bsdf_h.inputs["Emission Strength"].default_value = 0.0
    t.links.new(bsdf_h.outputs["BSDF"], out_h.inputs["Surface"])
    mats["hull"] = mat_hull

    # ══════════════════════════════════════════════════════════════════
    # 2. Hero LED Radial Bar — INDEPENDENT Per-Segment ON/OFF
    # ══════════════════════════════════════════════════════════════════
    mat_led = _get_or_new("BB_Mat_PT_LEDPrimary")
    mat_led.use_nodes = True
    t_led = mat_led.node_tree
    t_led.nodes.clear()

    out_l = t_led.nodes.new("ShaderNodeOutputMaterial")
    out_l.location = (1850, 0)

    bsdf_l = t_led.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_l.location = (1500, 0)
    bsdf_l.inputs["Base Color"].default_value = (0.003, 0.005, 0.012, 1.0)
    bsdf_l.inputs["Metallic"].default_value = 0.0
    bsdf_l.inputs["Roughness"].default_value = 0.5

    # ── Audio Value Nodes (driven by preset.py) ────────────────────
    kick_val = t_led.nodes.new("ShaderNodeValue")
    kick_val.name = "BB_PT_KickVal"
    kick_val.label = "Kick (Driven)"
    kick_val.location = (-1000, 500)
    kick_val.outputs[0].default_value = 0.5

    bass_val = t_led.nodes.new("ShaderNodeValue")
    bass_val.name = "BB_PT_BassVal"
    bass_val.label = "Bass (Driven)"
    bass_val.location = (-1000, 350)
    bass_val.outputs[0].default_value = 0.5

    energy_val = t_led.nodes.new("ShaderNodeValue")
    energy_val.name = "BB_PT_EnergyVal"
    energy_val.label = "Energy (Driven)"
    energy_val.location = (-1000, 200)
    energy_val.outputs[0].default_value = 0.7

    wave_pos = t_led.nodes.new("ShaderNodeValue")
    wave_pos.name = "BB_PT_WavePos"
    wave_pos.label = "Wave Position (Driven)"
    wave_pos.location = (-1000, 50)
    wave_pos.outputs[0].default_value = 0.0

    # ── Get Object-space XY for segment angle + ring zone ──────────
    tex_coord = t_led.nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-1000, -200)

    sep_xyz = t_led.nodes.new("ShaderNodeSeparateXYZ")
    sep_xyz.location = (-800, -200)
    t_led.links.new(tex_coord.outputs["Object"], sep_xyz.inputs["Vector"])

    # ── Segment angle index: atan2(Y, X) ───────────────────────────
    atan2_node = t_led.nodes.new("ShaderNodeMath")
    atan2_node.operation = 'ARCTAN2'
    atan2_node.location = (-600, -300)
    t_led.links.new(sep_xyz.outputs["Y"], atan2_node.inputs[0])
    t_led.links.new(sep_xyz.outputs["X"], atan2_node.inputs[1])

    # Scale atan2 to [0, 32] range → 32 / (2*pi) = 5.092958
    seg_scale = t_led.nodes.new("ShaderNodeMath")
    seg_scale.operation = 'MULTIPLY'
    seg_scale.location = (-450, -300)
    seg_scale.inputs[1].default_value = 5.092958
    t_led.links.new(atan2_node.outputs["Value"], seg_scale.inputs[0])

    seg_floor = t_led.nodes.new("ShaderNodeMath")
    seg_floor.operation = 'FLOOR'
    seg_floor.location = (-300, -300)
    t_led.links.new(seg_scale.outputs["Value"], seg_floor.inputs[0])

    # ── Ring zone from radial distance: length(XY) ─────────────────
    ring_dist_x2 = t_led.nodes.new("ShaderNodeMath")
    ring_dist_x2.operation = 'MULTIPLY'
    ring_dist_x2.location = (-600, -500)
    t_led.links.new(sep_xyz.outputs["X"], ring_dist_x2.inputs[0])
    t_led.links.new(sep_xyz.outputs["X"], ring_dist_x2.inputs[1])

    ring_dist_y2 = t_led.nodes.new("ShaderNodeMath")
    ring_dist_y2.operation = 'MULTIPLY'
    ring_dist_y2.location = (-600, -650)
    t_led.links.new(sep_xyz.outputs["Y"], ring_dist_y2.inputs[0])
    t_led.links.new(sep_xyz.outputs["Y"], ring_dist_y2.inputs[1])

    ring_dist_sum = t_led.nodes.new("ShaderNodeMath")
    ring_dist_sum.operation = 'ADD'
    ring_dist_sum.location = (-450, -550)
    t_led.links.new(ring_dist_x2.outputs["Value"], ring_dist_sum.inputs[0])
    t_led.links.new(ring_dist_y2.outputs["Value"], ring_dist_sum.inputs[1])

    ring_dist = t_led.nodes.new("ShaderNodeMath")
    ring_dist.operation = 'SQRT'
    ring_dist.location = (-300, -550)
    t_led.links.new(ring_dist_sum.outputs["Value"], ring_dist.inputs[0])

    # ── Step-wise Zone ID so each individual rectangular bar has a clean integer ID ──
    # Zone 1: Inner ticks (r < 1.85) -> ID 0
    # Zone 2: Mid starburst (1.85 <= r < 3.50) -> ID 1
    # Zone 3: Fringe ticks (3.50 <= r < 4.15) -> ID 2
    # Zone 4: Outer spoke bars (4.15 <= r < 6.80) -> ID 3
    # Zone 5: Perimeter diamonds (r >= 6.80) -> ID 4
    z_step1 = t_led.nodes.new("ShaderNodeMath")
    z_step1.operation = 'GREATER_THAN'
    z_step1.location = (-150, -500)
    z_step1.inputs[1].default_value = 1.85
    t_led.links.new(ring_dist.outputs["Value"], z_step1.inputs[0])

    z_step2 = t_led.nodes.new("ShaderNodeMath")
    z_step2.operation = 'GREATER_THAN'
    z_step2.location = (-150, -620)
    z_step2.inputs[1].default_value = 3.50
    t_led.links.new(ring_dist.outputs["Value"], z_step2.inputs[0])

    z_step3 = t_led.nodes.new("ShaderNodeMath")
    z_step3.operation = 'GREATER_THAN'
    z_step3.location = (-150, -740)
    z_step3.inputs[1].default_value = 4.15
    t_led.links.new(ring_dist.outputs["Value"], z_step3.inputs[0])

    z_step4 = t_led.nodes.new("ShaderNodeMath")
    z_step4.operation = 'GREATER_THAN'
    z_step4.location = (-150, -860)
    z_step4.inputs[1].default_value = 5.40
    t_led.links.new(ring_dist.outputs["Value"], z_step4.inputs[0])

    z_sum1 = t_led.nodes.new("ShaderNodeMath")
    z_sum1.operation = 'ADD'
    z_sum1.location = (0, -550)
    t_led.links.new(z_step1.outputs["Value"], z_sum1.inputs[0])
    t_led.links.new(z_step2.outputs["Value"], z_sum1.inputs[1])

    z_sum2 = t_led.nodes.new("ShaderNodeMath")
    z_sum2.operation = 'ADD'
    z_sum2.location = (0, -700)
    t_led.links.new(z_step3.outputs["Value"], z_sum2.inputs[0])
    t_led.links.new(z_step4.outputs["Value"], z_sum2.inputs[1])

    zone_id = t_led.nodes.new("ShaderNodeMath")
    zone_id.operation = 'ADD'
    zone_id.location = (150, -620)
    t_led.links.new(z_sum1.outputs["Value"], zone_id.inputs[0])
    t_led.links.new(z_sum2.outputs["Value"], zone_id.inputs[1])

    # Quantize Z position to ring index (each ring along Z = 1.8m spacing)
    z_quant = t_led.nodes.new("ShaderNodeMath")
    z_quant.operation = 'MULTIPLY'
    z_quant.location = (-300, -1000)
    z_quant.inputs[1].default_value = 0.555  # 1.0 / 1.8
    t_led.links.new(sep_xyz.outputs["Z"], z_quant.inputs[0])

    z_id = t_led.nodes.new("ShaderNodeMath")
    z_id.operation = 'FLOOR'
    z_id.location = (-150, -1000)
    t_led.links.new(z_quant.outputs["Value"], z_id.inputs[0])

    # ── Individual Segment Stochastic Hash ─────────────────────────
    # Each rectangular segment has a unique (seg_floor, zone_id, z_id)
    # hash = fract(sin(seg * 127.1 + zone * 311.7 + z_ring * 74.3) * 43758.5453)
    hash_seg = t_led.nodes.new("ShaderNodeMath")
    hash_seg.operation = 'MULTIPLY'
    hash_seg.location = (150, -350)
    hash_seg.inputs[1].default_value = 127.1
    t_led.links.new(seg_floor.outputs["Value"], hash_seg.inputs[0])

    hash_zone = t_led.nodes.new("ShaderNodeMath")
    hash_zone.operation = 'MULTIPLY'
    hash_zone.location = (150, -500)
    hash_zone.inputs[1].default_value = 311.7
    t_led.links.new(zone_id.outputs["Value"], hash_zone.inputs[0])

    hash_z = t_led.nodes.new("ShaderNodeMath")
    hash_z.operation = 'MULTIPLY'
    hash_z.location = (150, -650)
    hash_z.inputs[1].default_value = 74.3
    t_led.links.new(z_id.outputs["Value"], hash_z.inputs[0])

    hash_add1 = t_led.nodes.new("ShaderNodeMath")
    hash_add1.operation = 'ADD'
    hash_add1.location = (300, -450)
    t_led.links.new(hash_seg.outputs["Value"], hash_add1.inputs[0])
    t_led.links.new(hash_zone.outputs["Value"], hash_add1.inputs[1])

    hash_add2 = t_led.nodes.new("ShaderNodeMath")
    hash_add2.operation = 'ADD'
    hash_add2.location = (450, -500)
    t_led.links.new(hash_add1.outputs["Value"], hash_add2.inputs[0])
    t_led.links.new(hash_z.outputs["Value"], hash_add2.inputs[1])

    hash_sin = t_led.nodes.new("ShaderNodeMath")
    hash_sin.operation = 'SINE'
    hash_sin.location = (600, -500)
    t_led.links.new(hash_add2.outputs["Value"], hash_sin.inputs[0])

    hash_abs = t_led.nodes.new("ShaderNodeMath")
    hash_abs.operation = 'ABSOLUTE'
    hash_abs.location = (750, -500)
    t_led.links.new(hash_sin.outputs["Value"], hash_abs.inputs[0])

    hash_mul_big = t_led.nodes.new("ShaderNodeMath")
    hash_mul_big.operation = 'MULTIPLY'
    hash_mul_big.location = (900, -500)
    hash_mul_big.inputs[1].default_value = 43758.5453
    t_led.links.new(hash_abs.outputs["Value"], hash_mul_big.inputs[0])

    hash_frac = t_led.nodes.new("ShaderNodeMath")
    hash_frac.operation = 'FRACT'
    hash_frac.location = (1050, -500)
    t_led.links.new(hash_mul_big.outputs["Value"], hash_frac.inputs[0])

    # ── Stochastic ON/OFF Probability Gate ─────────────────────────
    # Threshold = kick * 0.75 + energy * 0.25
    # If hash < probability → segment lights up; otherwise COMPLETELY OFF (or resting glow)
    kick_prob = t_led.nodes.new("ShaderNodeMath")
    kick_prob.operation = 'MULTIPLY'
    kick_prob.location = (500, 200)
    kick_prob.inputs[1].default_value = 0.75
    t_led.links.new(kick_val.outputs[0], kick_prob.inputs[0])

    energy_prob = t_led.nodes.new("ShaderNodeMath")
    energy_prob.operation = 'MULTIPLY'
    energy_prob.location = (500, 50)
    energy_prob.inputs[1].default_value = 0.35
    t_led.links.new(energy_val.outputs[0], energy_prob.inputs[0])

    prob_add = t_led.nodes.new("ShaderNodeMath")
    prob_add.operation = 'ADD'
    prob_add.location = (700, 150)
    t_led.links.new(kick_prob.outputs["Value"], prob_add.inputs[0])
    t_led.links.new(energy_prob.outputs["Value"], prob_add.inputs[1])

    # ── Depth Shockwave Modulation ─────────────────────────────────
    # Calculate distance of this ring along Z to wave_pos:
    # wave_dist = abs(sep_xyz.Z - wave_pos)
    wave_diff = t_led.nodes.new("ShaderNodeMath")
    wave_diff.operation = 'SUBTRACT'
    wave_diff.location = (650, 0)
    t_led.links.new(sep_xyz.outputs["Z"], wave_diff.inputs[0])
    t_led.links.new(wave_pos.outputs[0], wave_diff.inputs[1])

    wave_abs = t_led.nodes.new("ShaderNodeMath")
    wave_abs.operation = 'ABSOLUTE'
    wave_abs.location = (780, 0)
    t_led.links.new(wave_diff.outputs["Value"], wave_abs.inputs[0])

    # Wave envelope: 1.0 at wave head, falloff over ~18m depth
    wave_norm = t_led.nodes.new("ShaderNodeMath")
    wave_norm.operation = 'MULTIPLY'
    wave_norm.location = (900, 0)
    wave_norm.inputs[1].default_value = 0.055  # 1.0 / 18.0m
    t_led.links.new(wave_abs.outputs["Value"], wave_norm.inputs[0])

    wave_env = t_led.nodes.new("ShaderNodeMath")
    wave_env.operation = 'SUBTRACT'
    wave_env.location = (1020, 0)
    wave_env.inputs[0].default_value = 1.0
    t_led.links.new(wave_norm.outputs["Value"], wave_env.inputs[1])

    wave_boost = t_led.nodes.new("ShaderNodeClamp")
    wave_boost.location = (1140, 0)
    wave_boost.inputs["Min"].default_value = 0.15  # Baseline activity everywhere
    wave_boost.inputs["Max"].default_value = 1.0
    t_led.links.new(wave_env.outputs["Value"], wave_boost.inputs["Value"])

    # Modulate probability with shockwave envelope
    prob_wave = t_led.nodes.new("ShaderNodeMath")
    prob_wave.operation = 'MULTIPLY'
    prob_wave.location = (850, 150)
    t_led.links.new(prob_add.outputs["Value"], prob_wave.inputs[0])
    t_led.links.new(wave_boost.outputs["Result"], prob_wave.inputs[1])

    prob_clamp = t_led.nodes.new("ShaderNodeClamp")
    prob_clamp.location = (980, 150)
    prob_clamp.inputs["Min"].default_value = 0.0   # Can turn completely off when quiet
    prob_clamp.inputs["Max"].default_value = 1.0
    t_led.links.new(prob_wave.outputs["Value"], prob_clamp.inputs["Value"])

    # Compare: 1.0 if ON, 0.0 if OFF
    seg_gate = t_led.nodes.new("ShaderNodeMath")
    seg_gate.operation = 'LESS_THAN'
    seg_gate.location = (1200, -350)
    t_led.links.new(hash_frac.outputs["Value"], seg_gate.inputs[0])
    t_led.links.new(prob_clamp.outputs["Result"], seg_gate.inputs[1])

    # ── Color Palette Integration ──────────────────────────────────
    # Inner ring (r < 1.9) = Primary Color
    # Mid Starburst spokes (1.9 <= r < 3.6) = Secondary Color
    # Outer radial bars & Halo = Primary Color
    # Perimeter diamonds (r > 6.8) = Secondary Color
    is_star_zone = t_led.nodes.new("ShaderNodeMath")
    is_star_zone.operation = 'GREATER_THAN'
    is_star_zone.location = (100, 350)
    is_star_zone.inputs[1].default_value = 1.9
    t_led.links.new(ring_dist.outputs["Value"], is_star_zone.inputs[0])

    is_outer_zone = t_led.nodes.new("ShaderNodeMath")
    is_outer_zone.operation = 'GREATER_THAN'
    is_outer_zone.location = (250, 350)
    is_outer_zone.inputs[1].default_value = 3.6
    t_led.links.new(ring_dist.outputs["Value"], is_outer_zone.inputs[0])

    zone_mix_factor = t_led.nodes.new("ShaderNodeMath")
    zone_mix_factor.operation = 'SUBTRACT'
    zone_mix_factor.location = (400, 350)
    t_led.links.new(is_star_zone.outputs["Value"], zone_mix_factor.inputs[0])
    t_led.links.new(is_outer_zone.outputs["Value"], zone_mix_factor.inputs[1])

    is_perimeter = t_led.nodes.new("ShaderNodeMath")
    is_perimeter.operation = 'GREATER_THAN'
    is_perimeter.location = (400, 200)
    is_perimeter.inputs[1].default_value = 5.4
    t_led.links.new(ring_dist.outputs["Value"], is_perimeter.inputs[0])

    sec_mask = t_led.nodes.new("ShaderNodeMath")
    sec_mask.operation = 'MAXIMUM'
    sec_mask.location = (550, 300)
    t_led.links.new(zone_mix_factor.outputs["Value"], sec_mask.inputs[0])
    t_led.links.new(is_perimeter.outputs["Value"], sec_mask.inputs[1])

    color_prim_node = t_led.nodes.new("ShaderNodeRGB")
    color_prim_node.location = (650, 500)
    color_prim_node.outputs[0].default_value = (*col_prim, 1.0)

    color_sec_node = t_led.nodes.new("ShaderNodeRGB")
    color_sec_node.location = (650, 350)
    color_sec_node.outputs[0].default_value = (*col_sec, 1.0)

    color_mix = t_led.nodes.new("ShaderNodeMix")
    color_mix.data_type = "RGBA"
    color_mix.location = (850, 450)
    t_led.links.new(sec_mask.outputs["Value"], color_mix.inputs["Factor"])
    t_led.links.new(color_prim_node.outputs[0], color_mix.inputs["A"])
    t_led.links.new(color_sec_node.outputs[0], color_mix.inputs["B"])

    # Peak kick white-hot highlight (only on extreme transients > 0.94, gently mixed)
    kick_hot = t_led.nodes.new("ShaderNodeMath")
    kick_hot.operation = 'GREATER_THAN'
    kick_hot.location = (700, 600)
    kick_hot.inputs[1].default_value = 0.94
    t_led.links.new(kick_val.outputs[0], kick_hot.inputs[0])

    kick_hot_scale = t_led.nodes.new("ShaderNodeMath")
    kick_hot_scale.operation = 'MULTIPLY'
    kick_hot_scale.location = (850, 600)
    kick_hot_scale.inputs[1].default_value = 0.70
    t_led.links.new(kick_hot.outputs["Value"], kick_hot_scale.inputs[0])

    color_white = t_led.nodes.new("ShaderNodeRGB")
    color_white.location = (850, 750)
    color_white.outputs[0].default_value = (1.0, 1.0, 1.0, 1.0)

    final_color = t_led.nodes.new("ShaderNodeMix")
    final_color.data_type = "RGBA"
    final_color.location = (1050, 450)
    t_led.links.new(kick_hot_scale.outputs["Value"], final_color.inputs["Factor"])
    t_led.links.new(color_mix.outputs["Result"], final_color.inputs["A"])
    t_led.links.new(color_white.outputs[0], final_color.inputs["B"])

    # ── Emission Brightness with Controllable Glow & Resting Off ────
    # emit = resting_glow + seg_gate * (glow_intensity * (0.35 + kick * 0.65))
    peak_dyn = t_led.nodes.new("ShaderNodeMath")
    peak_dyn.operation = 'MULTIPLY'
    peak_dyn.location = (900, -50)
    peak_dyn.inputs[1].default_value = glow_intensity * 0.65
    t_led.links.new(kick_val.outputs[0], peak_dyn.inputs[0])

    emit_base = t_led.nodes.new("ShaderNodeMath")
    emit_base.operation = 'ADD'
    emit_base.location = (1050, -50)
    emit_base.inputs[1].default_value = glow_intensity * 0.35
    t_led.links.new(peak_dyn.outputs["Value"], emit_base.inputs[0])

    emit_gated = t_led.nodes.new("ShaderNodeMath")
    emit_gated.operation = 'MULTIPLY'
    emit_gated.location = (1250, -100)
    t_led.links.new(seg_gate.outputs["Value"], emit_gated.inputs[0])
    t_led.links.new(emit_base.outputs["Value"], emit_gated.inputs[1])

    emit_final = t_led.nodes.new("ShaderNodeMath")
    emit_final.operation = 'ADD'
    emit_final.location = (1400, -100)
    emit_final.inputs[1].default_value = resting_glow
    t_led.links.new(emit_gated.outputs["Value"], emit_final.inputs[0])

    t_led.links.new(final_color.outputs["Result"], bsdf_l.inputs["Emission Color"])
    t_led.links.new(emit_final.outputs["Value"], bsdf_l.inputs["Emission Strength"])
    t_led.links.new(bsdf_l.outputs["BSDF"], out_l.inputs["Surface"])

    mats["led_primary"] = mat_led

    # ══════════════════════════════════════════════════════════════════
    # 3. Glow Ring — Hero Continuous Emission
    # ══════════════════════════════════════════════════════════════════
    mat_glow = _get_or_new("BB_Mat_PT_GlowRing")
    mat_glow.use_nodes = True
    t_g = mat_glow.node_tree
    t_g.nodes.clear()

    out_g = t_g.nodes.new("ShaderNodeOutputMaterial")
    out_g.location = (600, 0)

    bsdf_g = t_g.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_g.location = (300, 0)
    bsdf_g.inputs["Base Color"].default_value = (0.0, 0.1, 0.15, 1.0)
    bsdf_g.inputs["Metallic"].default_value = 0.0
    bsdf_g.inputs["Roughness"].default_value = 0.3
    bsdf_g.inputs["Emission Color"].default_value = (*col_halo, 1.0)

    glow_energy = t_g.nodes.new("ShaderNodeValue")
    glow_energy.name = "BB_PT_GlowEnergy"
    glow_energy.label = "Energy (Driven)"
    glow_energy.location = (-200, 0)
    glow_energy.outputs[0].default_value = 0.7

    glow_mul = t_g.nodes.new("ShaderNodeMath")
    glow_mul.operation = 'MULTIPLY'
    glow_mul.location = (0, 0)
    glow_mul.inputs[1].default_value = glow_intensity * 0.7
    t_g.links.new(glow_energy.outputs[0], glow_mul.inputs[0])

    glow_add = t_g.nodes.new("ShaderNodeMath")
    glow_add.operation = 'ADD'
    glow_add.location = (150, 0)
    glow_add.inputs[1].default_value = max(resting_glow, glow_intensity * 0.4)
    t_g.links.new(glow_mul.outputs["Value"], glow_add.inputs[0])

    t_g.links.new(glow_add.outputs["Value"], bsdf_g.inputs["Emission Strength"])
    t_g.links.new(bsdf_g.outputs["BSDF"], out_g.inputs["Surface"])

    mats["led_accent"] = mat_glow

    print(f"[BlenderBeat] Pulse Tunnel materials created: palette={palette_name}, "
          f"glow_intensity={glow_intensity}, resting_glow={resting_glow}")
    return mats


def _get_or_new(name: str) -> bpy.types.Material:
    """Get existing material or create new one."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    return mat
