"""
BlenderBeat — Cosmic Blossom Environment & Platform Architecture.

Constructs the awe-inspiring sci-fi cathedral / cosmic temple environment from the reference image:
1. Reflective Mirror Obsidian Lake (vast polished dark mirror reflecting flower & lights)
2. Concentric Stepped Golden Dais Rings directly underneath the blossom
3. Approach Causeway / Ceremonial Pathway reaching into the foreground
4. Foreground Avatar Silhouette / Cosmic Observer anchoring the human scale
"""

import bpy
import bmesh
import math
from typing import Dict, Any


def create_cosmic_environment(
    materials_dict: Dict[str, bpy.types.Material],
    platform_radius: float = 18.0,
    parent_collection: bpy.types.Collection = None,
) -> Dict[str, bpy.types.Object]:
    """
    Generate the reflective temple dais, causeway, and cosmic platform.
    """
    env_objs = {}

    mat_mirror = materials_dict.get('mirror')
    mat_gold = materials_dict.get('gold')
    mat_frame = materials_dict.get('dark_frame')
    mat_vein = materials_dict.get('energy_vein')

    # ─────────────────────────────────────────────────────────────
    # 1. Vast Obsidian Mirror Lake (Ground Floor)
    # ─────────────────────────────────────────────────────────────
    mesh_lake = bpy.data.meshes.new("BB_MirrorLake_Mesh")
    obj_lake = bpy.data.objects.new("BB_Env_MirrorLake", mesh_lake)

    bm_lake = bmesh.new()
    bmesh.ops.create_grid(
        bm_lake,
        x_segments=16,
        y_segments=16,
        size=platform_radius * 1.5,
    )
    bm_lake.to_mesh(mesh_lake)
    bm_lake.free()

    if mat_mirror:
        obj_lake.data.materials.append(mat_mirror)
    obj_lake.location = (0.0, 0.0, -3.2)

    if parent_collection and obj_lake.name not in parent_collection.objects:
        parent_collection.objects.link(obj_lake)
    env_objs['mirror_lake'] = obj_lake

    # ─────────────────────────────────────────────────────────────
    # 2. Concentric Stepped Dais Platform (Directly below Flower)
    # ─────────────────────────────────────────────────────────────
    mesh_dais = bpy.data.meshes.new("BB_TempleDais_Mesh")
    obj_dais = bpy.data.objects.new("BB_Env_TempleDais", mesh_dais)

    if mat_frame:
        obj_dais.data.materials.append(mat_frame)  # Slot 0
    if mat_gold:
        obj_dais.data.materials.append(mat_gold)    # Slot 1
    if mat_vein:
        obj_dais.data.materials.append(mat_vein)    # Slot 2 (LED track)

    bm_dais = bmesh.new()
    dais_radii = [2.2, 3.8, 5.4, 7.2]
    dais_height = 0.12
    dais_segs = 64

    for step_idx, r_step in enumerate(dais_radii):
        z_base = -3.15 + (step_idx * 0.06)
        r_inner = r_step * 0.96

        v_in_b, v_in_t, v_out_b, v_out_t = [], [], [], []
        for i in range(dais_segs):
            th = (i / dais_segs) * 2.0 * math.pi
            ct, st = math.cos(th), math.sin(th)

            v_in_b.append(bm_dais.verts.new((r_inner * ct, r_inner * st, z_base)))
            v_in_t.append(bm_dais.verts.new((r_inner * ct, r_inner * st, z_base + dais_height)))
            v_out_b.append(bm_dais.verts.new((r_step * ct, r_step * st, z_base)))
            v_out_t.append(bm_dais.verts.new((r_step * ct, r_step * st, z_base + dais_height)))

        bm_dais.verts.ensure_lookup_table()
        for i in range(dais_segs):
            nxt = (i + 1) % dais_segs
            # Top concentric ring face
            f_top = bm_dais.faces.new([v_in_t[i], v_in_t[nxt], v_out_t[nxt], v_out_t[i]])
            # Alternating gold track and illuminated runner
            if step_idx % 2 == 1:
                f_top.material_index = 1 if (i % 4 != 0) else 2
            else:
                f_top.material_index = 0

            # Outer rim face (brushed gold rim)
            f_rim = bm_dais.faces.new([v_out_t[i], v_out_t[nxt], v_out_b[nxt], v_out_b[i]])
            f_rim.material_index = 1

    bmesh.ops.recalc_face_normals(bm_dais, faces=bm_dais.faces)
    bm_dais.to_mesh(mesh_dais)
    bm_dais.free()

    obj_dais.location = (0.0, 0.0, 0.0)
    if parent_collection and obj_dais.name not in parent_collection.objects:
        parent_collection.objects.link(obj_dais)
    env_objs['temple_dais'] = obj_dais

    # ─────────────────────────────────────────────────────────────
    # 3. Approach Causeway / Ceremonial Pathway
    # ─────────────────────────────────────────────────────────────
    mesh_causeway = bpy.data.meshes.new("BB_Causeway_Mesh")
    obj_causeway = bpy.data.objects.new("BB_Env_Causeway", mesh_causeway)

    if mat_frame:
        obj_causeway.data.materials.append(mat_frame)  # Slot 0
    if mat_gold:
        obj_causeway.data.materials.append(mat_gold)    # Slot 1
    if mat_vein:
        obj_causeway.data.materials.append(mat_vein)    # Slot 2

    bm_c = bmesh.new()
    width = 1.4
    y_start = 2.0
    y_end = 16.0
    tiles = 14
    z_level = -2.90

    for t in range(tiles):
        y0 = y_start + (t * (y_end - y_start) / tiles)
        y1 = y_start + ((t + 1) * (y_end - y_start) / tiles) - 0.04  # expansion seam

        # 4 vertices for tile
        v0 = bm_c.verts.new((-width * 0.5, y0, z_level))
        v1 = bm_c.verts.new((width * 0.5, y0, z_level))
        v2 = bm_c.verts.new((width * 0.5, y1, z_level))
        v3 = bm_c.verts.new((-width * 0.5, y1, z_level))

        f_tile = bm_c.faces.new([v0, v1, v2, v3])
        f_tile.material_index = 0

        # Lateral gold curbs with energy runner
        v_curb_l0 = bm_c.verts.new((-width * 0.5 - 0.12, y0, z_level + 0.03))
        v_curb_l1 = bm_c.verts.new((-width * 0.5, y0, z_level + 0.03))
        v_curb_l2 = bm_c.verts.new((-width * 0.5, y1, z_level + 0.03))
        v_curb_l3 = bm_c.verts.new((-width * 0.5 - 0.12, y1, z_level + 0.03))

        f_curb_l = bm_c.faces.new([v_curb_l0, v_curb_l1, v_curb_l2, v_curb_l3])
        f_curb_l.material_index = 2 if (t % 2 == 0) else 1

        v_curb_r0 = bm_c.verts.new((width * 0.5, y0, z_level + 0.03))
        v_curb_r1 = bm_c.verts.new((width * 0.5 + 0.12, y0, z_level + 0.03))
        v_curb_r2 = bm_c.verts.new((width * 0.5 + 0.12, y1, z_level + 0.03))
        v_curb_r3 = bm_c.verts.new((width * 0.5, y1, z_level + 0.03))

        f_curb_r = bm_c.faces.new([v_curb_r0, v_curb_r1, v_curb_r2, v_curb_r3])
        f_curb_r.material_index = 2 if (t % 2 == 0) else 1

    bmesh.ops.recalc_face_normals(bm_c, faces=bm_c.faces)
    bm_c.to_mesh(mesh_causeway)
    bm_c.free()

    obj_causeway.location = (0.0, 0.0, 0.0)
    if parent_collection and obj_causeway.name not in parent_collection.objects:
        parent_collection.objects.link(obj_causeway)
    env_objs['causeway'] = obj_causeway

    # ─────────────────────────────────────────────────────────────
    # 4. Cinematic Observer Silhouette (Scale Reference)
    # ─────────────────────────────────────────────────────────────
    mesh_avatar = bpy.data.meshes.new("BB_Avatar_Mesh")
    obj_avatar = bpy.data.objects.new("BB_Env_Observer", mesh_avatar)

    bm_a = bmesh.new()
    # Robed silhouette: tapered cone base + head sphere
    bmesh.ops.create_cone(
        bm_a,
        cap_ends=True,
        segments=16,
        radius1=0.28,
        radius2=0.08,
        depth=1.65,
    )
    # Move cone base to ground
    for v in bm_a.verts:
        v.co.z += 0.825

    # Head sphere
    bmesh.ops.create_uvsphere(
        bm_a,
        u_segments=12,
        v_segments=8,
        radius=0.12,
    )
    for v in list(bm_a.verts)[-12*8:]:
        v.co.z += 1.72

    bm_a.to_mesh(mesh_avatar)
    bm_a.free()

    if mat_frame:
        obj_avatar.data.materials.append(mat_frame)

    # Position on causeway gazing up at flower
    obj_avatar.location = (0.0, 8.5, -2.90)
    obj_avatar.rotation_euler = (0.0, 0.0, 0.0)  # Faces towards center (0,0,0)

    if parent_collection and obj_avatar.name not in parent_collection.objects:
        parent_collection.objects.link(obj_avatar)
    env_objs['observer'] = obj_avatar

    print("[BlenderBeat] Cosmic temple environment, mirror lake, and causeway constructed")
    return env_objs
