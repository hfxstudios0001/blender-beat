"""
BlenderBeat — Infinite Black Hole Tunnel Geometry Nodes Engine.

Instantiates N master rings along negative Z depth, applies alternating
group rotations (+1.0, -0.5, +0.25), distributes floating asteroid debris,
and sets up dynamic LED chase wave propagation down the tunnel.
"""

import bpy
import math
from typing import Optional


def create_tunnel_geometry_nodes(
    viz_obj: bpy.types.Object,
    ring_obj: bpy.types.Object,
    ring_count: int = 50,
    spacing: float = 1.2,
    debris_count: int = 60,
) -> bpy.types.NodeTree:
    """
    Constructs the Geometry Nodes modifier tree for the tunnel.
    """
    tree_name = "BB_TunnelGeometryNodes"
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

    # Inputs
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1200, 0)
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1600, 0)

    # Internal Value Nodes for robust per-frame driver evaluation
    bass_val = nodes.new('ShaderNodeValue')
    bass_val.name = "BB_TunnelBassVal"
    bass_val.label = "Bass Expansion (Driven)"
    bass_val.location = (-1000, 200)

    kick_val = nodes.new('ShaderNodeValue')
    kick_val.name = "BB_TunnelKickVal"
    kick_val.label = "Kick Pulse (Driven)"
    kick_val.location = (-1000, 0)

    time_val = nodes.new('ShaderNodeValue')
    time_val.name = "BB_TunnelTimeVal"
    time_val.label = "Flythrough Phase (Driven)"
    time_val.location = (-1000, -200)

    # 1. Mesh Line for ring positions along Z axis (0 down to -tunnel_depth)
    line = nodes.new('GeometryNodeMeshLine')
    line.location = (-800, 400)
    line.inputs['Count'].default_value = ring_count
    line.inputs['Start Location'].default_value = (0.0, 0.0, 0.0)
    line.inputs['Offset'].default_value = (0.0, 0.0, -spacing)

    # 2. Object Info to fetch Master Ring mesh
    ring_info = nodes.new('GeometryNodeObjectInfo')
    ring_info.location = (-800, 100)
    ring_info.inputs['Object'].default_value = ring_obj
    ring_info.transform_space = 'RELATIVE'

    # 3. Dynamic scale per ring (Bass breathing + Kick shockwave)
    # scale = 1.0 + (bass * 0.15) + (kick * 0.08)
    scale_add1 = nodes.new('ShaderNodeMath')
    scale_add1.location = (-600, 200)
    scale_add1.operation = 'MULTIPLY_ADD'
    scale_add1.inputs[1].default_value = 0.18
    links.new(bass_val.outputs[0], scale_add1.inputs[0])
    scale_add1.inputs[2].default_value = 1.0

    scale_add2 = nodes.new('ShaderNodeMath')
    scale_add2.location = (-400, 200)
    scale_add2.operation = 'MULTIPLY_ADD'
    scale_add2.inputs[1].default_value = 0.10
    links.new(kick_val.outputs[0], scale_add2.inputs[0])
    links.new(scale_add1.outputs['Value'], scale_add2.inputs[2])

    combine_ring_scale = nodes.new('ShaderNodeCombineXYZ')
    combine_ring_scale.location = (-200, 200)
    links.new(scale_add2.outputs['Value'], combine_ring_scale.inputs['X'])
    links.new(scale_add2.outputs['Value'], combine_ring_scale.inputs['Y'])
    combine_ring_scale.inputs['Z'].default_value = 1.0

    # ──────────────────────────────────────────────────────────────────
    # 4. PER-RING TRAVELING SHOCKWAVE PULSE (bb_ring_glow attribute)
    # ──────────────────────────────────────────────────────────────────
    # Each ring gets a unique glow energy:
    #   wave = sin( (index * wave_freq) - (kick * wave_speed) )
    #   glow = clamp( wave * bass + kick * 0.6, 0.15, 1.0 )
    # This creates a visible pulse traveling down the tunnel on every kick.

    index_node = nodes.new('GeometryNodeInputIndex')
    index_node.location = (-800, -500)

    # index * wave_freq (spread the wave across ring indices)
    wave_freq = nodes.new('ShaderNodeMath')
    wave_freq.location = (-600, -500)
    wave_freq.operation = 'MULTIPLY'
    wave_freq.inputs[1].default_value = 0.55  # radians per ring index
    links.new(index_node.outputs['Index'], wave_freq.inputs[0])

    # Continuous traveling pulse motion:
    # wave_offset = (time_val * 2.0) + (kick_val * 6.0)
    time_motion = nodes.new('ShaderNodeMath')
    time_motion.location = (-800, -650)
    time_motion.operation = 'MULTIPLY'
    time_motion.inputs[1].default_value = 2.0
    links.new(time_val.outputs[0], time_motion.inputs[0])

    kick_speed = nodes.new('ShaderNodeMath')
    kick_speed.location = (-800, -750)
    kick_speed.operation = 'MULTIPLY'
    kick_speed.inputs[1].default_value = 6.0
    links.new(kick_val.outputs[0], kick_speed.inputs[0])

    travel_offset = nodes.new('ShaderNodeMath')
    travel_offset.location = (-600, -650)
    travel_offset.operation = 'ADD'
    links.new(time_motion.outputs['Value'], travel_offset.inputs[0])
    links.new(kick_speed.outputs['Value'], travel_offset.inputs[1])

    # (index * freq) - travel_offset
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

    # Remap sin from [-1,1] to [0,1]: (sin + 1) * 0.5
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

    # Sharpen the wave with power curve (contrast): wave^2.5
    wave_power = nodes.new('ShaderNodeMath')
    wave_power.location = (350, -550)
    wave_power.operation = 'POWER'
    wave_power.inputs[1].default_value = 2.5
    links.new(wave_remap_half.outputs['Value'], wave_power.inputs[0])

    # Modulate wave by audio energy (bass + kick) with gain booster
    audio_energy = nodes.new('ShaderNodeMath')
    audio_energy.location = (200, -700)
    audio_energy.operation = 'ADD'
    links.new(bass_val.outputs[0], audio_energy.inputs[0])
    links.new(kick_val.outputs[0], audio_energy.inputs[1])

    audio_gain = nodes.new('ShaderNodeMath')
    audio_gain.location = (350, -700)
    audio_gain.operation = 'MULTIPLY'
    audio_gain.inputs[1].default_value = 2.4  # Boost to full [0..1] range
    links.new(audio_energy.outputs['Value'], audio_gain.inputs[0])

    wave_pulse = nodes.new('ShaderNodeMath')
    wave_pulse.location = (500, -600)
    wave_pulse.operation = 'MULTIPLY'
    links.new(wave_power.outputs['Value'], wave_pulse.inputs[0])
    links.new(audio_gain.outputs['Value'], wave_pulse.inputs[1])

    # Add transient kick punch directly
    kick_transient = nodes.new('ShaderNodeMath')
    kick_transient.location = (500, -750)
    kick_transient.operation = 'MULTIPLY'
    kick_transient.inputs[1].default_value = 1.6  # Punchy kick transient
    links.new(kick_val.outputs[0], kick_transient.inputs[0])

    total_pulse = nodes.new('ShaderNodeMath')
    total_pulse.location = (700, -650)
    total_pulse.operation = 'ADD'
    links.new(wave_pulse.outputs['Value'], total_pulse.inputs[0])
    links.new(kick_transient.outputs['Value'], total_pulse.inputs[1])

    # Clamp to full [0.0, 1.0] range
    glow_clamp = nodes.new('ShaderNodeClamp')
    glow_clamp.location = (900, -650)
    glow_clamp.inputs['Min'].default_value = 0.0
    glow_clamp.inputs['Max'].default_value = 1.0
    links.new(total_pulse.outputs['Value'], glow_clamp.inputs['Value'])

    # Store as named attribute "bb_ring_glow" on the mesh line points
    store_glow = nodes.new('GeometryNodeStoreNamedAttribute')
    store_glow.location = (-50, 400)
    store_glow.data_type = 'FLOAT'
    store_glow.domain = 'POINT'
    store_glow.inputs['Name'].default_value = "bb_ring_glow"
    links.new(line.outputs['Mesh'], store_glow.inputs['Geometry'])
    links.new(glow_clamp.outputs['Result'], store_glow.inputs['Value'])

    # Also compute normalized ring phase [0..1] for rainbow spectrum hue
    ring_norm = nodes.new('ShaderNodeMath')
    ring_norm.location = (-600, -350)
    ring_norm.operation = 'DIVIDE'
    ring_norm.inputs[1].default_value = float(max(ring_count, 1))
    links.new(index_node.outputs['Index'], ring_norm.inputs[0])

    store_phase = nodes.new('GeometryNodeStoreNamedAttribute')
    store_phase.location = (150, 400)
    store_phase.data_type = 'FLOAT'
    store_phase.domain = 'POINT'
    store_phase.inputs['Name'].default_value = "bb_ring_phase"
    links.new(store_glow.outputs['Geometry'], store_phase.inputs['Geometry'])
    links.new(ring_norm.outputs['Value'], store_phase.inputs['Value'])

    # ──────────────────────────────────────────────────────────────────
    # 4b. RANDOM BAR FLICKER (bb_bar_flicker attribute)
    # ──────────────────────────────────────────────────────────────────
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
    store_flicker.location = (350, 400)
    store_flicker.data_type = 'FLOAT'
    store_flicker.domain = 'POINT'
    store_flicker.inputs['Name'].default_value = "bb_bar_flicker"
    links.new(store_phase.outputs['Geometry'], store_flicker.inputs['Geometry'])
    links.new(bar_flash.outputs['Value'], store_flicker.inputs['Value'])

    # ──────────────────────────────────────────────────────────────────
    # 5. Seamless Corridor Alignment (Rails continuous along corridor)
    # ──────────────────────────────────────────────────────────────────
    combine_rot = nodes.new('ShaderNodeCombineXYZ')
    combine_rot.location = (200, -300)
    combine_rot.inputs['X'].default_value = 0.0
    combine_rot.inputs['Y'].default_value = 0.0
    combine_rot.inputs['Z'].default_value = 0.0

    # 6. Instance Rings on Points of Mesh Line
    inst_rings = nodes.new('GeometryNodeInstanceOnPoints')
    inst_rings.location = (600, 300)
    links.new(store_flicker.outputs['Geometry'], inst_rings.inputs['Points'])
    links.new(ring_info.outputs['Geometry'], inst_rings.inputs['Instance'])
    links.new(combine_ring_scale.outputs['Vector'], inst_rings.inputs['Scale'])
    links.new(combine_rot.outputs['Vector'], inst_rings.inputs['Rotation'])

    # 7. Optional Debris (only if debris_count > 0)
    if debris_count > 0:
        debris_line = nodes.new('GeometryNodeMeshLine')
        debris_line.location = (200, -100)
        debris_line.inputs['Count'].default_value = debris_count
        debris_line.inputs['Start Location'].default_value = (0.0, 0.0, -2.0)
        debris_line.inputs['Offset'].default_value = (0.0, 0.0, -spacing * 0.8)

        rand_vec = nodes.new('FunctionNodeRandomValue')
        rand_vec.location = (200, -300)
        rand_vec.data_type = 'FLOAT_VECTOR'
        rand_vec.inputs['Min'].default_value = (-2.2, -2.2, -1.0)
        rand_vec.inputs['Max'].default_value = (2.2, 2.2, 1.0)

        set_debris_pos = nodes.new('GeometryNodeSetPosition')
        set_debris_pos.location = (450, -100)
        links.new(debris_line.outputs['Mesh'], set_debris_pos.inputs['Geometry'])
        links.new(rand_vec.outputs['Value'], set_debris_pos.inputs['Offset'])

        rock_mesh = nodes.new('GeometryNodeMeshIcoSphere')
        rock_mesh.location = (450, -300)
        rock_mesh.inputs['Radius'].default_value = 0.22
        rock_mesh.inputs['Subdivisions'].default_value = 1

        inst_debris = nodes.new('GeometryNodeInstanceOnPoints')
        inst_debris.location = (700, -100)
        links.new(set_debris_pos.outputs['Geometry'], inst_debris.inputs['Points'])
        links.new(rock_mesh.outputs['Mesh'], inst_debris.inputs['Instance'])

        from ...visual.materials_library import create_dark_metal_material
        mat_rock = create_dark_metal_material("BB_Mat_DebrisRock")
        set_rock_mat = nodes.new('GeometryNodeSetMaterial')
        set_rock_mat.location = (900, -100)
        set_rock_mat.inputs['Material'].default_value = mat_rock
        links.new(inst_debris.outputs['Instances'], set_rock_mat.inputs['Geometry'])

        join_geo = nodes.new('GeometryNodeJoinGeometry')
        join_geo.location = (1100, 200)
        links.new(inst_rings.outputs['Instances'], join_geo.inputs['Geometry'])
        links.new(set_rock_mat.outputs['Geometry'], join_geo.inputs['Geometry'])
        final_instances = join_geo.outputs['Geometry']
    else:
        final_instances = inst_rings.outputs['Instances']

    # 8. Realize Instances to preserve materials and attributes
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (1300, 200)
    links.new(final_instances, realize.inputs['Geometry'])
    links.new(realize.outputs['Geometry'], output_node.inputs['Geometry'])

    # Apply modifier to visualizer object
    mod_name = "BlenderBeat_Tunnel_GN"
    mod = viz_obj.modifiers.get(mod_name)
    if mod is None:
        mod = viz_obj.modifiers.new(name=mod_name, type='NODES')
    mod.node_group = node_tree

    print(f"[BlenderBeat] Tunnel Geometry Nodes created: {ring_count} rings, {debris_count} debris")
    return node_tree
