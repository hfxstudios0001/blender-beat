"""
BlenderBeat — Cosmic Blossom Floating Crystalline Shards & Ambient Spark FX.

Creates the delicate floating diamond/marquise crystalline petals drifting in zero-g:
1. Procedural Master Shard mesh (faceted diamond marquise crystal)
2. Geometry Nodes instancer scattering shards around the blossom with orbital motion
3. High-frequency audio reactivity: shards shimmer and flash on snares/treble
"""

import bpy
import bmesh
import math
from typing import Dict, Any


def create_master_shard_mesh(name: str = "BB_MasterShard") -> bpy.types.Object:
    """
    Construct a faceted, double-pointed crystal shard (marquise diamond cut).
    """
    shard_obj = bpy.data.objects.get(name)
    if shard_obj:
        return shard_obj

    mesh = bpy.data.meshes.new(name)
    shard_obj = bpy.data.objects.new(name, mesh)

    bm = bmesh.new()

    # Diamond crystal profile:
    # Top tip (0, 0, 0.45)
    # Bottom tip (0, 0, -0.45)
    # Equatorial equator: 6 faceted vertices
    v_top = bm.verts.new((0.0, 0.0, 0.45))
    v_bot = bm.verts.new((0.0, 0.0, -0.45))

    equator_r_x = 0.08
    equator_r_y = 0.18  # Elongated petal silhouette

    eq_verts = [
        bm.verts.new((0.0, equator_r_y, 0.0)),
        bm.verts.new((equator_r_x, equator_r_y * 0.5, 0.0)),
        bm.verts.new((equator_r_x, -equator_r_y * 0.5, 0.0)),
        bm.verts.new((0.0, -equator_r_y, 0.0)),
        bm.verts.new((-equator_r_x, -equator_r_y * 0.5, 0.0)),
        bm.verts.new((-equator_r_x, equator_r_y * 0.5, 0.0)),
    ]

    bm.verts.ensure_lookup_table()

    # Build upper pyramid facets
    for i in range(6):
        nxt = (i + 1) % 6
        bm.faces.new([v_top, eq_verts[i], eq_verts[nxt]])

    # Build lower pyramid facets
    for i in range(6):
        nxt = (i + 1) % 6
        bm.faces.new([v_bot, eq_verts[nxt], eq_verts[i]])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    # Flat shading on facets for diamond refraction glints
    for p in mesh.polygons:
        p.use_smooth = False

    return shard_obj


def create_floating_shards_system(
    materials_dict: Dict[str, bpy.types.Material],
    shard_count: int = 40,
    parent_collection: bpy.types.Collection = None,
) -> bpy.types.Object:
    """
    Generate an instanced field of floating faceted crystal shards orbiting the flower.
    """
    master_shard = create_master_shard_mesh()
    mat_shard = materials_dict.get('shard')
    if mat_shard and len(master_shard.data.materials) == 0:
        master_shard.data.materials.append(mat_shard)

    if parent_collection and master_shard.name not in parent_collection.objects:
        parent_collection.objects.link(master_shard)
    master_shard.hide_viewport = True
    master_shard.hide_render = True

    # Main Shard Emitter Object
    mesh_emitter = bpy.data.meshes.new("BB_ShardEmitter_Mesh")
    obj_emitter = bpy.data.objects.new("BB_FloatingShards", mesh_emitter)

    # Geometry Nodes setup for orbital dispersion
    tree_name = "BB_Shards_GN"
    node_tree = bpy.data.node_groups.get(tree_name)
    if node_tree is None:
        node_tree = bpy.data.node_groups.new(tree_name, 'GeometryNodeTree')

    nodes = node_tree.nodes
    links = node_tree.links
    nodes.clear()

    for item in list(node_tree.interface.items_tree):
        if item.item_type in {'SOCKET'}:
            node_tree.interface.remove(item)

    node_tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    out_node = nodes.new('NodeGroupOutput')
    out_node.location = (800, 0)

    # Random points in spherical shell
    pts = nodes.new('GeometryNodeDistributePointsInVolume') if hasattr(bpy.types, 'GeometryNodeDistributePointsInVolume') else None
    # Alternatively, use Points node with random position
    pts_node = nodes.new('GeometryNodePoints')
    pts_node.location = (-400, 0)
    pts_node.inputs['Count'].default_value = shard_count

    # Random position in cylinder/torus volume around flower
    pos_rand = nodes.new('FunctionNodeRandomValue')
    pos_rand.location = (-200, 100)
    pos_rand.data_type = 'FLOAT_VECTOR'
    pos_rand.inputs['Min'].default_value = (-4.5, -4.5, -1.0)
    pos_rand.inputs['Max'].default_value = (4.5, 4.5, 4.0)
    pos_rand.inputs['Seed'].default_value = 42

    set_pos = nodes.new('GeometryNodeSetPosition')
    set_pos.location = (0, 0)
    links.new(pts_node.outputs['Points'], set_pos.inputs['Geometry'])
    links.new(pos_rand.outputs['Value'], set_pos.inputs['Position'])

    # Shard Object Info
    info = nodes.new('GeometryNodeObjectInfo')
    info.location = (0, -200)
    info.inputs['Object'].default_value = master_shard
    info.transform_space = 'RELATIVE'

    # Random rotation
    rot_rand = nodes.new('FunctionNodeRandomValue')
    rot_rand.location = (0, 250)
    rot_rand.data_type = 'FLOAT_VECTOR'
    rot_rand.inputs['Min'].default_value = (-math.pi, -math.pi, -math.pi)
    rot_rand.inputs['Max'].default_value = (math.pi, math.pi, math.pi)
    rot_rand.inputs['Seed'].default_value = 88

    # Random scale
    scale_rand = nodes.new('FunctionNodeRandomValue')
    scale_rand.location = (0, -350)
    scale_rand.data_type = 'FLOAT'
    scale_rand.inputs['Min'].default_value = 0.45  # min
    scale_rand.inputs['Max'].default_value = 1.35  # max
    scale_rand.inputs['Seed'].default_value = 104

    scale_vec = nodes.new('ShaderNodeCombineXYZ')
    scale_vec.location = (200, -350)
    links.new(scale_rand.outputs['Value'], scale_vec.inputs['X'])
    links.new(scale_rand.outputs['Value'], scale_vec.inputs['Y'])
    links.new(scale_rand.outputs['Value'], scale_vec.inputs['Z'])

    # Instance on points
    inst = nodes.new('GeometryNodeInstanceOnPoints')
    inst.location = (300, 0)
    links.new(set_pos.outputs['Geometry'], inst.inputs['Points'])
    links.new(info.outputs['Geometry'], inst.inputs['Instance'])
    links.new(rot_rand.outputs['Value'], inst.inputs['Rotation'])
    links.new(scale_vec.outputs['Vector'], inst.inputs['Scale'])

    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (550, 0)
    links.new(inst.outputs['Instances'], realize.inputs['Geometry'])
    links.new(realize.outputs['Geometry'], out_node.inputs['Geometry'])

    mod = obj_emitter.modifiers.new(name="BlenderBeat_Shards_GN", type='NODES')
    mod.node_group = node_tree

    if mat_shard:
        obj_emitter.data.materials.append(mat_shard)

    if parent_collection and obj_emitter.name not in parent_collection.objects:
        parent_collection.objects.link(obj_emitter)

    print(f"[BlenderBeat] Floating shard system generated ({shard_count} diamond shards)")
    return obj_emitter
