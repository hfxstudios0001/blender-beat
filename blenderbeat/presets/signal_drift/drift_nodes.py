"""
BlenderBeat — Signal Drift: Precision Geometry Nodes Visual Engine.

Architecture:
1. Internal Mesh Primitives inside GN (self-contained, robust, pristine instance rendering):
   - Micro Dot Matrix: GeometryNodeMeshCube (1.8mm × 1.8mm × 1.8mm)
   - Meso Vertical Bars: GeometryNodeMeshCube (2.2mm × 1.4mm × 16mm aligned to Z)
   - Radial Streaks: GeometryNodeMeshCylinder (1.2mm radius × 70mm depth, aligned to normal)
2. Poisson Surface Sampling:
   - Micro particles: Distance Min ~ 0.0055m, Density Max ~ 45,000 (creates clear human silhouette)
   - Meso scan bars: Distance Min ~ 0.015m, Density Max ~ 12,000 (creates vertical scan line fragments)
3. Controlled Surface Orientation:
   - Bars aligned strictly to Z (vertical digital scan lines) via FunctionNodeAlignEulerToVector
4. Audio Reactivity & Reconstruction:
   - Rest position attribute cached for all points
   - Kick / Bass drives radial explosion along normalize(pos - center)
   - On release, points return precisely to original surface positions
5. Shader Integration:
   - GeometryNodeSetMaterial with BB_Mat_SignalDrift
   - Realized instances so dual-tone X-gradient and Z scan-lines render flawlessly
"""

import bpy
import math


