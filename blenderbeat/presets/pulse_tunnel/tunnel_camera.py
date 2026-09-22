"""
BlenderBeat — Pulse Tunnel: Camera System.

CRITICAL DESIGN RULE:
═══════════════════════════════════════════════════════════════
THE CAMERA DOES NOT REACT TO THE MUSIC.
NO CAMERA SHAKE. NO CAMERA PULSE. NO CAMERA KICK.
NO AUDIO-DRIVEN CAMERA ZOOM. NO RANDOM CAMERA JITTER.
═══════════════════════════════════════════════════════════════

The camera travels forward at CONSTANT speed through the tunnel.
Smooth, cinematic, completely decoupled from audio signals.
"""

import bpy
import math
from typing import Optional


def setup_pulse_tunnel_camera(
    tunnel_depth: float = 160.0,
    camera_z_start: float = 1.5,
    total_frames: int = 446,
    lens_mm: float = 20.0,
    collection: Optional[bpy.types.Collection] = None,
) -> bpy.types.Object:
    """
    Create a constant-speed forward-traveling camera.

    The camera moves along -Z from z_start toward the tunnel end.
    It travels ~70% of tunnel depth to maintain infinite illusion.

    Args:
        tunnel_depth: Full tunnel depth in meters.
        camera_z_start: Starting Z position (near tunnel entrance).
        total_frames: Total animation frames (from audio analysis).
        lens_mm: Focal length in mm (20mm = ultra-wide).
        collection: Optional collection to link camera into.

    Returns:
        The camera object.
    """
    cam_name = "BB_Camera"

    # Remove existing camera
    existing = bpy.data.objects.get(cam_name)
    if existing:
        # Clear animation data first
        if existing.animation_data and existing.animation_data.action:
            bpy.data.actions.remove(existing.animation_data.action)
        bpy.data.objects.remove(existing, do_unlink=True)

    # Create camera
    cam_data = bpy.data.cameras.new(cam_name)
    cam_data.lens = lens_mm
    cam_data.clip_start = 0.1
    cam_data.clip_end = 500.0

    # Disable DOF (clean sharp tunnel look)
    cam_data.dof.use_dof = False

    cam_obj = bpy.data.objects.new(cam_name, cam_data)

    # Link to collection or scene
    if collection:
        collection.objects.link(cam_obj)
    else:
        bpy.context.scene.collection.objects.link(cam_obj)

    bpy.context.scene.camera = cam_obj

    # ── Animate constant-speed forward motion ──────────────────────
    # Camera looks down -Z axis (rotation = 0,0,0 = looking down -Z by default
    # in Blender's camera convention: camera looks toward its local -Z)
    cam_obj.rotation_euler = (0.0, 0.0, 0.0)

    # Clear any old animation
    cam_obj.animation_data_create()

    # Travel distance = 70% of tunnel depth (leaves rings visible ahead)
    travel_distance = tunnel_depth * 0.7
    z_end = camera_z_start - travel_distance

    for frame in range(1, total_frames + 1):
        t = (frame - 1) / max(total_frames - 1, 1)
        z = camera_z_start - (t * travel_distance)

        # Perfectly centered, no lateral movement
        cam_obj.location = (0.0, 0.0, z)
        cam_obj.keyframe_insert(data_path="location", frame=frame)

    # Smooth linear interpolation for true constant-speed motion
    if cam_obj.animation_data and cam_obj.animation_data.action:
        from ...animation.baking import _get_action_fcurves
        cam_fcurves = _get_action_fcurves(cam_obj, create_action=False)
        if cam_fcurves:
            for fc in cam_fcurves:
                for kf in fc.keyframe_points:
                    kf.interpolation = 'LINEAR'  # Linear = true constant speed

    # NO zoom punch driver
    # NO shake driver
    # NO audio-linked parameters

    print(f"[BlenderBeat] Pulse Tunnel camera: lens={lens_mm}mm, "
          f"Z={camera_z_start:.1f} → {z_end:.1f}, "
          f"frames={total_frames}, ZERO audio reactivity")
    return cam_obj
