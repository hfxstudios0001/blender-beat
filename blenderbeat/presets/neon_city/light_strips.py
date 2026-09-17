"""
BlenderBeat — Neon Signal City: Hero Vertical Light Strip Modules.

Creates the signature vertical LED light columns:
- Dark mounting housing / reflector backer
- Emissive diffuse core channel
- Multi-segment vertical light strips for rhythm and variation
"""

import bpy
import bmesh
from mathutils import Vector, Matrix


def create_vertical_light_strip_mesh(name: str = "BB_NC_LightStrip") -> bpy.types.Object:
    """
    Construct a vertical light strip module consisting of:
    - Dark housing backplate (0.35m wide × 0.25m deep × 28.0m tall)
    - Front emissive LED light bar (0.18m wide × 0.1m deep × 27.6m tall)
    Divided into segmented dashes/bars to resemble digital matrix light columns.
    """
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm = bmesh.new()

    # 1. Dark structural housing / backing trough (Z = 0 to 46m)
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, 0.08, 23.0))) @ Matrix.Diagonal(Vector((0.40, 0.22, 46.0, 1.0))),
    )

    # 2. Segmented front glowing light bars (multi-dash light column)
    # 6 distinct segments separated by varying gaps to match reference matrix aesthetic
    segment_heights = [6.0, 8.5, 4.0, 7.5, 9.0, 5.0]
    gap = 0.9
    current_z = 1.0

    for seg_h in segment_heights:
        center_z = current_z + (seg_h / 2.0)
        bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation(Vector((0, -0.05, center_z))) @ Matrix.Diagonal(Vector((0.20, 0.12, seg_h, 1.0))),
        )
        current_z += seg_h + gap

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    # Move prototype mesh far below scene so it never occludes the camera
    obj.location = (0.0, 0.0, -1000.0)
    obj.hide_viewport = False
    obj.hide_render = False
    bpy.context.scene.collection.objects.link(obj)
    return obj


def create_overhead_neon_sign_mesh(name: str = "BB_NC_NeonSign") -> bpy.types.Object:
    """
    Construct a vertical futuristic sign glyph / beacon for midground/deep city focal points.
    """
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm = bmesh.new()

    # Tall vertical banner sign: 1.8m wide × 18m tall × 0.3m depth
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, 0, 9.0))) @ Matrix.Diagonal(Vector((1.8, 0.3, 18.0, 1.0))),
    )

    # Lateral mounting brackets
    for z in (3.0, 9.0, 15.0):
        bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation(Vector((0, 0.5, z))) @ Matrix.Diagonal(Vector((2.2, 0.8, 0.4, 1.0))),
        )

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    # Move prototype mesh far below scene so it never occludes the camera
    obj.location = (0.0, 0.0, -1000.0)
    obj.hide_viewport = False
    obj.hide_render = False
    bpy.context.scene.collection.objects.link(obj)
    return obj
