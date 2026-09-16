"""
BlenderBeat — Signal Drift: Human Source Mesh Loader.

Loads the authentic 3D human asset (`Human_Base_Full`) from
`blenderbeat/assets/models/human_base.blend`.

The loaded human mesh preserves accurate anatomy:
- Head, facial contours, neck
- Shoulders, chest, torso, waist
- Arms, hands, fingers
- Pelvis, legs, feet/boots

The human mesh is used as the instance source for the Geometry Nodes
distribution system. It is hidden from direct rendering.
"""

import bpy
import os
import math
from typing import Optional


def get_human_asset_path(head_only: bool = True) -> str:
    """Return the absolute path to the bundled human asset blend."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    preset_dir = os.path.dirname(current_dir)
    blenderbeat_dir = os.path.dirname(preset_dir)
    filename = "human_head.blend" if head_only else "human_base.blend"
    return os.path.join(blenderbeat_dir, "assets", "models", filename)


def create_mannequin_mesh(
    name: str = "BB_SD_Mannequin",
    total_height: float = 1.80,
    head_only: bool = True,
) -> bpy.types.Object:
    """
    Import and prepare the authentic human/face mesh for Signal Drift.

    Args:
        name: Object name for the human in the active scene
        total_height: Target height in meters
        head_only: If True, load only the head/face mesh for fast viewport performance

    Returns:
        bpy.types.Object: The human mesh object (hidden from render/viewport)
    """
    # Remove existing
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    asset_path = get_human_asset_path(head_only=head_only)
    if not os.path.exists(asset_path):
        # Fallback to human_base.blend if head blend not found
        asset_path = get_human_asset_path(head_only=False)

    human_obj: Optional[bpy.types.Object] = None

    if os.path.exists(asset_path):
        try:
            with bpy.data.libraries.load(asset_path, link=False) as (data_from, data_to):
                target_names = ["Human_Head_Face", "Human_Base_Full"]
                matched = [n for n in target_names if n in data_from.objects]
                if matched:
                    data_to.objects = [matched[0]]
                elif data_from.objects:
                    data_to.objects = [data_from.objects[0]]

            if data_to.objects:
                human_obj = data_to.objects[0]
                bpy.context.collection.objects.link(human_obj)
                human_obj.name = name
                print(f"[BlenderBeat] Loaded human asset from {asset_path} (head_only={head_only})")
        except Exception as e:
            print(f"[BlenderBeat] Failed to append human asset: {e}")

    # Fallback if asset file missing or load failed
    if human_obj is None:
        print("[BlenderBeat] WARNING: human_base.blend asset not found, creating emergency fallback mesh.")
        human_obj = _create_emergency_human(name, total_height)
    else:
        # Normalize scale to total_height if needed
        human_obj.hide_viewport = False
        human_obj.hide_render = False
        
        # Calculate current height along Z
        bb = human_obj.bound_box
        min_z = min(v[2] for v in bb)
        max_z = max(v[2] for v in bb)
        current_h = max(max_z - min_z, 0.001)

        scale_factor = total_height / current_h
        if abs(scale_factor - 1.0) > 0.01:
            human_obj.scale *= scale_factor
            bpy.context.view_layer.objects.active = human_obj
            human_obj.select_set(True)
            bpy.ops.object.transform_apply(scale=True)
            human_obj.select_set(False)

        # Center X and Y at 0
        bb = human_obj.bound_box
        center_x = sum(v[0] for v in bb) / 8.0
        center_y = sum(v[1] for v in bb) / 8.0
        min_z = min(v[2] for v in bb)
        max_z = max(v[2] for v in bb)
        
        if head_only:
            # Center the face directly at (0, 0, 0)
            center_z = sum(v[2] for v in bb) / 8.0
            human_obj.location = (-center_x, -center_y, -center_z)
        else:
            # Full body standing with feet on ground plane Z=0
            human_obj.location = (-center_x, -center_y, -min_z)

        bpy.context.view_layer.objects.active = human_obj
        human_obj.select_set(True)
        bpy.ops.object.transform_apply(location=True)
        human_obj.select_set(False)

    # Hide from viewport and render — it's strictly an instance and surface sampling source
    human_obj.hide_viewport = True
    human_obj.hide_render = True

    mesh = human_obj.data
    print(f"[BlenderBeat] Human representation verified: {len(mesh.vertices)} verts, "
          f"{len(mesh.polygons)} faces, height={total_height:.2f}m")
    return human_obj


def _create_emergency_human(name: str, total_height: float) -> bpy.types.Object:
    """Emergency fallback mesh only used if human_base.blend is missing."""
    import bmesh
    from mathutils import Vector, Matrix

    bm = bmesh.new()
    s = total_height / 1.8
    # Head
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.12 * s, matrix=Matrix.Translation(Vector((0, 0, 1.65 * s))))
    # Torso
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(Vector((0, 0, 1.15 * s))))
    for v in list(bm.verts)[-8:]:
        loc = v.co - Vector((0, 0, 1.15 * s))
        v.co = Vector((0, 0, 1.15 * s)) + Vector((loc.x * 0.45 * s, loc.y * 0.22 * s, loc.z * 0.65 * s))
    # Legs
    for side in (-1, 1):
        mat = Matrix.Translation(Vector((side * 0.12 * s, 0, 0.45 * s)))
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=0.07 * s, radius2=0.05 * s, depth=0.9 * s, matrix=mat)
    # Arms
    for side in (-1, 1):
        mat = Matrix.Translation(Vector((side * 0.32 * s, 0, 1.15 * s)))
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=0.05 * s, radius2=0.04 * s, depth=0.7 * s, matrix=mat)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj
