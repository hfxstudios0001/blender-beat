"""
BlenderBeat — Neon Signal City: Wet Reflective Ground.

Creates a dark wet futuristic street/walkway:
- Raised central pathway / pedestrian corridor with curb borders
- Drainage seams and expansion joints
- Wide wet reflection basins catching glowing towers and atmospheric haze
"""

import bpy
import bmesh
from mathutils import Vector, Matrix


def create_wet_street_mesh(
    name: str = "BB_NC_WetStreet",
    corridor_length: float = 160.0,
    walkway_width: float = 6.0,
    total_width: float = 40.0,
) -> bpy.types.Object:
    """
    Construct the wet street corridor mesh with central raised slab and reflection basins.
    """
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm = bmesh.new()

    half_len = corridor_length / 2.0
    center_y = half_len  # Extends from Y=0 to Y=corridor_length

    # 1. Main wide ground plane (Z = -0.15m, reflecting skyscrapers)
    bmesh.ops.create_grid(
        bm,
        x_segments=16,
        y_segments=48,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, center_y, -0.15))) @ Matrix.Diagonal(Vector((total_width, corridor_length, 1.0, 1.0))),
    )

    # 2. Central elevated walkway / platform slab (Z = 0.0m)
    # Walking path down center of corridor
    bmesh.ops.create_grid(
        bm,
        x_segments=4,
        y_segments=32,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, center_y, 0.0))) @ Matrix.Diagonal(Vector((walkway_width, corridor_length, 1.0, 1.0))),
    )

    # 3. Curb edge borders along walkway (X = ±walkway_width/2)
    curb_w = 0.35
    curb_h = 0.12
    for side in (-1, 1):
        curb_x = side * (walkway_width / 2.0 + curb_w / 2.0)
        bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation(Vector((curb_x, center_y, curb_h / 2.0))) @ Matrix.Diagonal(Vector((curb_w, corridor_length, curb_h, 1.0))),
        )

    # 4. Transverse expansion joint slabs every 10m along walkway
    slab_interval = 8.0
    num_slabs = int(corridor_length / slab_interval)
    for i in range(num_slabs):
        slab_y = (i + 0.5) * slab_interval
        bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation(Vector((0, slab_y, 0.02))) @ Matrix.Diagonal(Vector((walkway_width * 0.96, 0.15, 0.04, 1.0))),
        )

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj
