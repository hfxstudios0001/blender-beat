"""
BlenderBeat — Pulse Tunnel: Atmospheric Lighting & Compositor Setup.

Configures:
1. Pitch-black world background
2. EEVEE-Next raytracing
3. Volumetric scatter cube for subtle atmospheric haze
4. Terminus glow point light at tunnel end
5. Real-time Compositor Fog Glow bloom
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Optional


def setup_pulse_tunnel_lighting(
    collection: bpy.types.Collection,
    tunnel_depth: float = 160.0,
    haze_density: float = 0.0,
    haze_color: tuple = (0.0, 0.0, 0.0),
    bloom_threshold: float = 0.65,
    bloom_size: float = 0.95,
):
    """
    Configure atmospheric lighting and bloom for the Pulse Tunnel.

    Args:
        collection: BB collection to link light objects into.
        tunnel_depth: Full tunnel depth for volumetric scaling.
        haze_density: Fog density (0.0 for pure pitch-black space contrast).
        haze_color: RGB tint for volumetric scatter.
    """
    scene = bpy.context.scene

    # ── 1. Pitch-Black World ───────────────────────────────────────
    if scene.world is None:
        scene.world = bpy.data.worlds.new("BB_World")
    scene.world.use_nodes = True

    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
        bg.inputs["Strength"].default_value = 0.0

    # ── 2. EEVEE-Next Raytracing ───────────────────────────────────
    if hasattr(scene, 'eevee'):
        try:
            scene.eevee.use_raytracing = True
        except (AttributeError, TypeError):
            pass

    # ── 3. Volumetric Atmosphere Cube (Only if haze_density > 0) ───
    vol_name = "BB_PT_Atmosphere"
    vol_obj = bpy.data.objects.get(vol_name)
    if haze_density > 0.0:
        if vol_obj is None:
            mesh = bpy.data.meshes.new(f"{vol_name}_Mesh")
            vol_obj = bpy.data.objects.new(vol_name, mesh)
            bm = bmesh.new()
            bmesh.ops.create_cube(
                bm,
                size=1.0,
                matrix=(
                    Matrix.Translation(Vector((0, 0, -tunnel_depth / 2.0)))
                    @ Matrix.Diagonal(Vector((26.0, 26.0, tunnel_depth + 10.0, 1.0)))
                ),
            )
            bm.to_mesh(mesh)
            bm.free()
            if vol_obj.name not in collection.objects:
                collection.objects.link(vol_obj)

        mat_vol = bpy.data.materials.get("BB_Mat_PT_Atmosphere") or bpy.data.materials.new("BB_Mat_PT_Atmosphere")
        mat_vol.use_nodes = True
        v_tree = mat_vol.node_tree
        v_tree.nodes.clear()

        out_v = v_tree.nodes.new("ShaderNodeOutputMaterial")
        out_v.location = (300, 0)
        scat = v_tree.nodes.new("ShaderNodeVolumeScatter")
        scat.location = (0, 0)
        scat.inputs["Color"].default_value = (*haze_color, 1.0)
        scat.inputs["Density"].default_value = haze_density
        scat.inputs["Anisotropy"].default_value = 0.75
        v_tree.links.new(scat.outputs["Volume"], out_v.inputs["Volume"])

        vol_obj.data.materials.clear()
        vol_obj.data.materials.append(mat_vol)
    else:
        if vol_obj:
            bpy.data.objects.remove(vol_obj, do_unlink=True)

    # ── 4. Terminus Glow Orb (bright white-cyan beacon at tunnel end) ─
    terminus_name = "BB_PT_TerminusGlow"
    terminus_obj = bpy.data.objects.get(terminus_name)
    if terminus_obj is None:
        mesh = bpy.data.meshes.new(terminus_name + "_Mesh")
        terminus_obj = bpy.data.objects.new(terminus_name, mesh)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
        bm.to_mesh(mesh)
        bm.free()
        
        mat_orb = bpy.data.materials.new("BB_Mat_PT_TerminusOrb")
        mat_orb.use_nodes = True
        t_orb = mat_orb.node_tree
        t_orb.nodes.clear()
        out_o = t_orb.nodes.new("ShaderNodeOutputMaterial")
        emit_o = t_orb.nodes.new("ShaderNodeEmission")
        emit_o.inputs["Color"].default_value = (0.85, 0.98, 1.0, 1.0)
        emit_o.inputs["Strength"].default_value = 100.0
        t_orb.links.new(emit_o.outputs["Emission"], out_o.inputs["Surface"])
        
        terminus_obj.data.materials.append(mat_orb)
        if terminus_obj.name not in collection.objects:
            collection.objects.link(terminus_obj)

    terminus_obj.location = (0.0, 0.0, -(tunnel_depth + 2.0))

    # ── 5. Remove entrance light so it doesn't wash out foreground ──
    entrance_name = "BB_PT_EntranceLight"
    entrance_obj = bpy.data.objects.get(entrance_name)
    if entrance_obj:
        bpy.data.objects.remove(entrance_obj, do_unlink=True)

    # ── 6. Real-time Compositor Fog Glow ───────────────────────────
    from ...visual.lighting import setup_realtime_glow_compositor
    setup_realtime_glow_compositor(
        threshold=bloom_threshold,
        size=bloom_size,
    )

    print(f"[BlenderBeat] Pulse Tunnel lighting configured: "
          f"haze_density={haze_density}, tunnel_depth={tunnel_depth}m, "
          f"bloom_threshold={bloom_threshold}, bloom_size={bloom_size}")
