"""
BlenderBeat — Black Hole Singularity Geometry Generator.

Creates the central light-absorbing event horizon void sphere
and surrounding gravitational accretion energy disc.
"""

import bpy
import math
from ...visual.materials_library import (
    create_black_hole_void_material,
    create_amber_led_material,
)


def create_black_hole_singularity(
    name: str = "BB_BlackHole_Singularity",
    radius: float = 2.2,
    location_z: float = -65.0,
) -> bpy.types.Object:
    """
    Create the deep black hole singularity sphere at the tunnel terminus.
    Light stops here; the central circle remains pitch black,
    framed by the concentric glowing rings of the tunnel.
    """
    old_obj = bpy.data.objects.get(name)
    if old_obj:
        bpy.data.objects.remove(old_obj, do_unlink=True)

    # High-subdivision UV Sphere
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = (0.0, 0.0, location_z)

    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=48,
        v_segments=32,
        radius=radius,
    )
    bm.to_mesh(mesh)
    bm.free()

    # Apply pure zero-albedo light-absorbing void material
    mat_void = create_black_hole_void_material()
    obj.data.materials.append(mat_void)

    print(f"[BlenderBeat] Black Hole Singularity created at z={location_z}")
    return obj
