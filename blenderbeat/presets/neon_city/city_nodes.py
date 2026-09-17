"""
BlenderBeat — Neon Signal City: Procedural City Corridor Geometry Nodes Engine.

Instancing architecture:
1. Skyscraper Towers along left and right building flanks (Y = 10m to 150m)
2. Heavy framing pillars in the immediate foreground and midground (Y = 3m to 120m)
3. Signature vertical LED columns on multiple depth lines
4. Vanishing point terminus portal at deep vanishing point
"""

import bpy


def create_city_geometry_nodes(
    viz_obj: bpy.types.Object,
    bldg_obj: bpy.types.Object,
    pillar_obj: bpy.types.Object,
    light_strip_obj: bpy.types.Object,
    corridor_length: float = 160.0,
    corridor_width: float = 14.0,
    materials: dict = None,
) -> bpy.types.NodeTree:
    """
    Construct the Geometry Nodes system for Neon Signal City.
    """
    tree_name = "BB_NeonCity_GN"
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
    out_node = nodes.new('NodeGroupOutput')
    out_node.location = (2600, 200)

    # ══════════════════════════════════════════════════════════════════
    # DRIVER CHANNELS (Baked Audio)
    # ══════════════════════════════════════════════════════════════════
    bass_val = nodes.new('ShaderNodeValue')
    bass_val.name = "BB_NC_BassVal"
    bass_val.label = "Bass Driver"
    bass_val.location = (-1800, 300)
    bass_val.outputs[0].default_value = 0.0

    kick_val = nodes.new('ShaderNodeValue')
    kick_val.name = "BB_NC_KickVal"
    kick_val.label = "Kick Driver"
    kick_val.location = (-1800, 100)
    kick_val.outputs[0].default_value = 0.0

    # ══════════════════════════════════════════════════════════════════
    # SOURCE OBJECT INFO (ORIGINAL space so Z=-1000 offset is ignored)
    # ══════════════════════════════════════════════════════════════════
    bldg_info = nodes.new('GeometryNodeObjectInfo')
    bldg_info.location = (-1600, 600)
    bldg_info.inputs['Object'].default_value = bldg_obj
    bldg_info.transform_space = 'ORIGINAL'

    pillar_info = nodes.new('GeometryNodeObjectInfo')
    pillar_info.location = (-1600, 0)
    pillar_info.inputs['Object'].default_value = pillar_obj
    pillar_info.transform_space = 'ORIGINAL'

    strip_info = nodes.new('GeometryNodeObjectInfo')
    strip_info.location = (-1600, -600)
    strip_info.inputs['Object'].default_value = light_strip_obj
    strip_info.transform_space = 'ORIGINAL'

    # ══════════════════════════════════════════════════════════════════
    # 1. SKYSCRAPER TOWERS (Left & Right Flanks)
    # ══════════════════════════════════════════════════════════════════
    line_bldg_l = nodes.new('GeometryNodeCurvePrimitiveLine')
    line_bldg_l.location = (-1200, 800)
    line_bldg_l.inputs['Start'].default_value = (-corridor_width * 0.88, 6.0, 0.0)
    line_bldg_l.inputs['End'].default_value = (-corridor_width * 0.88, corridor_length, 0.0)

    resample_bldg_l = nodes.new('GeometryNodeResampleCurve')
    resample_bldg_l.location = (-950, 800)
    resample_bldg_l.inputs['Mode'].default_value = 'Length'
    resample_bldg_l.inputs['Length'].default_value = 14.0
    links.new(line_bldg_l.outputs['Curve'], resample_bldg_l.inputs['Curve'])

    line_bldg_r = nodes.new('GeometryNodeCurvePrimitiveLine')
    line_bldg_r.location = (-1200, 500)
    line_bldg_r.inputs['Start'].default_value = (corridor_width * 0.88, 6.0, 0.0)
    line_bldg_r.inputs['End'].default_value = (corridor_width * 0.88, corridor_length, 0.0)

    resample_bldg_r = nodes.new('GeometryNodeResampleCurve')
    resample_bldg_r.location = (-950, 500)
    resample_bldg_r.inputs['Mode'].default_value = 'Length'
    resample_bldg_r.inputs['Length'].default_value = 14.0
    links.new(line_bldg_r.outputs['Curve'], resample_bldg_r.inputs['Curve'])

    join_bldg_curves = nodes.new('GeometryNodeJoinGeometry')
    join_bldg_curves.location = (-700, 650)
    links.new(resample_bldg_l.outputs['Curve'], join_bldg_curves.inputs['Geometry'])
    links.new(resample_bldg_r.outputs['Curve'], join_bldg_curves.inputs['Geometry'])

    pts_bldg = nodes.new('GeometryNodeCurveToPoints')
    pts_bldg.location = (-500, 650)
    links.new(join_bldg_curves.outputs['Geometry'], pts_bldg.inputs['Curve'])

    # Building scale variation
    rand_bldg_scale = nodes.new('FunctionNodeRandomValue')
    rand_bldg_scale.data_type = 'FLOAT_VECTOR'
    rand_bldg_scale.location = (-500, 450)
    rand_bldg_scale.inputs['Min'].default_value = (0.9, 0.9, 0.8)
    rand_bldg_scale.inputs['Max'].default_value = (1.2, 1.2, 1.35)
    rand_bldg_scale.inputs['Seed'].default_value = 42

    inst_bldg = nodes.new('GeometryNodeInstanceOnPoints')
    inst_bldg.location = (-200, 650)
    links.new(pts_bldg.outputs['Points'], inst_bldg.inputs['Points'])
    links.new(bldg_info.outputs['Geometry'], inst_bldg.inputs['Instance'])
    links.new(rand_bldg_scale.outputs['Value'], inst_bldg.inputs['Scale'])

    set_mat_bldg = nodes.new('GeometryNodeSetMaterial')
    set_mat_bldg.location = (50, 650)
    if materials and "building" in materials:
        set_mat_bldg.inputs['Material'].default_value = materials["building"]
    links.new(inst_bldg.outputs['Instances'], set_mat_bldg.inputs['Geometry'])

    # ══════════════════════════════════════════════════════════════════
    # 2. FRAMING PILLARS (Along Walkway Borders, framing corridor)
    # ══════════════════════════════════════════════════════════════════
    line_pillar_l = nodes.new('GeometryNodeCurvePrimitiveLine')
    line_pillar_l.location = (-1200, 100)
    line_pillar_l.inputs['Start'].default_value = (-corridor_width * 0.42, 3.0, 0.0)
    line_pillar_l.inputs['End'].default_value = (-corridor_width * 0.42, corridor_length * 0.85, 0.0)

    resample_pillar_l = nodes.new('GeometryNodeResampleCurve')
    resample_pillar_l.location = (-950, 100)
    resample_pillar_l.inputs['Mode'].default_value = 'Length'
    resample_pillar_l.inputs['Length'].default_value = 12.0
    links.new(line_pillar_l.outputs['Curve'], resample_pillar_l.inputs['Curve'])

    line_pillar_r = nodes.new('GeometryNodeCurvePrimitiveLine')
    line_pillar_r.location = (-1200, -150)
    line_pillar_r.inputs['Start'].default_value = (corridor_width * 0.42, 3.0, 0.0)
    line_pillar_r.inputs['End'].default_value = (corridor_width * 0.42, corridor_length * 0.85, 0.0)

    resample_pillar_r = nodes.new('GeometryNodeResampleCurve')
    resample_pillar_r.location = (-950, -150)
    resample_pillar_r.inputs['Mode'].default_value = 'Length'
    resample_pillar_r.inputs['Length'].default_value = 12.0
    links.new(line_pillar_r.outputs['Curve'], resample_pillar_r.inputs['Curve'])

    join_pillar_curves = nodes.new('GeometryNodeJoinGeometry')
    join_pillar_curves.location = (-700, 0)
    links.new(resample_pillar_l.outputs['Curve'], join_pillar_curves.inputs['Geometry'])
    links.new(resample_pillar_r.outputs['Curve'], join_pillar_curves.inputs['Geometry'])

    pts_pillars = nodes.new('GeometryNodeCurveToPoints')
    pts_pillars.location = (-500, 0)
    links.new(join_pillar_curves.outputs['Geometry'], pts_pillars.inputs['Curve'])

    inst_pillars = nodes.new('GeometryNodeInstanceOnPoints')
    inst_pillars.location = (-200, 0)
    links.new(pts_pillars.outputs['Points'], inst_pillars.inputs['Points'])
    links.new(pillar_info.outputs['Geometry'], inst_pillars.inputs['Instance'])

    set_mat_pillar = nodes.new('GeometryNodeSetMaterial')
    set_mat_pillar.location = (50, 0)
    if materials and "building" in materials:
        set_mat_pillar.inputs['Material'].default_value = materials["building"]
    links.new(inst_pillars.outputs['Instances'], set_mat_pillar.inputs['Geometry'])

    # ══════════════════════════════════════════════════════════════════
    # 3. HERO VERTICAL LIGHT STRIPS (Multiple Parallel Depth Lines)
    # Line A (Inner walkway pillars): X = ±4.6m (flanking walkway)
    # Line B (Mid flank facade): X = ±9.8m (flanking skyscrapers)
    # Line C (Far outer skyline): X = ±16.0m (outer corridor backdrop)
    # ══════════════════════════════════════════════════════════════════
    line_strips_l1 = nodes.new('GeometryNodeCurvePrimitiveLine')
    line_strips_l1.location = (-1200, -450)
    line_strips_l1.inputs['Start'].default_value = (-4.6, 4.0, 0.0)
    line_strips_l1.inputs['End'].default_value = (-4.6, corridor_length * 0.95, 0.0)

    res_l1 = nodes.new('GeometryNodeResampleCurve')
    res_l1.location = (-950, -450)
    res_l1.inputs['Mode'].default_value = 'Length'
    res_l1.inputs['Length'].default_value = 5.5
    links.new(line_strips_l1.outputs['Curve'], res_l1.inputs['Curve'])

    line_strips_r1 = nodes.new('GeometryNodeCurvePrimitiveLine')
    line_strips_r1.location = (-1200, -600)
    line_strips_r1.inputs['Start'].default_value = (4.6, 4.0, 0.0)
    line_strips_r1.inputs['End'].default_value = (4.6, corridor_length * 0.95, 0.0)

    res_r1 = nodes.new('GeometryNodeResampleCurve')
    res_r1.location = (-950, -600)
    res_r1.inputs['Mode'].default_value = 'Length'
    res_r1.inputs['Length'].default_value = 5.5
    links.new(line_strips_r1.outputs['Curve'], res_r1.inputs['Curve'])

    # Mid flank lines along skyscraper facades
    line_strips_l2 = nodes.new('GeometryNodeCurvePrimitiveLine')
    line_strips_l2.location = (-1200, -750)
    line_strips_l2.inputs['Start'].default_value = (-9.8, 8.0, 0.0)
    line_strips_l2.inputs['End'].default_value = (-9.8, corridor_length * 0.95, 0.0)

    res_l2 = nodes.new('GeometryNodeResampleCurve')
    res_l2.location = (-950, -750)
    res_l2.inputs['Mode'].default_value = 'Length'
    res_l2.inputs['Length'].default_value = 7.0
    links.new(line_strips_l2.outputs['Curve'], res_l2.inputs['Curve'])

    line_strips_r2 = nodes.new('GeometryNodeCurvePrimitiveLine')
    line_strips_r2.location = (-1200, -900)
    line_strips_r2.inputs['Start'].default_value = (9.8, 8.0, 0.0)
    line_strips_r2.inputs['End'].default_value = (9.8, corridor_length * 0.95, 0.0)

    res_r2 = nodes.new('GeometryNodeResampleCurve')
    res_r2.location = (-950, -900)
    res_r2.inputs['Mode'].default_value = 'Length'
    res_r2.inputs['Length'].default_value = 7.0
    links.new(line_strips_r2.outputs['Curve'], res_r2.inputs['Curve'])

    # Far outer skyline lines
    line_strips_l3 = nodes.new('GeometryNodeCurvePrimitiveLine')
    line_strips_l3.location = (-1200, -1050)
    line_strips_l3.inputs['Start'].default_value = (-16.0, 16.0, 0.0)
    line_strips_l3.inputs['End'].default_value = (-16.0, corridor_length * 0.92, 0.0)

    res_l3 = nodes.new('GeometryNodeResampleCurve')
    res_l3.location = (-950, -1050)
    res_l3.inputs['Mode'].default_value = 'Length'
    res_l3.inputs['Length'].default_value = 9.0
    links.new(line_strips_l3.outputs['Curve'], res_l3.inputs['Curve'])

    line_strips_r3 = nodes.new('GeometryNodeCurvePrimitiveLine')
    line_strips_r3.location = (-1200, -1200)
    line_strips_r3.inputs['Start'].default_value = (16.0, 16.0, 0.0)
    line_strips_r3.inputs['End'].default_value = (16.0, corridor_length * 0.92, 0.0)

    res_r3 = nodes.new('GeometryNodeResampleCurve')
    res_r3.location = (-950, -1200)
    res_r3.inputs['Mode'].default_value = 'Length'
    res_r3.inputs['Length'].default_value = 9.0
    links.new(line_strips_r3.outputs['Curve'], res_r3.inputs['Curve'])

    join_strips_curves = nodes.new('GeometryNodeJoinGeometry')
    join_strips_curves.location = (-700, -600)
    links.new(res_l1.outputs['Curve'], join_strips_curves.inputs['Geometry'])
    links.new(res_r1.outputs['Curve'], join_strips_curves.inputs['Geometry'])
    links.new(res_l2.outputs['Curve'], join_strips_curves.inputs['Geometry'])
    links.new(res_r2.outputs['Curve'], join_strips_curves.inputs['Geometry'])
    links.new(res_l3.outputs['Curve'], join_strips_curves.inputs['Geometry'])
    links.new(res_r3.outputs['Curve'], join_strips_curves.inputs['Geometry'])

    pts_strips = nodes.new('GeometryNodeCurveToPoints')
    pts_strips.location = (-500, -600)
    links.new(join_strips_curves.outputs['Geometry'], pts_strips.inputs['Curve'])

    # Light strip random vertical scale and Z height offset
    rand_strip_scale = nodes.new('FunctionNodeRandomValue')
    rand_strip_scale.data_type = 'FLOAT_VECTOR'
    rand_strip_scale.location = (-500, -850)
    rand_strip_scale.inputs['Min'].default_value = (0.85, 0.85, 0.6)
    rand_strip_scale.inputs['Max'].default_value = (1.2, 1.2, 1.6)
    rand_strip_scale.inputs['Seed'].default_value = 101

    inst_strips = nodes.new('GeometryNodeInstanceOnPoints')
    inst_strips.location = (-200, -600)
    links.new(pts_strips.outputs['Points'], inst_strips.inputs['Points'])
    links.new(strip_info.outputs['Geometry'], inst_strips.inputs['Instance'])
    links.new(rand_strip_scale.outputs['Value'], inst_strips.inputs['Scale'])

    # Rotate instances to face slightly inward towards central walkway
    rot_strips = nodes.new('GeometryNodeRotateInstances')
    rot_strips.location = (20, -600)
    links.new(inst_strips.outputs['Instances'], rot_strips.inputs['Instances'])

    set_mat_strips = nodes.new('GeometryNodeSetMaterial')
    set_mat_strips.location = (240, -600)
    if materials and "lights" in materials:
        set_mat_strips.inputs['Material'].default_value = materials["lights"]
    links.new(rot_strips.outputs['Instances'], set_mat_strips.inputs['Geometry'])

    # ══════════════════════════════════════════════════════════════════
    # 4. VANISHING POINT TERMINUS BEACON (Slender Multi-Tier Light Portal)
    # ══════════════════════════════════════════════════════════════════
    cyl_terminus = nodes.new('GeometryNodeMeshCylinder')
    cyl_terminus.location = (-200, -1100)
    cyl_terminus.inputs['Vertices'].default_value = 8
    cyl_terminus.inputs['Radius'].default_value = 0.35
    cyl_terminus.inputs['Depth'].default_value = 80.0

    tf_terminus = nodes.new('GeometryNodeTransform')
    tf_terminus.location = (50, -1100)
    tf_terminus.inputs['Translation'].default_value = (0.0, corridor_length + 2.0, 40.0)
    links.new(cyl_terminus.outputs['Mesh'], tf_terminus.inputs['Geometry'])

    set_mat_term = nodes.new('GeometryNodeSetMaterial')
    set_mat_term.location = (300, -1100)
    if materials and "terminus" in materials:
        set_mat_term.inputs['Material'].default_value = materials["terminus"]
    links.new(tf_terminus.outputs['Geometry'], set_mat_term.inputs['Geometry'])

    # ══════════════════════════════════════════════════════════════════
    # COMBINE ALL CITY COMPONENTS & REALIZE
    # ══════════════════════════════════════════════════════════════════
    join_all = nodes.new('GeometryNodeJoinGeometry')
    join_all.location = (800, 200)
    links.new(set_mat_bldg.outputs['Geometry'], join_all.inputs['Geometry'])
    links.new(set_mat_pillar.outputs['Geometry'], join_all.inputs['Geometry'])
    links.new(set_mat_strips.outputs['Geometry'], join_all.inputs['Geometry'])
    links.new(set_mat_term.outputs['Geometry'], join_all.inputs['Geometry'])

    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (1400, 200)
    links.new(join_all.outputs['Geometry'], realize.inputs['Geometry'])

    links.new(realize.outputs['Geometry'], out_node.inputs['Geometry'])

    # Apply modifier to viz_obj
    mod_name = "BlenderBeat_NeonCity_GN"
    mod = viz_obj.modifiers.get(mod_name) or viz_obj.modifiers.new(name=mod_name, type='NODES')
    mod.node_group = node_tree

    print(f"[BlenderBeat] Neon Signal City Geometry Nodes successfully built.")
    return node_tree
