"""
BlenderBeat — Master Lotus Petal Geometry.

Directly crafts the iconic crystal lotus leaf from the reference image:
- Majestic wide oval diamond silhouette with slender stem and sharp spear tip
- Convex outer shell / concave inner bowl cupping the glowing energy core
- Golden specular perimeter rim
- Radial internal crystal facets running from base to tip
- Bright incandescent center spine vein channel
"""

import bpy
import math
from typing import Dict, Any


def create_master_petal_mesh(
    name: str = "BB_MasterPetal",
    materials_dict: Dict[str, bpy.types.Material] = None,
    length: float = 7.2,
    max_width: float = 4.8,
    curvature: float = 0.30,
    thickness: float = 0.04,
    u_segments: int = 48,
    v_segments: int = 18,
    width: float = None,
) -> bpy.types.Object:
    if width is not None:
        max_width = width
    old_obj = bpy.data.objects.get(name)
    if old_obj:
        bpy.data.objects.remove(old_obj, do_unlink=True)

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    if materials_dict:
        obj.data.materials.append(materials_dict.get('crystal'))      # 0: Crystal
        obj.data.materials.append(materials_dict.get('gold'))         # 1: Gold frame
        obj.data.materials.append(materials_dict.get('energy_vein'))  # 2: Energy vein

    verts = []
    faces = []
    face_mat_indices = []

    # Parametric lotus petal mesh:
    # Petal grows along +Z (from base Z=0 to tip Z=length)
    # Lateral width along X
    # Thickness / concave curvature along Y
    grid = []
    for i in range(u_segments + 1):
        u = i / float(u_segments)
        row = []

        # Height along petal length:
        z = u * length

        # Natural arch / curve towards inside (-Y):
        # Starts at 0, arches inward gracefully, needle tip points up-inward
        arch_y = -(math.sin(u * math.pi * 0.85) ** 1.3) * (length * curvature)

        # Width profile (diamond lotus envelope):
        # Swells to max width at u = 0.48
        if u < 1.0:
            w = (math.sin(u * math.pi) ** 0.70) * (max_width * 0.5)
        else:
            w = 0.0

        for j in range(v_segments + 1):
            v = (j / float(v_segments)) * 2.0 - 1.0
            x = v * w

            # Transverse concave bowl curvature:
            # Center (v=0) is deepest, edges (v=+-1) curl towards outer convex side (+Y)
            cup_y = (abs(v) ** 1.8) * (0.28 * max_width) * math.sin(u * math.pi)

            # Central glowing vein ridge:
            spine_y = -0.04 * math.sin(u * math.pi) if abs(v) < 0.10 else 0.0

            y = arch_y + cup_y + spine_y

            idx = len(verts)
            verts.append((x, y, z))
            row.append(idx)
        grid.append(row)

    for i in range(u_segments):
        for j in range(v_segments):
            p0 = grid[i][j]
            p1 = grid[i][j + 1]
            p2 = grid[i + 1][j + 1]
            p3 = grid[i + 1][j]
            faces.append((p0, p1, p2, p3))

            v_norm = abs(((j + 0.5) / float(v_segments)) * 2.0 - 1.0)
            if v_norm < 0.10:
                face_mat_indices.append(2)  # Glowing vein
            elif v_norm > 0.90:
                face_mat_indices.append(1)  # Gold rim
            else:
                face_mat_indices.append(0)  # Crystal glass body

    mesh.from_pydata(verts, [], faces)
    mesh.update()

    for poly, mat_idx in zip(mesh.polygons, face_mat_indices):
        poly.material_index = mat_idx

    solid = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    solid.thickness = thickness
    solid.use_even_offset = True
    solid.material_offset_rim = 1

    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.008
    bevel.segments = 2

    for p in mesh.polygons:
        p.use_smooth = True

    return obj
