"""
BlenderBeat — Infinite Light Grid: Camera System.

Forward flythrough camera looking down the square tunnel corridor.
Features:
- Centered Z-axis forward motion with subtle XY drift
- Beat-reactive zoom punch (kick → focal length increase)
- Audio-reactive camera shake
- Seamless loop motion
"""

import bpy
import math


def setup_grid_camera(
    tunnel_depth: float,
    total_frames: int,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    """
    Create and configure the forward flythrough camera for the light grid.

    The camera starts just behind the first frame and moves forward
    through the tunnel with subtle sinusoidal XY drift for cinematic feel.

    Args:
        tunnel_depth: Total Z-depth of the tunnel (positive value)
        total_frames: Total animation frames
        collection: Collection to link camera into

    Returns:
        bpy.types.Object: The camera object
    """
    cam_name = "BB_Camera"
    cam_obj = bpy.data.objects.get(cam_name)
    if cam_obj is None:
        cam_data = bpy.data.cameras.new(cam_name)
        cam_obj = bpy.data.objects.new(cam_name, cam_data)
        bpy.context.scene.collection.objects.link(cam_obj)

    bpy.context.scene.camera = cam_obj

    # Ultra-wide cinematic lens for dramatic tunnel perspective
    cam_obj.data.lens = 20.0
    cam_obj.data.clip_end = 500.0

    # Point camera down -Z axis (looking into the tunnel)
    cam_obj.rotation_euler = (0.0, 0.0, 0.0)

    # ── Animate Forward Motion ─────────────────────────────────────────
    # Clear existing animation
    if cam_obj.animation_data and cam_obj.animation_data.action:
        bpy.data.actions.remove(cam_obj.animation_data.action)

    cam_obj.animation_data_create()

    # Camera travels a modest portion of the tunnel depth for seamless loop
    # It never reaches the end, maintaining the infinite illusion
    travel_range = min(tunnel_depth * 0.15, 12.0)

    for frame in range(1, total_frames + 1):
        t = (frame - 1) / total_frames

        # Forward Z motion (seamless loop via sine)
        z = 1.0 - travel_range * (0.5 - 0.5 * math.cos(t * 2.0 * math.pi))

        # Subtle XY drift (smooth organic roll)
        x = math.sin(t * 2.0 * math.pi) * 0.12
        y = math.cos(t * 2.0 * math.pi) * 0.08

        cam_obj.location = (x, y, z)
        cam_obj.keyframe_insert(data_path="location", frame=frame)

        # Counter-clockwise rotation around Z (in Blender +Z rotation is CCW when looking from +Z to -Z)
        rot_z = t * 2.0 * math.pi  # Full 360-degree counter-clockwise revolution over sequence
        cam_obj.rotation_euler = (0.0, 0.0, rot_z)
        cam_obj.keyframe_insert(data_path="rotation_euler", frame=frame)

    # Set interpolation to smooth Bezier
    from ...animation.baking import _get_action_fcurves
    cam_fcurves = _get_action_fcurves(cam_obj, create_action=False)
    if cam_fcurves:
        for fc in cam_fcurves:
            for kf in fc.keyframe_points:
                kf.interpolation = 'BEZIER'
                kf.handle_left_type = 'AUTO_CLAMPED'
                kf.handle_right_type = 'AUTO_CLAMPED'

    # ── Zoom Punch Driver ──────────────────────────────────────────────
    viz_obj = bpy.data.objects.get("BB_Visualizer")
    if viz_obj:
        from ...visual.camera import setup_camera_zoom
        setup_camera_zoom(cam_obj, viz_obj, base_lens=20.0, zoom_punch_mm=10.0)

    # Link to collection if not already
    if cam_obj.name not in collection.objects:
        collection.objects.link(cam_obj)

    print(f"[BlenderBeat] Grid camera: {total_frames} frames, "
          f"travel={travel_range:.1f}m, lens=20mm")
    return cam_obj
