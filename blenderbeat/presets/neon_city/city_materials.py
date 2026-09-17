"""
BlenderBeat — Neon Signal City: Shaders & Materials.

Materials:
1. BB_Mat_CityBuilding: Dark metallic architectural panels with subtle specular reflection
2. BB_Mat_CityLights: Hero audio-reactive vertical light emission shader with:
   - Dual-tone gradient: Cyan / Electric Teal to Magenta / Purple
   - Kick-driven depth wave propagation along Y
   - Beat zone alternating choreography
   - White-hot core flare on transient kick peaks
3. BB_Mat_WetStreet: Highly reflective wet concrete/asphalt with puddle roughness noise
4. BB_Mat_Terminus: Distant atmospheric beacon at corridor end
"""

import bpy


def create_city_materials() -> dict:
    """Construct all materials required for Neon Signal City."""
    mats = {}

    # ══════════════════════════════════════════════════════════════════
    # 1. Dark Building Facade Material
    # ══════════════════════════════════════════════════════════════════
    mat_bldg = bpy.data.materials.get("BB_Mat_CityBuilding") or bpy.data.materials.new("BB_Mat_CityBuilding")
    mat_bldg.use_nodes = True
    t_bldg = mat_bldg.node_tree
    n_bldg = t_bldg.nodes
    l_bldg = t_bldg.links
    n_bldg.clear()

    out_bldg = n_bldg.new("ShaderNodeOutputMaterial")
    out_bldg.location = (800, 0)

    bsdf_bldg = n_bldg.new("ShaderNodeBsdfPrincipled")
    bsdf_bldg.location = (400, 0)
    # Dark reflective architectural alloy with subtle blue-gray tone
    bsdf_bldg.inputs["Base Color"].default_value = (0.025, 0.038, 0.052, 1.0)
    bsdf_bldg.inputs["Metallic"].default_value = 0.85
    bsdf_bldg.inputs["Roughness"].default_value = 0.32
    bsdf_bldg.inputs["IOR"].default_value = 1.45

    # Subtle architectural edge bevel emission / ambient bounce so the majestic towers are visible
    fresnel = n_bldg.new("ShaderNodeFresnel")
    fresnel.location = (0, -200)
    fresnel.inputs["IOR"].default_value = 1.35

    fresnel_tint = n_bldg.new("ShaderNodeMix")
    fresnel_tint.data_type = "RGBA"
    fresnel_tint.location = (200, -200)
    fresnel_tint.inputs["Factor"].default_value = 0.08
    fresnel_tint.inputs["A"].default_value = (0.0, 0.0, 0.0, 1.0)
    fresnel_tint.inputs["B"].default_value = (0.08, 0.35, 0.55, 1.0)

    bsdf_bldg.inputs["Emission Color"].default_value = (0.04, 0.22, 0.38, 1.0)
    bsdf_bldg.inputs["Emission Strength"].default_value = 0.12

    l_bldg.new(bsdf_bldg.outputs["BSDF"], out_bldg.inputs["Surface"])
    mats["building"] = mat_bldg

    # ══════════════════════════════════════════════════════════════════
    # 2. Wet Reflective Street Material
    # ══════════════════════════════════════════════════════════════════
    mat_street = bpy.data.materials.get("BB_Mat_WetStreet") or bpy.data.materials.new("BB_Mat_WetStreet")
    mat_street.use_nodes = True
    t_st = mat_street.node_tree
    n_st = t_st.nodes
    l_st = t_st.links
    n_st.clear()

    out_st = n_st.new("ShaderNodeOutputMaterial")
    out_st.location = (800, 0)

    bsdf_st = n_st.new("ShaderNodeBsdfPrincipled")
    bsdf_st.location = (400, 0)
    # Very dark damp asphalt base color with mirror wetness
    bsdf_st.inputs["Base Color"].default_value = (0.008, 0.012, 0.018, 1.0)
    bsdf_st.inputs["Metallic"].default_value = 0.88
    bsdf_st.inputs["IOR"].default_value = 1.333

    # Puddle roughness noise
    tex_coord = n_st.new("ShaderNodeTexCoord")
    tex_coord.location = (-700, 0)

    noise_puddles = n_st.new("ShaderNodeTexNoise")
    noise_puddles.location = (-450, 0)
    noise_puddles.inputs["Scale"].default_value = 0.5
    noise_puddles.inputs["Detail"].default_value = 4.0
    noise_puddles.inputs["Roughness"].default_value = 0.5
    l_st.new(tex_coord.outputs["Object"], noise_puddles.inputs["Vector"])

    ramp_rough = n_st.new("ShaderNodeMapRange")
    ramp_rough.location = (-150, 0)
    ramp_rough.inputs["From Min"].default_value = 0.2
    ramp_rough.inputs["From Max"].default_value = 0.75
    ramp_rough.inputs["To Min"].default_value = 0.005   # Mirror wet reflection
    ramp_rough.inputs["To Max"].default_value = 0.09    # Dark damp concrete
    l_st.new(noise_puddles.outputs["Fac"], ramp_rough.inputs["Value"])
    l_st.new(ramp_rough.outputs["Result"], bsdf_st.inputs["Roughness"])

    l_st.new(bsdf_st.outputs["BSDF"], out_st.inputs["Surface"])
    mats["street"] = mat_street

    # ══════════════════════════════════════════════════════════════════
    # 3. Hero Audio-Reactive Vertical Light Strip Material
    # ══════════════════════════════════════════════════════════════════
    mat_lights = bpy.data.materials.get("BB_Mat_CityLights") or bpy.data.materials.new("BB_Mat_CityLights")
    mat_lights.use_nodes = True
    t_lt = mat_lights.node_tree
    n_lt = t_lt.nodes
    l_lt = t_lt.links
    n_lt.clear()

    out_lt = n_lt.new("ShaderNodeOutputMaterial")
    out_lt.location = (1800, 0)

    emission = n_lt.new("ShaderNodeEmission")
    emission.location = (1500, 0)

    # Inputs from drivers and geometry
    geom = n_lt.new("ShaderNodeNewGeometry")
    geom.location = (-1200, 300)

    sep_pos = n_lt.new("ShaderNodeSeparateXYZ")
    sep_pos.location = (-950, 300)
    l_lt.new(geom.outputs["Position"], sep_pos.inputs["Vector"])

    # Driver Channels
    val_kick = n_lt.new("ShaderNodeValue")
    val_kick.name = "BB_NC_KickVal"
    val_kick.label = "Kick Impulse"
    val_kick.location = (-1200, 0)
    val_kick.outputs[0].default_value = 0.0

    val_wave_pos = n_lt.new("ShaderNodeValue")
    val_wave_pos.name = "BB_NC_WavePos"
    val_wave_pos.label = "Kick Wave Depth Y"
    val_wave_pos.location = (-1200, -200)
    val_wave_pos.outputs[0].default_value = 0.0

    val_bass = n_lt.new("ShaderNodeValue")
    val_bass.name = "BB_NC_BassVal"
    val_bass.label = "Bass Macro Ambient"
    val_bass.location = (-1200, -400)
    val_bass.outputs[0].default_value = 0.35

    val_beat = n_lt.new("ShaderNodeValue")
    val_beat.name = "BB_NC_BeatVal"
    val_beat.label = "Beat Zone Phase"
    val_beat.location = (-1200, -600)
    val_beat.outputs[0].default_value = 0.0

    # ── Depth Wave Falloff along Y ────────────────────────────────────
    wave_dist = n_lt.new("ShaderNodeMath")
    wave_dist.location = (-700, 100)
    wave_dist.operation = "SUBTRACT"
    l_lt.new(sep_pos.outputs["Y"], wave_dist.inputs[0])
    l_lt.new(val_wave_pos.outputs[0], wave_dist.inputs[1])

    wave_abs = n_lt.new("ShaderNodeMath")
    wave_abs.location = (-500, 100)
    wave_abs.operation = "ABSOLUTE"
    l_lt.new(wave_dist.outputs["Value"], wave_abs.inputs[0])

    # Wave width: ~25m depth window
    wave_falloff = n_lt.new("ShaderNodeMapRange")
    wave_falloff.location = (-300, 100)
    wave_falloff.inputs["From Min"].default_value = 0.0
    wave_falloff.inputs["From Max"].default_value = 25.0
    wave_falloff.inputs["To Min"].default_value = 1.0
    wave_falloff.inputs["To Max"].default_value = 0.0
    l_lt.new(wave_abs.outputs["Value"], wave_falloff.inputs["Value"])

    # Modulate wave intensity by kick impulse
    kick_wave_intensity = n_lt.new("ShaderNodeMath")
    kick_wave_intensity.location = (-50, 100)
    kick_wave_intensity.operation = "MULTIPLY"
    l_lt.new(wave_falloff.outputs["Result"], kick_wave_intensity.inputs[0])
    l_lt.new(val_kick.outputs[0], kick_wave_intensity.inputs[1])

    # Base ambient breathing (bass driven)
    bass_ambient = n_lt.new("ShaderNodeMath")
    bass_ambient.location = (150, -200)
    bass_ambient.operation = "MULTIPLY_ADD"
    bass_ambient.inputs[1].default_value = 1.4
    bass_ambient.inputs[2].default_value = 0.45  # Resting dim brightness
    l_lt.new(val_bass.outputs[0], bass_ambient.inputs[0])

    # Combined total emission factor
    total_factor = n_lt.new("ShaderNodeMath")
    total_factor.location = (400, 0)
    total_factor.operation = "ADD"
    l_lt.new(kick_wave_intensity.outputs["Value"], total_factor.inputs[0])
    l_lt.new(bass_ambient.outputs["Value"], total_factor.inputs[1])

    # ── Dual-Tone Color Palette (Cyan/Teal vs Magenta/Purple) ─────────
    side_map = n_lt.new("ShaderNodeMapRange")
    side_map.location = (-300, 400)
    side_map.inputs["From Min"].default_value = -12.0
    side_map.inputs["From Max"].default_value = 12.0
    side_map.inputs["To Min"].default_value = 0.0
    side_map.inputs["To Max"].default_value = 1.0
    l_lt.new(sep_pos.outputs["X"], side_map.inputs["Value"])

    col_ramp = n_lt.new("ShaderNodeValToRGB")
    col_ramp.location = (0, 400)
    elements = col_ramp.color_ramp.elements
    # Stop 0 (Left Side - Magenta/Purple accent)
    elements[0].position = 0.0
    elements[0].color = (0.85, 0.05, 0.85, 1.0)
    # Stop 1 (Right Side - Electric Cyan hero)
    elements[1].position = 1.0
    elements[1].color = (0.0, 0.95, 0.95, 1.0)
    # Mid stop (Deep Electric Indigo)
    mid_e = col_ramp.color_ramp.elements.new(0.48)
    mid_e.color = (0.05, 0.45, 1.0, 1.0)
    l_lt.new(side_map.outputs["Result"], col_ramp.inputs["Fac"])

    # White-hot transient flare mix when kick factor is high
    white_mix = n_lt.new("ShaderNodeMix")
    white_mix.data_type = "RGBA"
    white_mix.location = (600, 300)
    white_mix.inputs["B"].default_value = (1.0, 1.0, 1.0, 1.0)
    l_lt.new(kick_wave_intensity.outputs["Value"], white_mix.inputs["Factor"])
    l_lt.new(col_ramp.outputs["Color"], white_mix.inputs["A"])

    l_lt.new(white_mix.outputs["Result"], emission.inputs["Color"])

    # Final Emission Strength scale
    final_strength = n_lt.new("ShaderNodeMath")
    final_strength.location = (850, 0)
    final_strength.operation = "MULTIPLY"
    final_strength.inputs[1].default_value = 32.0  # High brightness for real-time Fog Glow bloom
    l_lt.new(total_factor.outputs["Value"], final_strength.inputs[0])
    l_lt.new(final_strength.outputs["Value"], emission.inputs["Strength"])

    l_lt.new(emission.outputs["Emission"], out_lt.inputs["Surface"])
    mats["lights"] = mat_lights

    # ══════════════════════════════════════════════════════════════════
    # 4. Vanishing Point Terminus Beacon
    # ══════════════════════════════════════════════════════════════════
    mat_term = bpy.data.materials.get("BB_Mat_CityTerminus") or bpy.data.materials.new("BB_Mat_CityTerminus")
    mat_term.use_nodes = True
    t_tm = mat_term.node_tree
    n_tm = t_tm.nodes
    l_tm = t_tm.links
    n_tm.clear()

    out_tm = n_tm.new("ShaderNodeOutputMaterial")
    em_tm = n_tm.new("ShaderNodeEmission")
    em_tm.inputs["Color"].default_value = (0.2, 0.95, 1.0, 1.0)
    em_tm.inputs["Strength"].default_value = 24.0
    l_tm.new(em_tm.outputs["Emission"], out_tm.inputs["Surface"])
    mats["terminus"] = mat_term

    return mats
