"""
BlenderBeat — Neon Signal City: Scale Silhouette Figure.

Creates a dark, seated/standing cloaked humanoid figure positioned
in the central foreground/midground walkway.
Provides monumental cinematic scale without distracting from the city architecture.
"""

import bpy
import bmesh
from mathutils import Vector, Matrix


def create_silhouette_figure(
    name: str = "BB_NC_SilhouetteFigure",
    location: tuple = (0.0, 14.0, 0.05),
) -> bpy.types.Object:
    """
    Construct a stylized seated/meditating cloaked figure silhouette.
    """
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm = bmesh.new()

    # Seated cloaked humanoid:
    # 1. Base / Cross-legged lower body drape (ellipsoid mound)
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=16,
        v_segments=12,
        radius=0.45,
        matrix=Matrix.Translation(Vector((0, 0, 0.22))) @ Matrix.Diagonal(Vector((1.3, 1.0, 0.65, 1.0))),
    )

    # 2. Torso / Cloak (tapered cone/capsule)
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=16,
        radius1=0.38,
        radius2=0.22,
        depth=0.75,
        matrix=Matrix.Translation(Vector((0, 0, 0.65))),
    )

    # 3. Hooded head (forward-leaning sphere with hood brim)
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=16,
        v_segments=12,
        radius=0.20,
        matrix=Matrix.Translation(Vector((0, 0.06, 1.12))) @ Matrix.Diagonal(Vector((1.0, 1.15, 1.1, 1.0))),
    )

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(location)

    # Assign pure dark silhouette material
    mat = bpy.data.materials.get("BB_Mat_CitySilhouette")
    if not mat:
        mat = bpy.data.materials.new("BB_Mat_CitySilhouette")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        out = nodes.new("ShaderNodeOutputMaterial")
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = (0.01, 0.01, 0.015, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.95
        mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    obj.data.materials.append(mat)
    bpy.context.scene.collection.objects.link(obj)
    return obj
