"""
BlenderBeat — Cosmic Blossom Flower Geometry Nodes System.

Procedurally distributes and animates 5 distinct tiers of the cosmic lotus:
Petals are oriented along +Z:
- Normal vector points outward radially in X-Y.
- Tangent angle aligns petal around the perimeter.
- Pitch rotates petal from upright (+Z) outward and downward:
  * Tier 0: Outer drooping sepals (pitch = 110° - pointing down towards lake)
  * Tier 1: Outer flared lotus bowl (pitch = 58° - flared wide open)
  * Tier 2: Middle ascending cup (pitch = 38° - upward cup)
  * Tier 3: Inner steep guard petals (pitch = 22° - protecting core)
  * Tier 4: Core crown bud petals (pitch = 8° - nearly upright around singularity)
"""

import bpy
import math


def create_flower_geometry_nodes(
    viz_obj: bpy.types.Object,
    petal_obj: bpy.types.Object,
    outer_petals: int = 14,
    open_factor: float = 0.55,
) -> bpy.types.NodeTree:
    tree_name = "BB_CosmicBlossom_GN"
    node_tree = bpy.data.node_groups.get(tree_name)
    if node_tree is None:
        node_tree = bpy.data.node_groups.new(tree_name, 'GeometryNodeTree')

    nodes = node_tree.nodes
    links = node_tree.links
    nodes.clear()

    for item in list(node_tree.interface.items_tree):
        if item.item_type in {'SOCKET'}:
            node_tree.interface.remove(item)

    node_tree.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry',
    )

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1800, 0)

    bass_val = nodes.new('ShaderNodeValue')
    bass_val.name = "BB_BlossomBassVal"
    bass_val.label = "Bass Breathing (Driven)"
    bass_val.location = (-1200, 300)

    kick_val = nodes.new('ShaderNodeValue')
    kick_val.name = "BB_BlossomKickVal"
    kick_val.label = "Kick Shockwave (Driven)"
    kick_val.location = (-1200, 100)

    time_val = nodes.new('ShaderNodeValue')
    time_val.name = "BB_BlossomTimeVal"
    time_val.label = "Continuous Time Phase (Driven)"
    time_val.location = (-1200, -100)

    petal_info = nodes.new('GeometryNodeObjectInfo')
    petal_info.location = (-800, -300)
    petal_info.inputs['Object'].default_value = petal_obj
    petal_info.transform_space = 'RELATIVE'

    join_tiers = nodes.new('GeometryNodeJoinGeometry')
    join_tiers.location = (1400, 0)

    # 5 Tiers: (count, ring_radius, scale, pitch_deg_from_vertical, z_elev, wave_tier)
    tiers = [
        # Tier 0: Outer drooping sepals (points downwards: pitch ~ 105°)
        (12, 3.2, 1.25, 105.0 * open_factor, -0.6, 0),
        # Tier 1: Outer flared lotus bowl (pitch ~ 58°)
        (outer_petals, 2.6, 1.15, 58.0 * open_factor, -0.2, 1),
        # Tier 2: Middle ascending cup (pitch ~ 38°)
        (max(int(outer_petals * 0.72), 8), 1.9, 1.00, 38.0 * open_factor, 0.2, 2),
        # Tier 3: Inner steep guard petals (pitch ~ 22°)
        (max(int(outer_petals * 0.55), 6), 1.3, 0.85, 22.0 * open_factor, 0.5, 3),
        # Tier 4: Core crown bud petals (pitch ~ 8° - upright)
        (max(int(outer_petals * 0.40), 4), 0.7, 0.70, 8.0 * open_factor, 0.7, 4),
    ]

    for tier_idx, (count, radius, base_scale, pitch_deg, z_elev, wave_tier) in enumerate(tiers):
        loc_x = -400 + (tier_idx * 300)
        loc_y = 700 - (tier_idx * 320)

        circle = nodes.new('GeometryNodeMeshCircle')
        circle.location = (loc_x - 300, loc_y)
        circle.inputs['Vertices'].default_value = count
        circle.inputs['Radius'].default_value = radius
        circle.fill_type = 'NONE'

        set_z = nodes.new('GeometryNodeSetPosition')
        set_z.location = (loc_x - 100, loc_y)
        links.new(circle.outputs['Mesh'], set_z.inputs['Geometry'])
        set_z.inputs['Offset'].default_value = (0.0, 0.0, z_elev)

        tier_const = nodes.new('ShaderNodeValue')
        tier_const.location = (loc_x - 300, loc_y - 150)
        tier_const.outputs[0].default_value = float(wave_tier)

        tier_delay = nodes.new('ShaderNodeMath')
        tier_delay.location = (loc_x - 150, loc_y - 150)
        tier_delay.operation = 'MULTIPLY'
        tier_delay.inputs[1].default_value = 1.35
        links.new(tier_const.outputs[0], tier_delay.inputs[0])

        time_motion = nodes.new('ShaderNodeMath')
        time_motion.location = (loc_x - 150, loc_y - 250)
        time_motion.operation = 'MULTIPLY'
        time_motion.inputs[1].default_value = 2.0
        links.new(time_val.outputs[0], time_motion.inputs[0])

        kick_motion = nodes.new('ShaderNodeMath')
        kick_motion.location = (loc_x - 150, loc_y - 350)
        kick_motion.operation = 'MULTIPLY'
        kick_motion.inputs[1].default_value = 7.5
        links.new(kick_val.outputs[0], kick_motion.inputs[0])

        wave_time = nodes.new('ShaderNodeMath')
        wave_time.location = (loc_x, loc_y - 250)
        wave_time.operation = 'ADD'
        links.new(time_motion.outputs['Value'], wave_time.inputs[0])
        links.new(kick_motion.outputs['Value'], wave_time.inputs[1])

        wave_phase = nodes.new('ShaderNodeMath')
        wave_phase.location = (loc_x + 150, loc_y - 200)
        wave_phase.operation = 'SUBTRACT'
        links.new(tier_delay.outputs['Value'], wave_phase.inputs[0])
        links.new(wave_time.outputs['Value'], wave_phase.inputs[1])

        wave_sin = nodes.new('ShaderNodeMath')
        wave_sin.location = (loc_x + 300, loc_y - 200)
        wave_sin.operation = 'SINE'
        links.new(wave_phase.outputs['Value'], wave_sin.inputs[0])

        wave_norm = nodes.new('ShaderNodeMath')
        wave_norm.location = (loc_x + 450, loc_y - 200)
        wave_norm.operation = 'MULTIPLY_ADD'
        wave_norm.inputs[1].default_value = 0.5
        wave_norm.inputs[2].default_value = 0.5
        links.new(wave_sin.outputs['Value'], wave_norm.inputs[0])

        wave_pow = nodes.new('ShaderNodeMath')
        wave_pow.location = (loc_x + 600, loc_y - 200)
        wave_pow.operation = 'POWER'
        wave_pow.inputs[1].default_value = 2.2
        links.new(wave_norm.outputs['Value'], wave_pow.inputs[0])

        audio_boost = nodes.new('ShaderNodeMath')
        audio_boost.location = (loc_x + 600, loc_y - 350)
        audio_boost.operation = 'MULTIPLY_ADD'
        audio_boost.inputs[1].default_value = 0.8
        audio_boost.inputs[2].default_value = 0.25
        links.new(kick_val.outputs[0], audio_boost.inputs[0])

        tier_energy = nodes.new('ShaderNodeMath')
        tier_energy.location = (loc_x + 750, loc_y - 250)
        tier_energy.operation = 'MULTIPLY'
        links.new(wave_pow.outputs['Value'], tier_energy.inputs[0])
        links.new(audio_boost.outputs['Value'], tier_energy.inputs[1])

        store_attr = nodes.new('GeometryNodeStoreNamedAttribute')
        store_attr.location = (loc_x + 100, loc_y)
        store_attr.data_type = 'FLOAT'
        store_attr.domain = 'POINT'
        store_attr.inputs['Name'].default_value = "bb_petal_energy"
        links.new(set_z.outputs['Geometry'], store_attr.inputs['Geometry'])
        links.new(tier_energy.outputs['Value'], store_attr.inputs['Value'])

        inst = nodes.new('GeometryNodeInstanceOnPoints')
        inst.location = (loc_x + 350, loc_y + 100)
        links.new(store_attr.outputs['Geometry'], inst.inputs['Points'])
        links.new(petal_info.outputs['Geometry'], inst.inputs['Instance'])

        scale_calc = nodes.new('ShaderNodeMath')
        scale_calc.location = (loc_x + 100, loc_y + 250)
        scale_calc.operation = 'MULTIPLY_ADD'
        scale_calc.inputs[1].default_value = 0.18
        scale_calc.inputs[2].default_value = 1.0
        links.new(bass_val.outputs[0], scale_calc.inputs[0])

        final_scale = nodes.new('ShaderNodeMath')
        final_scale.location = (loc_x + 250, loc_y + 250)
        final_scale.operation = 'MULTIPLY'
        final_scale.inputs[1].default_value = base_scale
        links.new(scale_calc.outputs['Value'], final_scale.inputs[0])

        scale_vec = nodes.new('ShaderNodeCombineXYZ')
        scale_vec.location = (loc_x + 400, loc_y + 250)
        links.new(final_scale.outputs['Value'], scale_vec.inputs['X'])
        links.new(final_scale.outputs['Value'], scale_vec.inputs['Y'])
        links.new(final_scale.outputs['Value'], scale_vec.inputs['Z'])
        links.new(scale_vec.outputs['Vector'], inst.inputs['Scale'])

        # Orientation:
        # Align petal tangent around circle: Align Euler Y to radial normal
        normal = nodes.new('GeometryNodeInputNormal')
        normal.location = (loc_x + 100, loc_y - 50)

        align_rot = nodes.new('FunctionNodeAlignEulerToVector')
        align_rot.location = (loc_x + 250, loc_y - 50)
        align_rot.axis = 'Y'  # Petal normal/facing points outward
        links.new(normal.outputs['Normal'], align_rot.inputs['Vector'])

        # Rotate by pitch angle around local X axis:
        # Tilts +Z petal tip outward from vertical
        rot_eul = nodes.new('FunctionNodeRotateEuler')
        rot_eul.location = (loc_x + 450, loc_y - 50)
        rot_eul.space = 'LOCAL'
        links.new(align_rot.outputs['Rotation'], rot_eul.inputs['Rotation'])

        pitch_rad = math.radians(pitch_deg)
        rot_eul.inputs['Rotate By'].default_value = (pitch_rad, 0.0, 0.0)
        links.new(rot_eul.outputs['Rotation'], inst.inputs['Rotation'])

        links.new(inst.outputs['Instances'], join_tiers.inputs['Geometry'])

    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (1600, 0)
    links.new(join_tiers.outputs['Geometry'], realize.inputs['Geometry'])
    links.new(realize.outputs['Geometry'], output_node.inputs['Geometry'])

    mod_name = "BlenderBeat_Blossom_GN"
    mod = viz_obj.modifiers.get(mod_name)
    if mod is None:
        mod = viz_obj.modifiers.new(name=mod_name, type='NODES')
    mod.node_group = node_tree

    print("[BlenderBeat] Flower Geometry Nodes configured for vertical lotus petals")
    return node_tree
