"""
BlenderBeat — Master Ring Geometry Generator.

Creates a high-detail procedural mechanical ring:
- Outer structural ring with industrial beveled rim
- Inner concentric support ring
- 32 segmented radial hydraulic support struts
- Segmented armor panels with bolt indentations
- Recessed amber LED neon channels
- Floating mechanical blocks
"""

import bpy
import math


def create_master_ring_mesh(
    name: str = "BB_MasterRing",
    outer_radius: float = 3.0,
    inner_radius: float = 2.8,
    depth: float = 1.25,
    segments: int = 32,
    mat_led: bpy.types.Material = None,
) -> bpy.types.Object:
    """
    Generate the master corridor section object consisting of:
    1. Cylindrical armor corridor panels facing inward towards camera (MAT_DARK_METAL)
    2. Inward-protruding longitudinal chrome runner rails with specular highlights (MAT_CHROME)
    3. Concentric glowing Amber LED neon rings (MAT_LED_AMBER)
    """
    old_obj = bpy.data.objects.get(name)
    if old_obj:
        bpy.data.objects.remove(old_obj, do_unlink=True)

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    from ...visual.materials_library import (
        create_dark_metal_material,
        create_chrome_material,
        create_amber_led_material,
    )
    mat_dark = create_dark_metal_material()
    mat_chrome = create_chrome_material()
    if mat_led is None:
        mat_led = create_amber_led_material()

    obj.data.materials.append(mat_dark)    # 0: Dark gunmetal
    obj.data.materials.append(mat_chrome)  # 1: Chrome rails
    obj.data.materials.append(mat_led)     # 2: Amber LED neon

    verts = []
    faces = []
    face_mat_indices = []

    radius = outer_radius
    z_f = depth * 0.5
    z_b = -depth * 0.5

    # 1. 36 Hull segments (dark gunmetal) - clean paneling
    hull_segments = 36
    for i in range(hull_segments):
        th0 = (i / hull_segments) * 2.0 * math.pi
        th1 = ((i + 0.94) / hull_segments) * 2.0 * math.pi  # Crisp panel gap
        c0, s0 = math.cos(th0), math.sin(th0)
        c1, s1 = math.cos(th1), math.sin(th1)

        v_base = len(verts)
        verts.append((radius * c0, radius * s0, z_f))
        verts.append((radius * c1, radius * s1, z_f))
        verts.append((radius * c1, radius * s1, z_b))
        verts.append((radius * c0, radius * s0, z_b))
        faces.append((v_base, v_base + 3, v_base + 2, v_base + 1))
        face_mat_indices.append(0)

    # 2. 8 Heavy Longitudinal Chrome Girder Rails
    num_rails = 8
    r_base = radius - 0.05
    r_top = radius - 0.35
    w_half = 0.075

    for k in range(num_rails):
        angle = (k / num_rails) * 2.0 * math.pi
        ca, sa = math.cos(angle), math.sin(angle)
        px, py = -sa, ca

        # Left / right corners
        bl_x, bl_y = r_base * ca - px * w_half, r_base * sa - py * w_half
        br_x, br_y = r_base * ca + px * w_half, r_base * sa + py * w_half
        tl_x, tl_y = r_top * ca - px * (w_half * 0.65), r_top * sa - py * (w_half * 0.65)
        tr_x, tr_y = r_top * ca + px * (w_half * 0.65), r_top * sa + py * (w_half * 0.65)

        vb = len(verts)
        verts.extend([
            (bl_x, bl_y, z_f), (br_x, br_y, z_f), (tr_x, tr_y, z_f), (tl_x, tl_y, z_f),
            (bl_x, bl_y, z_b), (br_x, br_y, z_b), (tr_x, tr_y, z_b), (tl_x, tl_y, z_b)
        ])
        # Top chrome face
        faces.append((vb + 3, vb + 2, vb + 6, vb + 7))
        face_mat_indices.append(1)
        # Left side face
        faces.append((vb + 0, vb + 3, vb + 7, vb + 4))
        face_mat_indices.append(1)
        # Right side face
        faces.append((vb + 2, vb + 1, vb + 5, vb + 6))
        face_mat_indices.append(1)

    # 3. Concentric Primary Glowing Amber LED Neon Ring
    r_neon = radius - 0.22
    neon_w = 0.08
    for i in range(hull_segments):
        th0 = (i / hull_segments) * 2.0 * math.pi
        th1 = ((i + 1) / hull_segments) * 2.0 * math.pi
        c0, s0 = math.cos(th0), math.sin(th0)
        c1, s1 = math.cos(th1), math.sin(th1)

        v_base = len(verts)
        verts.append((r_neon * c0, r_neon * s0, neon_w * 0.5))
        verts.append((r_neon * c1, r_neon * s1, neon_w * 0.5))
        verts.append((r_neon * c1, r_neon * s1, -neon_w * 0.5))
        verts.append((r_neon * c0, r_neon * s0, -neon_w * 0.5))
        faces.append((v_base, v_base + 3, v_base + 2, v_base + 1))
        face_mat_indices.append(2)

    # 4. Secondary Concentric Dashed Neon Accent Strip
    r_neon2 = radius - 0.10
    z_neon2 = depth * 0.38
    for i in range(0, hull_segments, 2):
        th0 = (i / hull_segments) * 2.0 * math.pi
        th1 = ((i + 0.6) / hull_segments) * 2.0 * math.pi
        c0, s0 = math.cos(th0), math.sin(th0)
        c1, s1 = math.cos(th1), math.sin(th1)

        v_base = len(verts)
        verts.append((r_neon2 * c0, r_neon2 * s0, z_neon2 + 0.04))
        verts.append((r_neon2 * c1, r_neon2 * s1, z_neon2 + 0.04))
        verts.append((r_neon2 * c1, r_neon2 * s1, z_neon2 - 0.04))
        verts.append((r_neon2 * c0, r_neon2 * s0, z_neon2 - 0.04))
        faces.append((v_base, v_base + 3, v_base + 2, v_base + 1))
        face_mat_indices.append(2)

    mesh.from_pydata(verts, [], faces)
    mesh.update()

    for poly, mat_idx in zip(mesh.polygons, face_mat_indices):
        poly.material_index = mat_idx

    print(f"[BlenderBeat] Master Ring generated: {len(verts)} verts, {len(faces)} faces, 3 materials")
    return obj
