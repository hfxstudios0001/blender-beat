"""
BlenderBeat — Infinite Light Grid: Geometry Nodes Instancing Engine.

Instances N master frames along negative Z depth with:
1. Per-frame alternating twist rotation for spiral perspective effect
2. Traveling shockwave pulse (bb_frame_glow) on kick/bass hits
3. Normalized depth phase (bb_frame_phase) for rainbow spectrum
4. Random edge flicker (bb_edge_flicker) on snare/hi-hat transients
5. Bass-reactive scale breathing
"""

import bpy
import math
from typing import Optional


def create_grid_geometry_nodes(
    viz_obj: bpy.types.Object,
    frame_obj: bpy.types.Object,
    frame_count: int = 35,
    spacing: float = 2.0,
    twist_per_frame: float = 0.05,
) -> bpy.types.NodeTree:
    """
    Construct the Geometry Nodes modifier tree for the light grid tunnel.

    Args:
        viz_obj: The visualizer object to receive the modifier
        frame_obj: The hidden master frame mesh to instance
        frame_count: Number of square frames in the tunnel
        spacing: Z-distance between frames
        twist_per_frame: Rotation increment per frame (radians)

    Returns:
        bpy.types.NodeTree: The created GN tree
    """
    tree_name = "BB_GridGeometryNodes"
    if tree_name in bpy.data.node_groups:
        node_tree = bpy.data.node_groups[tree_name]
        for n in list(node_tree.nodes):
            node_tree.nodes.remove(n)
    else:
        node_tree = bpy.data.node_groups.new(tree_name, 'GeometryNodeTree')

    nodes = node_tree.nodes
    links = node_tree.links

    # Clear interface
    for item in list(node_tree.interface.items_tree):
        if item.item_type in {'SOCKET'}:
            node_tree.interface.remove(item)

    # Output socket
    node_tree.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry',
    )

    # Group I/O
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1200, 0)
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1600, 0)

    # ══════════════════════════════════════════════════════════════════
    # Internal Value Nodes (driven by custom properties via drivers)
    # ══════════════════════════════════════════════════════════════════
    bass_val = nodes.new('ShaderNodeValue')
    bass_val.name = "BB_GridBassVal"
    bass_val.label = "Bass Expansion (Driven)"
    bass_val.location = (-1000, 300)

    kick_val = nodes.new('ShaderNodeValue')
    kick_val.name = "BB_GridKickVal"
    kick_val.label = "Kick Pulse (Driven)"
    kick_val.location = (-1000, 100)

    time_val = nodes.new('ShaderNodeValue')
    time_val.name = "BB_GridTimeVal"
    time_val.label = "Rotation Phase (Driven)"
    time_val.location = (-1000, -100)

    # ══════════════════════════════════════════════════════════════════
    # 1. Mesh Line — frame positions along negative Z
    # ══════════════════════════════════════════════════════════════════
    line = nodes.new('GeometryNodeMeshLine')
    line.location = (-800, 500)
    line.inputs['Count'].default_value = frame_count
    line.inputs['Start Location'].default_value = (0.0, 0.0, 0.0)
    line.inputs['Offset'].default_value = (0.0, 0.0, -spacing)

    # ══════════════════════════════════════════════════════════════════
    # 2. Object Info — master frame mesh
    # ══════════════════════════════════════════════════════════════════
    frame_info = nodes.new('GeometryNodeObjectInfo')
    frame_info.location = (-800, 200)
    frame_info.inputs['Object'].default_value = frame_obj
    frame_info.transform_space = 'RELATIVE'

    # ══════════════════════════════════════════════════════════════════
    # 3. Index node for per-frame computations
    # ══════════════════════════════════════════════════════════════════
    index_node = nodes.new('GeometryNodeInputIndex')
    index_node.location = (-800, -400)

    # ══════════════════════════════════════════════════════════════════
    # 4. Dynamic Scale per frame (Bass breathing + Kick punch)
    #    scale = 1.0 + (bass * 0.12) + (kick * 0.06)
    # ══════════════════════════════════════════════════════════════════
    scale_bass = nodes.new('ShaderNodeMath')
    scale_bass.location = (-600, 300)
    scale_bass.operation = 'MULTIPLY_ADD'
    scale_bass.inputs[1].default_value = 0.14
    links.new(bass_val.outputs[0], scale_bass.inputs[0])
    scale_bass.inputs[2].default_value = 1.0

    scale_kick = nodes.new('ShaderNodeMath')
    scale_kick.location = (-400, 300)
    scale_kick.operation = 'MULTIPLY_ADD'
    scale_kick.inputs[1].default_value = 0.08
    links.new(kick_val.outputs[0], scale_kick.inputs[0])
    links.new(scale_bass.outputs['Value'], scale_kick.inputs[2])

    combine_scale = nodes.new('ShaderNodeCombineXYZ')
    combine_scale.location = (-200, 300)
    links.new(scale_kick.outputs['Value'], combine_scale.inputs['X'])
    links.new(scale_kick.outputs['Value'], combine_scale.inputs['Y'])
    combine_scale.inputs['Z'].default_value = 1.0

    # ══════════════════════════════════════════════════════════════════
    # 5. Per-frame alternating twist rotation
    #    rotation_z = index * twist_per_frame
    #    This creates the spiral perspective visible in the reference
    # ══════════════════════════════════════════════════════════════════
    twist_mult = nodes.new('ShaderNodeMath')
    twist_mult.location = (-600, -300)
    twist_mult.operation = 'MULTIPLY'
    twist_mult.inputs[1].default_value = twist_per_frame
    links.new(index_node.outputs['Index'], twist_mult.inputs[0])

    combine_rot = nodes.new('ShaderNodeCombineXYZ')
    combine_rot.location = (-200, -300)
    combine_rot.inputs['X'].default_value = 0.0
    combine_rot.inputs['Y'].default_value = 0.0
    links.new(twist_mult.outputs['Value'], combine_rot.inputs['Z'])

    # ══════════════════════════════════════════════════════════════════
    # 6. TRAVELING SHOCKWAVE PULSE (bb_frame_glow attribute)
    #    wave = sin((index * wave_freq) - (kick * speed + time * drift))
    #    glow = clamp(wave^2.5 * audio_energy + kick_transient, 0, 1)
    # ══════════════════════════════════════════════════════════════════

    # index * wave_freq
    wave_freq = nodes.new('ShaderNodeMath')
    wave_freq.location = (-600, -500)
    wave_freq.operation = 'MULTIPLY'
    wave_freq.inputs[1].default_value = 0.55
    links.new(index_node.outputs['Index'], wave_freq.inputs[0])

    # Continuous traveling motion: time * 2.0 + kick * 6.0
    time_motion = nodes.new('ShaderNodeMath')
    time_motion.location = (-800, -600)
    time_motion.operation = 'MULTIPLY'
    time_motion.inputs[1].default_value = 2.0
    links.new(time_val.outputs[0], time_motion.inputs[0])

    kick_speed = nodes.new('ShaderNodeMath')
    kick_speed.location = (-800, -700)
    kick_speed.operation = 'MULTIPLY'
    kick_speed.inputs[1].default_value = 6.0
    links.new(kick_val.outputs[0], kick_speed.inputs[0])

    travel_offset = nodes.new('ShaderNodeMath')
    travel_offset.location = (-600, -650)
    travel_offset.operation = 'ADD'
    links.new(time_motion.outputs['Value'], travel_offset.inputs[0])
    links.new(kick_speed.outputs['Value'], travel_offset.inputs[1])

    # phase = (index * freq) - travel_offset
    wave_phase = nodes.new('ShaderNodeMath')
    wave_phase.location = (-400, -550)
    wave_phase.operation = 'SUBTRACT'
    links.new(wave_freq.outputs['Value'], wave_phase.inputs[0])
    links.new(travel_offset.outputs['Value'], wave_phase.inputs[1])

    # sin(phase) → [-1, 1]
    wave_sin = nodes.new('ShaderNodeMath')
    wave_sin.location = (-200, -550)
    wave_sin.operation = 'SINE'
    links.new(wave_phase.outputs['Value'], wave_sin.inputs[0])

    # Remap [-1,1] → [0,1]: (sin+1)*0.5
    wave_remap_add = nodes.new('ShaderNodeMath')
    wave_remap_add.location = (0, -550)
    wave_remap_add.operation = 'ADD'
    wave_remap_add.inputs[1].default_value = 1.0
    links.new(wave_sin.outputs['Value'], wave_remap_add.inputs[0])

    wave_remap_half = nodes.new('ShaderNodeMath')
    wave_remap_half.location = (200, -550)
    wave_remap_half.operation = 'MULTIPLY'
    wave_remap_half.inputs[1].default_value = 0.5
    links.new(wave_remap_add.outputs['Value'], wave_remap_half.inputs[0])

    # Sharpen with power curve: wave^2.5
    wave_power = nodes.new('ShaderNodeMath')
    wave_power.location = (350, -550)
    wave_power.operation = 'POWER'
    wave_power.inputs[1].default_value = 2.5
    links.new(wave_remap_half.outputs['Value'], wave_power.inputs[0])

    # Audio energy modulation: (bass + kick) * 2.4
    audio_energy = nodes.new('ShaderNodeMath')
    audio_energy.location = (200, -700)
    audio_energy.operation = 'ADD'
    links.new(bass_val.outputs[0], audio_energy.inputs[0])
    links.new(kick_val.outputs[0], audio_energy.inputs[1])

    audio_gain = nodes.new('ShaderNodeMath')
    audio_gain.location = (350, -700)
    audio_gain.operation = 'MULTIPLY'
    audio_gain.inputs[1].default_value = 2.4
    links.new(audio_energy.outputs['Value'], audio_gain.inputs[0])

    # wave * audio_energy
    wave_pulse = nodes.new('ShaderNodeMath')
    wave_pulse.location = (500, -600)
    wave_pulse.operation = 'MULTIPLY'
    links.new(wave_power.outputs['Value'], wave_pulse.inputs[0])
    links.new(audio_gain.outputs['Value'], wave_pulse.inputs[1])

    # Add direct kick transient punch
    kick_transient = nodes.new('ShaderNodeMath')
    kick_transient.location = (500, -750)
    kick_transient.operation = 'MULTIPLY'
    kick_transient.inputs[1].default_value = 1.6
    links.new(kick_val.outputs[0], kick_transient.inputs[0])

    total_pulse = nodes.new('ShaderNodeMath')
    total_pulse.location = (700, -650)
    total_pulse.operation = 'ADD'
    links.new(wave_pulse.outputs['Value'], total_pulse.inputs[0])
    links.new(kick_transient.outputs['Value'], total_pulse.inputs[1])

    # Clamp [0, 1]
    glow_clamp = nodes.new('ShaderNodeClamp')
    glow_clamp.location = (900, -650)
    glow_clamp.inputs['Min'].default_value = 0.0
    glow_clamp.inputs['Max'].default_value = 1.0
    links.new(total_pulse.outputs['Value'], glow_clamp.inputs['Value'])

    # ══════════════════════════════════════════════════════════════════
    # 7. Store Named Attributes on Mesh Line Points
    # ══════════════════════════════════════════════════════════════════

    # bb_frame_glow (shockwave energy)
    store_glow = nodes.new('GeometryNodeStoreNamedAttribute')
    store_glow.location = (-50, 500)
    store_glow.data_type = 'FLOAT'
    store_glow.domain = 'POINT'
    store_glow.inputs['Name'].default_value = "bb_frame_glow"
    links.new(line.outputs['Mesh'], store_glow.inputs['Geometry'])
    links.new(glow_clamp.outputs['Result'], store_glow.inputs['Value'])

    # bb_frame_phase (normalized depth position for rainbow spectrum)
    ring_norm = nodes.new('ShaderNodeMath')
    ring_norm.location = (-600, -350)
    ring_norm.operation = 'DIVIDE'
    ring_norm.inputs[1].default_value = float(max(frame_count, 1))
    links.new(index_node.outputs['Index'], ring_norm.inputs[0])

    store_phase = nodes.new('GeometryNodeStoreNamedAttribute')
    store_phase.location = (150, 500)
    store_phase.data_type = 'FLOAT'
    store_phase.domain = 'POINT'
    store_phase.inputs['Name'].default_value = "bb_frame_phase"
    links.new(store_glow.outputs['Geometry'], store_phase.inputs['Geometry'])
    links.new(ring_norm.outputs['Value'], store_phase.inputs['Value'])

    # bb_edge_flicker (random flicker on snare/hi-hat transients)
    bar_rand = nodes.new('FunctionNodeRandomValue')
    bar_rand.location = (-200, -850)
    bar_rand.data_type = 'FLOAT'
    bar_rand.inputs['Min'].default_value = 0.0
    bar_rand.inputs['Max'].default_value = 1.0
    links.new(index_node.outputs['Index'], bar_rand.inputs['ID'])

    bar_thresh = nodes.new('ShaderNodeMath')
    bar_thresh.location = (0, -850)
    bar_thresh.operation = 'GREATER_THAN'
    bar_thresh.inputs[1].default_value = 0.5
    links.new(bar_rand.outputs['Value'], bar_thresh.inputs[0])

    bar_flash = nodes.new('ShaderNodeMath')
    bar_flash.location = (200, -850)
    bar_flash.operation = 'MULTIPLY'
    links.new(bar_thresh.outputs['Value'], bar_flash.inputs[0])
    links.new(kick_val.outputs[0], bar_flash.inputs[1])

    store_flicker = nodes.new('GeometryNodeStoreNamedAttribute')
    store_flicker.location = (350, 500)
    store_flicker.data_type = 'FLOAT'
    store_flicker.domain = 'POINT'
    store_flicker.inputs['Name'].default_value = "bb_edge_flicker"
    links.new(store_phase.outputs['Geometry'], store_flicker.inputs['Geometry'])
    links.new(bar_flash.outputs['Value'], store_flicker.inputs['Value'])

    # ══════════════════════════════════════════════════════════════════
    # 8. Instance Frames on Mesh Line Points
    # ══════════════════════════════════════════════════════════════════
    inst_frames = nodes.new('GeometryNodeInstanceOnPoints')
    inst_frames.location = (600, 400)
    links.new(store_flicker.outputs['Geometry'], inst_frames.inputs['Points'])
    links.new(frame_info.outputs['Geometry'], inst_frames.inputs['Instance'])
    links.new(combine_scale.outputs['Vector'], inst_frames.inputs['Scale'])
    links.new(combine_rot.outputs['Vector'], inst_frames.inputs['Rotation'])

    # ══════════════════════════════════════════════════════════════════
    # 9. Realize Instances (preserves materials + named attributes)
    # ══════════════════════════════════════════════════════════════════
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (1000, 400)
    links.new(inst_frames.outputs['Instances'], realize.inputs['Geometry'])
    links.new(realize.outputs['Geometry'], output_node.inputs['Geometry'])

    # ══════════════════════════════════════════════════════════════════
    # 10. Apply modifier to visualizer object
    # ══════════════════════════════════════════════════════════════════
    mod_name = "BlenderBeat_Grid_GN"
    mod = viz_obj.modifiers.get(mod_name)
    if mod is None:
        mod = viz_obj.modifiers.new(name=mod_name, type='NODES')
    mod.node_group = node_tree

    print(f"[BlenderBeat] Grid Geometry Nodes created: {frame_count} frames, "
          f"spacing={spacing}m, twist={twist_per_frame}rad/frame")
    return node_tree
