"""
BlenderBeat — Infinite Light Grid: Tunnel Terminus.

Creates a bright glowing haze at the far end of the tunnel,
giving the illusion of infinite depth. Unlike the Black Hole's
void singularity, this is an inverted effect — a white/color
emission point that creates the "light at the end" look.
"""

import bpy
import math


def create_grid_terminus(
    name: str = "BB_GridTerminus",
    radius: float = 2.0,
    location_z: float = -75.0,
    color: tuple = (0.8, 0.9, 1.0),
    emission_strength: float = 25.0,
) -> bpy.types.Object:
    """
    Create a glowing terminus sphere + point light at the tunnel's far end.

    This creates:
    1. A small emissive sphere (the visible "star" at the vanishing point)
    2. A point light casting soft volumetric glow into the tunnel

    Args:
        name: Object name
        radius: Radius of the emissive sphere
        location_z: Z-position (should be past the last frame)
        color: RGB emission color
        emission_strength: Emission intensity

    Returns:
        bpy.types.Object: The terminus sphere object
    """
    # Remove old objects
    for old_name in [name, f"{name}_Light"]:
        old = bpy.data.objects.get(old_name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)

    # ── Emissive Terminus Sphere ──────────────────────────────────────
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    # Create icosphere geometry
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Build simple sphere via bmesh
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=radius)
    bm.to_mesh(mesh)
    bm.free()

    obj.location = (0.0, 0.0, location_z)

    # Create terminus emission material
    mat_name = "BB_Mat_GridTerminus"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()

    output = tree.nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)

    emission = tree.nodes.new('ShaderNodeEmission')
    emission.location = (100, 0)
    emission.inputs['Color'].default_value = (*color, 1.0)
    emission.inputs['Strength'].default_value = emission_strength

    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

    obj.data.materials.append(mat)
    mesh.shade_smooth()

    # Unlink from scene collection (will be linked to preset collection)
    bpy.context.collection.objects.unlink(obj)

    # ── Point Light for ambient glow ──────────────────────────────────
    light_name = f"{name}_Light"
    light_data = bpy.data.lights.new(name=light_name, type='POINT')
    light_data.color = color
    light_data.energy = emission_strength * 50.0
    light_data.shadow_soft_size = radius * 2.0

    light_obj = bpy.data.objects.new(light_name, light_data)
    light_obj.location = (0.0, 0.0, location_z)
    # Will be linked to collection by preset

    print(f"[BlenderBeat] Grid terminus created at Z={location_z}, "
          f"radius={radius}, strength={emission_strength}")
    return obj