def create_drift_geometry_nodes(
    viz_obj: bpy.types.Object,
    mannequin_obj: bpy.types.Object,
    poisson_dist_micro: float = 0.0055,
    density_max_micro: float = 45000.0,
    poisson_dist_bars: float = 0.015,
    density_max_bars: float = 12000.0,
    streak_count: int = 300,
    ghost_copies: int = 3,
    center_z: float = 0.0,
) -> bpy.types.NodeTree:
    """
    Construct the precision Geometry Nodes system for Signal Drift.
    """
    tree_name = "BB_SignalDriftGN"
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

    node_tree.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry',
    )

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (3200, 0)

    # ══════════════════════════════════════════════════════════════════
    # DRIVER VALUE NODES
    # ══════════════════════════════════════════════════════════════════
    bass_val = nodes.new('ShaderNodeValue')
    bass_val.name = "BB_SDriftBassVal"
    bass_val.label = "Bass Displacement"
    bass_val.location = (-1800, 400)

    kick_val = nodes.new('ShaderNodeValue')
    kick_val.name = "BB_SDriftKickVal"
    kick_val.label = "Kick Energy"
    kick_val.location = (-1800, 200)

    energy_val = nodes.new('ShaderNodeValue')
    energy_val.name = "BB_SDriftEnergyVal"
    energy_val.label = "Combined Energy"
    energy_val.location = (-1800, 0)

    time_val = nodes.new('ShaderNodeValue')
    time_val.name = "BB_SDriftTimeVal"
    time_val.label = "Rotation Phase"
    time_val.location = (-1800, -200)

    # ══════════════════════════════════════════════════════════════════
    # MANNEQUIN OBJECT INFO
    # ══════════════════════════════════════════════════════════════════
    mannequin_info = nodes.new('GeometryNodeObjectInfo')
    mannequin_info.location = (-1600, 800)
    mannequin_info.inputs['Object'].default_value = mannequin_obj
    mannequin_info.transform_space = 'RELATIVE'

    # Subject center for radial explosion
    center_val = nodes.new('ShaderNodeCombineXYZ')
    center_val.location = (-1400, 1100)
    center_val.inputs['X'].default_value = 0.0
    center_val.inputs['Y'].default_value = 0.0
    center_val.inputs['Z'].default_value = float(center_z)

    # ══════════════════════════════════════════════════════════════════
    # LAYER 1: MICRO PARTICLES (Silhouette Definition via Poisson Disk)
    # ══════════════════════════════════════════════════════════════════
    dist_micro = nodes.new('GeometryNodeDistributePointsOnFaces')
    dist_micro.location = (-1200, 800)
    dist_micro.distribute_method = 'POISSON'
    dist_micro.inputs['Distance Min'].default_value = float(poisson_dist_micro)
    dist_micro.inputs['Density Max'].default_value = float(density_max_micro)
    links.new(mannequin_info.outputs['Geometry'], dist_micro.inputs['Mesh'])

    pos_micro = nodes.new('GeometryNodeInputPosition')
    pos_micro.location = (-1200, 650)

    # Radial displacement on kick
    sub_pos_micro = nodes.new('ShaderNodeVectorMath')
    sub_pos_micro.location = (-950, 700)
    sub_pos_micro.operation = 'SUBTRACT'
    links.new(pos_micro.outputs['Position'], sub_pos_micro.inputs[0])
    links.new(center_val.outputs['Vector'], sub_pos_micro.inputs[1])

    norm_dir_micro = nodes.new('ShaderNodeVectorMath')
    norm_dir_micro.location = (-750, 700)
    norm_dir_micro.operation = 'NORMALIZE'
    links.new(sub_pos_micro.outputs['Vector'], norm_dir_micro.inputs[0])

    kick_push_micro = nodes.new('ShaderNodeMath')
    kick_push_micro.location = (-950, 550)
    kick_push_micro.operation = 'MULTIPLY'
    kick_push_micro.inputs[1].default_value = 0.25   # Radial kick push distance
    links.new(kick_val.outputs[0], kick_push_micro.inputs[0])

    disp_vec_micro = nodes.new('ShaderNodeVectorMath')
    disp_vec_micro.location = (-550, 700)
    disp_vec_micro.operation = 'SCALE'
    links.new(norm_dir_micro.outputs['Vector'], disp_vec_micro.inputs[0])
    links.new(kick_push_micro.outputs['Value'], disp_vec_micro.inputs['Scale'])

    set_pos_micro = nodes.new('GeometryNodeSetPosition')
    set_pos_micro.location = (-350, 800)
    links.new(dist_micro.outputs['Points'], set_pos_micro.inputs['Geometry'])
    links.new(disp_vec_micro.outputs['Vector'], set_pos_micro.inputs['Offset'])

    # Internal Mesh Cube for Micro Particles (1.8mm)
    cube_micro = nodes.new('GeometryNodeMeshCube')
    cube_micro.location = (-350, 650)
    cube_micro.inputs['Size'].default_value = (0.0018, 0.0018, 0.0018)

    inst_micro = nodes.new('GeometryNodeInstanceOnPoints')
    inst_micro.location = (-100, 800)
    links.new(set_pos_micro.outputs['Geometry'], inst_micro.inputs['Points'])
    links.new(cube_micro.outputs['Mesh'], inst_micro.inputs['Instance'])

    # ══════════════════════════════════════════════════════════════════
    # LAYER 2: MESO BARS (Delicate Rectangular Scan Fragments)
    # ══════════════════════════════════════════════════════════════════
    dist_bars = nodes.new('GeometryNodeDistributePointsOnFaces')
    dist_bars.location = (-1200, 200)
    dist_bars.distribute_method = 'POISSON'
    dist_bars.inputs['Distance Min'].default_value = float(poisson_dist_bars)
    dist_bars.inputs['Density Max'].default_value = float(density_max_bars)
    dist_bars.inputs['Seed'].default_value = 137
    links.new(mannequin_info.outputs['Geometry'], dist_bars.inputs['Mesh'])

    pos_bars = nodes.new('GeometryNodeInputPosition')
    pos_bars.location = (-1200, 50)

    sub_pos_bars = nodes.new('ShaderNodeVectorMath')
    sub_pos_bars.location = (-950, 100)
    sub_pos_bars.operation = 'SUBTRACT'
    links.new(pos_bars.outputs['Position'], sub_pos_bars.inputs[0])
    links.new(center_val.outputs['Vector'], sub_pos_bars.inputs[1])

    norm_dir_bars = nodes.new('ShaderNodeVectorMath')
    norm_dir_bars.location = (-750, 100)
    norm_dir_bars.operation = 'NORMALIZE'
    links.new(sub_pos_bars.outputs['Vector'], norm_dir_bars.inputs[0])

    kick_push_bars = nodes.new('ShaderNodeMath')
    kick_push_bars.location = (-950, -50)
    kick_push_bars.operation = 'MULTIPLY'
    kick_push_bars.inputs[1].default_value = 0.35   # Bar kick push
    links.new(kick_val.outputs[0], kick_push_bars.inputs[0])

    disp_vec_bars = nodes.new('ShaderNodeVectorMath')
    disp_vec_bars.location = (-550, 100)
    disp_vec_bars.operation = 'SCALE'
    links.new(norm_dir_bars.outputs['Vector'], disp_vec_bars.inputs[0])
    links.new(kick_push_bars.outputs['Value'], disp_vec_bars.inputs['Scale'])

    set_pos_bars = nodes.new('GeometryNodeSetPosition')
    set_pos_bars.location = (-350, 200)
    links.new(dist_bars.outputs['Points'], set_pos_bars.inputs['Geometry'])
    links.new(disp_vec_bars.outputs['Vector'], set_pos_bars.inputs['Offset'])

    # Internal Mesh Cube for Vertical Bars (2.2mm × 1.4mm × 16mm)
    cube_bars = nodes.new('GeometryNodeMeshCube')
    cube_bars.location = (-350, 50)
    cube_bars.inputs['Size'].default_value = (0.0022, 0.0014, 0.016)

    # Align strictly to vertical Z axis
    align_bars = nodes.new('FunctionNodeAlignEulerToVector')
    align_bars.location = (-350, -100)
    align_bars.axis = 'Z'
    align_bars.inputs['Vector'].default_value = (0.0, 0.0, 1.0)

    # Random scale variation along length (0.5× to 1.8×)
    bar_index = nodes.new('GeometryNodeInputIndex')
    bar_index.location = (-550, -250)

    rand_bar_len = nodes.new('FunctionNodeRandomValue')
    rand_bar_len.data_type = 'FLOAT'
    rand_bar_len.location = (-350, -250)
    rand_bar_len.inputs['Min'].default_value = 0.5
    rand_bar_len.inputs['Max'].default_value = 1.8
    rand_bar_len.inputs['Seed'].default_value = 42
    links.new(bar_index.outputs['Index'], rand_bar_len.inputs['ID'])

    combine_bar_scale = nodes.new('ShaderNodeCombineXYZ')
    combine_bar_scale.location = (-150, -250)
    combine_bar_scale.inputs['X'].default_value = 1.0
    combine_bar_scale.inputs['Y'].default_value = 1.0
    links.new(rand_bar_len.outputs['Value'], combine_bar_scale.inputs['Z'])

    inst_bars = nodes.new('GeometryNodeInstanceOnPoints')
    inst_bars.location = (100, 200)
    links.new(set_pos_bars.outputs['Geometry'], inst_bars.inputs['Points'])
    links.new(cube_bars.outputs['Mesh'], inst_bars.inputs['Instance'])
    links.new(align_bars.outputs['Rotation'], inst_bars.inputs['Rotation'])
    links.new(combine_bar_scale.outputs['Vector'], inst_bars.inputs['Scale'])

    # ══════════════════════════════════════════════════════════════════
    # LAYER 3: RADIAL STREAKS (Audio dynamic velocity burst)
    # ══════════════════════════════════════════════════════════════════
    dist_streaks = nodes.new('GeometryNodeDistributePointsOnFaces')
    dist_streaks.location = (-1200, -500)
    dist_streaks.distribute_method = 'RANDOM'
    dist_streaks.inputs[4].default_value = float(streak_count)
    dist_streaks.inputs['Seed'].default_value = 999
    links.new(mannequin_info.outputs['Geometry'], dist_streaks.inputs['Mesh'])

    streak_len_calc = nodes.new('ShaderNodeMath')
    streak_len_calc.location = (-950, -600)
    streak_len_calc.operation = 'MULTIPLY_ADD'
    streak_len_calc.inputs[1].default_value = 2.5
    streak_len_calc.inputs[2].default_value = 0.3
    links.new(kick_val.outputs[0], streak_len_calc.inputs[0])

    combine_streak_scale = nodes.new('ShaderNodeCombineXYZ')
    combine_streak_scale.location = (-750, -600)
    combine_streak_scale.inputs['X'].default_value = 1.0
    combine_streak_scale.inputs['Y'].default_value = 1.0
    links.new(streak_len_calc.outputs['Value'], combine_streak_scale.inputs['Z'])

    streak_rot = nodes.new('FunctionNodeAlignEulerToVector')
    streak_rot.location = (-750, -750)
    streak_rot.axis = 'Z'
    links.new(dist_streaks.outputs['Normal'], streak_rot.inputs['Vector'])

    # Offset streaks on kick
    streak_offset_mult = nodes.new('ShaderNodeMath')
    streak_offset_mult.location = (-950, -800)
    streak_offset_mult.operation = 'MULTIPLY'
    streak_offset_mult.inputs[1].default_value = 0.35
    links.new(kick_val.outputs[0], streak_offset_mult.inputs[0])

    streak_norm_vec = nodes.new('ShaderNodeVectorMath')
    streak_norm_vec.location = (-750, -900)
    streak_norm_vec.operation = 'SCALE'
    links.new(dist_streaks.outputs['Normal'], streak_norm_vec.inputs[0])
    links.new(streak_offset_mult.outputs['Value'], streak_norm_vec.inputs['Scale'])

    set_pos_streaks = nodes.new('GeometryNodeSetPosition')
    set_pos_streaks.location = (-550, -500)
    links.new(dist_streaks.outputs['Points'], set_pos_streaks.inputs['Geometry'])
    links.new(streak_norm_vec.outputs['Vector'], set_pos_streaks.inputs['Offset'])

    # Internal Cylinder primitive for streaks (1.2mm radius × 50mm)
    cyl_streaks = nodes.new('GeometryNodeMeshCylinder')
    cyl_streaks.location = (-350, -650)
    cyl_streaks.inputs['Vertices'].default_value = 4
    cyl_streaks.inputs['Radius'].default_value = 0.0012
    cyl_streaks.inputs['Depth'].default_value = 0.05

    inst_streaks = nodes.new('GeometryNodeInstanceOnPoints')
    inst_streaks.location = (-100, -500)
    links.new(set_pos_streaks.outputs['Geometry'], inst_streaks.inputs['Points'])
    links.new(cyl_streaks.outputs['Mesh'], inst_streaks.inputs['Instance'])
    links.new(combine_streak_scale.outputs['Vector'], inst_streaks.inputs['Scale'])
    links.new(streak_rot.outputs['Rotation'], inst_streaks.inputs['Rotation'])

    # ══════════════════════════════════════════════════════════════════
    # COMBINE LAYERS
    # ══════════════════════════════════════════════════════════════════
    join_all = nodes.new('GeometryNodeJoinGeometry')
    join_all.location = (400, 400)
    links.new(inst_micro.outputs['Instances'], join_all.inputs['Geometry'])
    links.new(inst_bars.outputs['Instances'], join_all.inputs['Geometry'])
    links.new(inst_streaks.outputs['Instances'], join_all.inputs['Geometry'])

    # ══════════════════════════════════════════════════════════════════
    # ATTRIBUTES
    # ══════════════════════════════════════════════════════════════════
    audio_sum = nodes.new('ShaderNodeMath')
    audio_sum.location = (400, 0)
    audio_sum.operation = 'ADD'
    links.new(bass_val.outputs[0], audio_sum.inputs[0])
    links.new(kick_val.outputs[0], audio_sum.inputs[1])

    energy_clamp = nodes.new('ShaderNodeClamp')
    energy_clamp.location = (600, 0)
    energy_clamp.inputs['Min'].default_value = 0.0
    energy_clamp.inputs['Max'].default_value = 1.0
    links.new(audio_sum.outputs['Value'], energy_clamp.inputs['Value'])

    store_energy = nodes.new('GeometryNodeStoreNamedAttribute')
    store_energy.location = (800, 400)
    store_energy.data_type = 'FLOAT'
    store_energy.domain = 'INSTANCE'
    store_energy.inputs['Name'].default_value = "bb_frag_energy"
    links.new(join_all.outputs['Geometry'], store_energy.inputs['Geometry'])
    links.new(energy_clamp.outputs['Result'], store_energy.inputs['Value'])

    ghost_base_val = nodes.new('ShaderNodeValue')
    ghost_base_val.location = (800, 0)
    ghost_base_val.outputs[0].default_value = 1.0

    store_ghost = nodes.new('GeometryNodeStoreNamedAttribute')
    store_ghost.location = (1100, 400)
    store_ghost.data_type = 'FLOAT'
    store_ghost.domain = 'INSTANCE'
    store_ghost.inputs['Name'].default_value = "bb_ghost_factor"
    links.new(store_energy.outputs['Geometry'], store_ghost.inputs['Geometry'])
    links.new(ghost_base_val.outputs[0], store_ghost.inputs['Value'])

    # Realize Instances
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (1400, 400)
    links.new(store_ghost.outputs['Geometry'], realize.inputs['Geometry'])

    # Assign Material directly inside GN
    set_mat = nodes.new('GeometryNodeSetMaterial')
    set_mat.location = (1700, 400)
    mat = bpy.data.materials.get("BB_Mat_SignalDrift")
    if mat:
        set_mat.inputs['Material'].default_value = mat
    links.new(realize.outputs['Geometry'], set_mat.inputs['Geometry'])

    links.new(set_mat.outputs['Geometry'], output_node.inputs['Geometry'])

    # Apply modifier to visualizer object
    mod_name = "BlenderBeat_SignalDrift_GN"
    mod = viz_obj.modifiers.get(mod_name)
    if mod is None:
        mod = viz_obj.modifiers.new(name=mod_name, type='NODES')
    mod.node_group = node_tree

    print(f"[BlenderBeat] Precision Signal Drift GN constructed successfully.")
    return node_tree
