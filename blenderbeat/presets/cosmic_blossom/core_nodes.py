"""
BlenderBeat — Cosmic Blossom Central Energy Core.

Constructs the luminous celestial singularity at the center of the lotus:
1. Inner Supercharged Singularity Sphere (high-density plasma core)
2. Translucent Crystalline Egg Shell
3. 3 Concentric Gimbal / Gyroscope Rings rotating on distinct axes
4. Vertical Celestial Light Pillar (sharp celestial laser beam shooting up & down)
"""

import bpy
import bmesh
import math
from typing import Dict, Any


def create_energy_core_system(
    materials_dict: Dict[str, bpy.types.Material],
    core_radius: float = 0.95,
    parent_collection: bpy.types.Collection = None,
) -> Dict[str, bpy.types.Object]:
    """
    Generate the central core objects with fixed physical dimensions.
    """
    core_objs = {}

    # 1. Inner Plasma Energy Sphere
    mesh_sphere = bpy.data.meshes.new("BB_Core_InnerSphere")
    obj_sphere = bpy.data.objects.new("BB_Core_InnerSphere", mesh_sphere)

    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=core_radius * 0.72)
    bm.to_mesh(mesh_sphere)
    bm.free()

    mat_core = materials_dict.get('core')
    if mat_core:
        obj_sphere.data.materials.append(mat_core)
    obj_sphere.location = (0.0, 0.0, 0.6)

    if parent_collection and obj_sphere.name not in parent_collection.objects:
        parent_collection.objects.link(obj_sphere)
    core_objs['inner_sphere'] = obj_sphere

    # 2. Outer Translucent Crystalline Egg Shell
    mesh_shell = bpy.data.meshes.new("BB_Core_OuterShell")
    obj_shell = bpy.data.objects.new("BB_Core_OuterShell", mesh_shell)
    bm2 = bmesh.new()
    bmesh.ops.create_icosphere(bm2, subdivisions=3, radius=core_radius * 0.98)
    bm2.to_mesh(mesh_shell)
    bm2.free()

    mat_crystal = materials_dict.get('crystal')
    if mat_crystal:
        obj_shell.data.materials.append(mat_crystal)
    obj_shell.location = (0.0, 0.0, 0.6)

    if parent_collection and obj_shell.name not in parent_collection.objects:
        parent_collection.objects.link(obj_shell)
    core_objs['outer_shell'] = obj_shell

    # 3. Concentric Gyroscopic Rings (3 axes)
    mat_gold = materials_dict.get('gold')
    gyro_configs = [
        ("BB_Core_Gyro_X", core_radius * 1.25, (math.radians(25), 0, 0)),
        ("BB_Core_Gyro_Y", core_radius * 1.50, (0, math.radians(35), 0)),
        ("BB_Core_Gyro_Z", core_radius * 1.75, (math.radians(45), math.radians(45), 0)),
    ]

    for g_name, r, rot in gyro_configs:
        mesh_ring = bpy.data.meshes.new(g_name)
        obj_ring = bpy.data.objects.new(g_name, mesh_ring)

        bm_r = bmesh.new()
        seg = 48
        ring_verts = []
        for s in range(seg):
            angle = (s / seg) * 2.0 * math.pi
            ca, sa = math.cos(angle), math.sin(angle)
            ring_verts.append(bm_r.verts.new((r * ca, r * sa, 0.0)))
        bm_r.verts.ensure_lookup_table()

        for s in range(seg):
            bm_r.edges.new((ring_verts[s], ring_verts[(s + 1) % seg]))

        bm_r.to_mesh(mesh_ring)
        bm_r.free()

        # Skin and Bevel — thin delicate rings
        skin_mod = obj_ring.modifiers.new(name="Skin", type='SKIN')
        # Set vertex skin radius to thin for ethereal halos
        for v in mesh_ring.skin_vertices[0].data:
            v.radius = (0.008, 0.008)
        bevel = obj_ring.modifiers.new(name="Bevel", type='BEVEL')
        bevel.width = 0.006

        if mat_gold:
            obj_ring.data.materials.append(mat_gold)
        obj_ring.location = (0.0, 0.0, 0.6)
        obj_ring.rotation_euler = rot

        if parent_collection and obj_ring.name not in parent_collection.objects:
            parent_collection.objects.link(obj_ring)
        core_objs[g_name] = obj_ring

    # 4. Vertical Celestial Light Pillar (Razor-sharp vertical laser beam)
    mesh_beam = bpy.data.meshes.new("BB_Core_LightBeam")
    obj_beam = bpy.data.objects.new("BB_Core_LightBeam", mesh_beam)
    bm_b = bmesh.new()
    bmesh.ops.create_cone(
        bm_b,
        cap_ends=False,
        segments=24,
        radius1=0.015,
        radius2=0.025,
        depth=18.0,
    )
    bm_b.to_mesh(mesh_beam)
    bm_b.free()

    mat_beam = materials_dict.get('beam')
    if mat_beam:
        obj_beam.data.materials.append(mat_beam)
    obj_beam.location = (0.0, 0.0, 2.0)

    if parent_collection and obj_beam.name not in parent_collection.objects:
        parent_collection.objects.link(obj_beam)
    core_objs['light_beam'] = obj_beam

    print("[BlenderBeat] Central energy core and celestial light beam generated")
    return core_objs
