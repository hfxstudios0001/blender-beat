"""
BlenderBeat — Neon Signal City: Procedural Building & Pillar Modules.

Generates reusable, instanced architectural modules:
1. Master Skyscraper Tower: Tall vertical monolith with setbacks and facade panel reveals
2. Framing Pillar: Heavy foreground structural column with vertical light reveals
3. Midground Tower: Slender vertical spire
"""

import bpy
import bmesh
from mathutils import Vector, Matrix


def create_master_skyscraper_mesh(name: str = "BB_NC_MasterSkyscraper") -> bpy.types.Object:
    """
    Construct a procedural cyberpunk skyscraper mesh with setbacks and vertical reveals.
    """
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm = bmesh.new()

    # Base building dimensions (14m wide × 18m deep × 88m tall)
    # Tier 1 (Base): 0 to 28m
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, 0, 14.0))) @ Matrix.Diagonal(Vector((14.0, 18.0, 28.0, 1.0))),
    )

    # Tier 2 (Setback 1): 28 to 56m
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, 0, 42.0))) @ Matrix.Diagonal(Vector((11.0, 15.0, 28.0, 1.0))),
    )

    # Tier 3 (Setback 2 - Tower Spire): 56 to 80m
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, 0, 68.0))) @ Matrix.Diagonal(Vector((8.0, 11.0, 24.0, 1.0))),
    )

    # Roof Spire detail: 80 to 95m
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, 0, 87.5))) @ Matrix.Diagonal(Vector((2.5, 3.0, 15.0, 1.0))),
    )

    # Vertical facade ribs/buttresses along the front face (facing corridor)
    for rib_x in (-5.5, -2.5, 2.5, 5.5):
        bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation(Vector((rib_x, -9.2, 28.0))) @ Matrix.Diagonal(Vector((0.8, 0.6, 56.0, 1.0))),
        )

    # Overhang balcony ledge at Tier 1 transition (Z = 28m)
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, 0, 28.0))) @ Matrix.Diagonal(Vector((15.0, 19.0, 0.8, 1.0))),
    )

    # Overhang balcony ledge at Tier 2 transition (Z = 56m)
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, 0, 56.0))) @ Matrix.Diagonal(Vector((12.0, 16.0, 0.8, 1.0))),
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


def create_framing_pillar_mesh(name: str = "BB_NC_FramingPillar") -> bpy.types.Object:
    """
    Construct a heavy foreground architectural pillar with geometric bevels and light grooves.
    """
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm = bmesh.new()

    # Main pillar: 2.2m × 3.5m × 38m tall
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, 0, 19.0))) @ Matrix.Diagonal(Vector((2.2, 3.5, 38.0, 1.0))),
    )

    # Plinth base: 3.0m × 4.5m × 2.0m tall
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, 0, 1.0))) @ Matrix.Diagonal(Vector((3.0, 4.5, 2.0, 1.0))),
    )

    # Capital top head: 2.8m × 4.0m × 1.5m
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Translation(Vector((0, 0, 37.0))) @ Matrix.Diagonal(Vector((2.8, 4.0, 1.5, 1.0))),
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
