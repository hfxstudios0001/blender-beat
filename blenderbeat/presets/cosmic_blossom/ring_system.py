"""
BlenderBeat — Cosmic Blossom Surrounding Mechanical Ring System.

Creates the massive circular sci-fi accelerator ring embracing the flower equator:
1. Master Mechanical Ring:
   - Primary structural circular chassis (dark titanium)
   - Segmented exterior casing panels with expansion gaps
   - Precision radial support brackets & mechanical clamps (brushed gold)
   - Continuous inner runner LED neon track (reactive energy glow)
2. Outer Cosmic Horizon Ring:
   - Secondary delicate thin orbital ring suspended further out
   - Floating counter-rotating orientation
"""

import bpy
import bmesh
import math
from typing import Dict, Any


def create_cosmic_ring_system(
    materials_dict: Dict[str, bpy.types.Material],
    radius: float = 3.6,
    parent_collection: bpy.types.Collection = None,
) -> Dict[str, bpy.types.Object]:
    """
    Generate the equatorial mechanical accelerator ring and outer cosmic horizon ring.
    """
    ring_objs = {}

    mat_frame = materials_dict.get('dark_frame')
    mat_gold = materials_dict.get('gold')
    mat_vein = materials_dict.get('energy_vein')
    mat_crystal = materials_dict.get('crystal')

    # ─────────────────────────────────────────────────────────────
    # 1. Primary Equatorial Accelerator Ring
    # ─────────────────────────────────────────────────────────────
    mesh_accel = bpy.data.meshes.new("BB_Equatorial_Ring_Mesh")
    obj_accel = bpy.data.objects.new("BB_Equatorial_Ring", mesh_accel)

    bm = bmesh.new()

    segments = 64
    r_in = radius * 0.94
    r_mid = radius * 0.98
    r_out = radius * 1.05
    height = 0.06

    # Assign 3 material slots to mesh
    if mat_frame:
        obj_accel.data.materials.append(mat_frame)     # Slot 0: Dark Frame
    if mat_gold:
        obj_accel.data.materials.append(mat_gold)       # Slot 1: Gold Brackets
    if mat_vein:
        obj_accel.data.materials.append(mat_vein)       # Slot 2: Energy LED runner

    # Create concentric profile rings
    v_in_bot = []
    v_in_top = []
    v_mid_bot = []
    v_mid_top = []
    v_out_bot = []
    v_out_top = []

    for i in range(segments):
        theta = (i / segments) * 2.0 * math.pi
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        v_in_bot.append(bm.verts.new((r_in * cos_t, r_in * sin_t, -height * 0.5)))
        v_in_top.append(bm.verts.new((r_in * cos_t, r_in * sin_t, height * 0.5)))

        v_mid_bot.append(bm.verts.new((r_mid * cos_t, r_mid * sin_t, -height * 0.35)))
        v_mid_top.append(bm.verts.new((r_mid * cos_t, r_mid * sin_t, height * 0.35)))

        v_out_bot.append(bm.verts.new((r_out * cos_t, r_out * sin_t, -height * 0.5)))
        v_out_top.append(bm.verts.new((r_out * cos_t, r_out * sin_t, height * 0.5)))

    bm.verts.ensure_lookup_table()

    # Bridge concentric rings into faces with material indices
    for i in range(segments):
        nxt = (i + 1) % segments

        # Inner face (runner channel LED track - Slot 2)
        f_in = bm.faces.new([v_in_bot[i], v_in_bot[nxt], v_in_top[nxt], v_in_top[i]])
        f_in.material_index = 2

        # Top inner bevel (Gold trim - Slot 1)
        f_top_in = bm.faces.new([v_in_top[i], v_in_top[nxt], v_mid_top[nxt], v_mid_top[i]])
        f_top_in.material_index = 1

        # Top main casing (Titanium Frame - Slot 0)
        # Add intermittent expansion notches: every 8th segment is a gold bracket
        is_bracket = (i % 8 == 0 or i % 8 == 1)
        f_top_out = bm.faces.new([v_mid_top[i], v_mid_top[nxt], v_out_top[nxt], v_out_top[i]])
        f_top_out.material_index = 1 if is_bracket else 0

        # Outer perimeter face (Titanium Frame - Slot 0)
        f_out = bm.faces.new([v_out_top[i], v_out_top[nxt], v_out_bot[nxt], v_out_bot[i]])
        f_out.material_index = 1 if is_bracket else 0

        # Bottom main casing
        f_bot_out = bm.faces.new([v_out_bot[i], v_out_bot[nxt], v_mid_bot[nxt], v_mid_bot[i]])
        f_bot_out.material_index = 1 if is_bracket else 0

        # Bottom inner bevel
        f_bot_in = bm.faces.new([v_mid_bot[i], v_mid_bot[nxt], v_in_bot[nxt], v_in_bot[i]])
        f_bot_in.material_index = 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh_accel)
    bm.free()

    # Subtle bevel modifier for metallic edge glints
    bevel_mod = obj_accel.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = 0.008
    bevel_mod.segments = 2
    bevel_mod.limit_method = 'ANGLE'

    # Tilt slightly in space matching the reference image's grand diagonal perspective
    obj_accel.location = (0.0, 0.0, 0.3)
    obj_accel.rotation_euler = (math.radians(-6.0), math.radians(2.0), 0.0)

    if parent_collection and obj_accel.name not in parent_collection.objects:
        parent_collection.objects.link(obj_accel)
    ring_objs['accelerator_ring'] = obj_accel

    # ─────────────────────────────────────────────────────────────
    # 2. Outer Halo Orbital Ring (High Suspended Sci-Fi Horizon)
    # ─────────────────────────────────────────────────────────────
    mesh_halo = bpy.data.meshes.new("BB_Halo_Ring_Mesh")
    obj_halo = bpy.data.objects.new("BB_Halo_Ring", mesh_halo)

    bm_halo = bmesh.new()
    halo_r = radius * 1.55
    halo_seg = 72
    halo_verts = []

    for i in range(halo_seg):
        th = (i / halo_seg) * 2.0 * math.pi
        halo_verts.append(bm_halo.verts.new((halo_r * math.cos(th), halo_r * math.sin(th), 0.0)))

    bm_halo.verts.ensure_lookup_table()
    for i in range(halo_seg):
        bm_halo.edges.new((halo_verts[i], halo_verts[(i + 1) % halo_seg]))

    bm_halo.to_mesh(mesh_halo)
    bm_halo.free()

    # Thin sleek tube via skin & subdivision
    skin_mod = obj_halo.modifiers.new(name="Skin", type='SKIN')
    for v in mesh_halo.skin_vertices[0].data:
        v.radius = (0.006, 0.006)
    sub_mod = obj_halo.modifiers.new(name="Subsurf", type='SUBSURF')
    sub_mod.levels = 1

    if mat_gold:
        obj_halo.data.materials.append(mat_gold)

    # Position high above and tilted
    obj_halo.location = (0.0, 0.0, 3.2)
    obj_halo.rotation_euler = (math.radians(12.0), math.radians(-4.0), math.radians(45.0))

    if parent_collection and obj_halo.name not in parent_collection.objects:
        parent_collection.objects.link(obj_halo)
    ring_objs['halo_ring'] = obj_halo

    # ─────────────────────────────────────────────────────────────
    # 3. Additional Ethereal Halo Rings (Stacked Concentric Halos)
    # ─────────────────────────────────────────────────────────────
    extra_halos = [
        ("BB_Halo_Ring_Mid", radius * 1.85, (0.0, 0.0, 5.0), (math.radians(-8.0), math.radians(6.0), math.radians(20.0))),
        ("BB_Halo_Ring_Upper", radius * 2.20, (0.0, 0.0, 7.5), (math.radians(5.0), math.radians(-3.0), math.radians(65.0))),
    ]
    for h_name, h_r, h_loc, h_rot in extra_halos:
        mesh_h = bpy.data.meshes.new(h_name + "_Mesh")
        obj_h = bpy.data.objects.new(h_name, mesh_h)

        bm_h = bmesh.new()
        h_seg = 72
        h_verts = []
        for i in range(h_seg):
            th = (i / h_seg) * 2.0 * math.pi
            h_verts.append(bm_h.verts.new((h_r * math.cos(th), h_r * math.sin(th), 0.0)))
        bm_h.verts.ensure_lookup_table()
        for i in range(h_seg):
            bm_h.edges.new((h_verts[i], h_verts[(i + 1) % h_seg]))
        bm_h.to_mesh(mesh_h)
        bm_h.free()

        skin_h = obj_h.modifiers.new(name="Skin", type='SKIN')
        for v in mesh_h.skin_vertices[0].data:
            v.radius = (0.005, 0.005)
        sub_h = obj_h.modifiers.new(name="Subsurf", type='SUBSURF')
        sub_h.levels = 1

        if mat_gold:
            obj_h.data.materials.append(mat_gold)
        obj_h.location = h_loc
        obj_h.rotation_euler = h_rot

        if parent_collection and obj_h.name not in parent_collection.objects:
            parent_collection.objects.link(obj_h)
        ring_objs[h_name] = obj_h

    print(f"[BlenderBeat] Surrounding ring system created: R={radius:.2f}m")
    return ring_objs
