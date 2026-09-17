"""
BlenderBeat — Neon Signal City: Stable Cinematic Camera.

CRITICAL USER MANDATE:
- ABSOLUTELY NO CAMERA SHAKE.
- Zero per-frame random camera noise.
- Zero kick camera jitter.
- The camera remains stable at human street eye-level (~1.15m).
- Subtle, perfectly smooth forward glide down the corridor.
"""

import bpy
import math


def setup_city_camera(
    corridor_length: float = 160.0,
    camera_z: float = 1.15,
    camera_start_y: float = -2.0,
    total_frames: int = 446,
    lens_mm: float = 24.0,
    glide_distance: float = 12.0,
    camera_reactivity: float = 0.0,
    collection: bpy.types.Collection = None,
) -> bpy.types.Object:
    """
    Construct the stable cinematic camera for Neon Signal City.

    Args:
        corridor_length: Total length of the city corridor
        camera_z: Camera eye-level height in meters (1.15m seated perspective)
        camera_start_y: Initial Y position (looking into corridor)
        total_frames: Total sequence frames
        lens_mm: Cinematic focal length (24mm wide angle matches reference majestic verticality)
        glide_distance: Total smooth forward glide distance across entire song
        camera_reactivity: Audio reactivity scale (defaults strictly to 0.0)
        collection: Destination collection

    Returns:
        bpy.types.Object: Camera object
    """
    cam_name = "BB_Camera"
    cam_obj = bpy.data.objects.get(cam_name)
    if cam_obj is None:
        cam_data = bpy.data.cameras.new(cam_name)
        cam_obj = bpy.data.objects.new(cam_name, cam_data)
        bpy.context.scene.collection.objects.link(cam_obj)

    bpy.context.scene.camera = cam_obj

    # Cinematic wide lens setup (24mm for towering perspective)
    cam_obj.data.lens = lens_mm
    cam_obj.data.clip_start = 0.1
    cam_obj.data.clip_end = 400.0

    # Clear constraints to maintain pure, rock-solid orientation
    cam_obj.constraints.clear()

    # Orientation: Looking forward (+Y) tilted slightly upward (85.5 degrees on X)
    # matching reference composition: bottom 1/4 wet reflections, center silhouette, upper 3/4 towering light towers
    cam_obj.rotation_mode = 'XYZ'
    tilt_rad = math.radians(85.5)
    cam_obj.rotation_euler = (tilt_rad, 0.0, 0.0)

    # ── Deterministic, Smooth Cinematic Glide (NO RANDOM NOISE) ───────
    if cam_obj.animation_data and cam_obj.animation_data.action:
        bpy.data.actions.remove(cam_obj.animation_data.action)

    cam_obj.animation_data_create()

    # Smooth forward glide from camera_start_y over total_frames
    for frame in range(1, total_frames + 1):
        t = (frame - 1) / max(total_frames, 1)
        current_y = camera_start_y + (t * glide_distance)
        cam_obj.location = (0.0, current_y, camera_z)
        cam_obj.keyframe_insert(data_path="location", frame=frame)
        cam_obj.rotation_euler = (tilt_rad, 0.0, 0.0)
        cam_obj.keyframe_insert(data_path="rotation_euler", frame=frame)

    print(f"[BlenderBeat] Stable cinematic camera configured at Z={camera_z:.2f}m (24mm lens, Shake=0.0).")
    return cam_obj
