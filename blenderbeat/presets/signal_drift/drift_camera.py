"""
BlenderBeat — Signal Drift: Camera System.

Slow 360° orbit camera around the spectral apparition with:
- Cinematic 35mm lens (tighter framing than tunnel presets)
- Smooth circular orbit at configurable radius
- Slight vertical sinusoidal bob for organic feel
- Beat-reactive zoom punch on kick
- Audio-reactive camera shake on onset transients
"""

import bpy
import math


def setup_drift_camera(
    orbit_radius: float = 4.0,
    orbit_height: float = 1.2,
    total_frames: int = 446,
    lens_mm: float = 35.0,
    target_z: float = 0.0,
    collection: bpy.types.Collection = None,
) -> bpy.types.Object:
    """
    Create and animate the orbit camera for Signal Drift.

    The camera orbits the origin (where the mannequin/face stands)
    in a smooth 360° circle, always pointing at the target center.

    Args:
        orbit_radius: Distance from subject center
        orbit_height: Camera height (Z)
        total_frames: Total animation frames
        lens_mm: Focal length in mm
        target_z: Target Z focus coordinate (0.0 for centered face)
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

    # Cinematic lens
    cam_obj.data.lens = lens_mm
    cam_obj.data.clip_end = 200.0

    # ── Create Empty Target for Track To ──────────────────────────────
    target_name = "BB_SD_CameraTarget"
    target = bpy.data.objects.get(target_name)
    if target is None:
        target = bpy.data.objects.new(target_name, None)
        bpy.context.scene.collection.objects.link(target)

    # Target positioned at center of subject
    target.location = (0, 0, target_z)

    # Track To constraint
    existing_track = None
    for c in cam_obj.constraints:
        if c.type == 'TRACK_TO':
            existing_track = c
            break

    if existing_track is None:
        track = cam_obj.constraints.new(type='TRACK_TO')
    else:
        track = existing_track

    track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    # ── Animate Orbit ─────────────────────────────────────────────────
    # Clear existing animation
    if cam_obj.animation_data and cam_obj.animation_data.action:
        bpy.data.actions.remove(cam_obj.animation_data.action)

    cam_obj.animation_data_create()

    for frame in range(1, total_frames + 1):
        t = (frame - 1) / total_frames

        # Circular orbit (360° over entire sequence)
        angle = t * 2.0 * math.pi

        x = math.cos(angle) * orbit_radius
        y = math.sin(angle) * orbit_radius

        # Slight vertical bob for organic feel
        z = orbit_height + math.sin(t * 4.0 * math.pi) * 0.15

        cam_obj.location = (x, y, z)
        cam_obj.keyframe_insert(data_path="location", frame=frame)

    # Smooth interpolation
    from ...animation.baking import _get_action_fcurves
    cam_fcurves = _get_action_fcurves(cam_obj, create_action=False)
    if cam_fcurves:
        for fc in cam_fcurves:
            for kf in fc.keyframe_points:
                kf.interpolation = 'BEZIER'
                kf.handle_left_type = 'AUTO_CLAMPED'
                kf.handle_right_type = 'AUTO_CLAMPED'

    # ── Zoom Punch Driver ─────────────────────────────────────────────
    viz_obj = bpy.data.objects.get("BB_Visualizer")
    if viz_obj:
        from ...visual.camera import setup_camera_zoom
        setup_camera_zoom(
            cam_obj, viz_obj,
            base_lens=lens_mm,
            zoom_punch_mm=12.0,
        )

    # ── Link to collection ────────────────────────────────────────────
    if collection:
        if cam_obj.name not in collection.objects:
            collection.objects.link(cam_obj)
        if target.name not in collection.objects:
            collection.objects.link(target)

    print(f"[BlenderBeat] Signal Drift camera: {total_frames} frames, "
          f"orbit_r={orbit_radius}m, lens={lens_mm}mm")
    return cam_obj
