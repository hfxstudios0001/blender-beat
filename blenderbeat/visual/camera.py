"""
BlenderBeat — Procedural camera system.

Creates and animates cameras with smooth orbits,
beat-reactive shake, and seamless looping motion.
"""

import bpy
import math
import numpy as np
from typing import Optional

from ..animation.looping import make_periodic_array
from ..animation.baking import get_prop_name


def create_camera(
    name: str = "BB_Camera",
    distance: float = 8.0,
    height: float = 3.0,
    fov_degrees: float = 50.0,
    focus_distance: Optional[float] = None,
    fstop: float = 2.8,
) -> bpy.types.Object:
    """
    Create a camera with a good default position for visualizer shots.

    Returns the camera object.
    """
    # Remove existing BB camera
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    # Create camera data
    cam_data = bpy.data.cameras.new(name=name)
    cam_data.lens = _fov_to_focal_length(fov_degrees, 36.0)
    cam_data.clip_start = 0.1
    cam_data.clip_end = 1000.0

    # Enable depth of field with cinematic settings
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = focus_distance if focus_distance is not None else distance
    cam_data.dof.aperture_fstop = fstop

    # Create camera object
    cam_obj = bpy.data.objects.new(name, cam_data)
    bpy.context.collection.objects.link(cam_obj)

    # Position the camera
    cam_obj.location = (distance, 0, height)
    cam_obj.rotation_euler = (
        math.radians(70),   # Slight downward angle
        0,
        math.radians(90),   # Face the origin
    )

    # Set as active camera
    bpy.context.scene.camera = cam_obj

    # Add track-to constraint to always look at origin
    track = cam_obj.constraints.new(type='TRACK_TO')
    track.target = _get_or_create_empty("BB_CameraTarget", (0, 0, 0))
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    print(f"[BlenderBeat] Camera created: distance={distance}, height={height}")
    return cam_obj


def _get_or_create_empty(name: str, location: tuple) -> bpy.types.Object:
    """Get or create an empty object for targeting."""
    existing = bpy.data.objects.get(name)
    if existing:
        return existing

    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty.empty_display_size = 0.1
    empty.location = location
    empty.hide_viewport = True
    empty.hide_render = True
    bpy.context.collection.objects.link(empty)
    return empty


def animate_camera_orbit(
    cam_obj: bpy.types.Object,
    total_frames: int,
    orbit_speed: float = 1.0,
    distance: float = 8.0,
    height: float = 3.0,
    height_variation: float = 1.0,
    distance_variation: float = 1.5,
    energy_curve: Optional[np.ndarray] = None,
):
    """
    Animate the camera in a smooth orbit that loops seamlessly.

    If energy_curve is provided (Polyfjord style), the orbit angle
    is calculated by integrating energy over time, so the camera
    drifts smoothly during calm passages and accelerates into dynamic sweeps
    on musical drops.

    Args:
        cam_obj: Camera object.
        total_frames: Total loop frames.
        orbit_speed: Orbits per loop (1.0 = one full orbit).
        distance: Base distance from center.
        height: Base height.
        height_variation: Amplitude of vertical oscillation.
        distance_variation: Amplitude of distance oscillation.
        energy_curve: Audio energy array (length total_frames).
    """
    # Clear existing camera animation
    if cam_obj.animation_data and cam_obj.animation_data.action:
        bpy.data.actions.remove(cam_obj.animation_data.action)

    # Compute cumulative orbit phase
    if energy_curve is not None and len(energy_curve) >= total_frames:
        # Normalize and compute running cumulative sum
        en = np.array(energy_curve[:total_frames], dtype=float)
        # Base drift speed + audio energy boost
        speed_per_frame = 0.35 + 1.2 * en
        cum_angle = np.cumsum(speed_per_frame)
        # Rescale so the full loop completes exactly orbit_speed * 2π for seamless looping
        if cum_angle[-1] > 0:
            angles = (cum_angle / cum_angle[-1]) * 2.0 * math.pi * orbit_speed
        else:
            angles = np.linspace(0, 2.0 * math.pi * orbit_speed, total_frames, endpoint=False)
    else:
        angles = [ (f / total_frames) * 2.0 * math.pi * orbit_speed for f in range(total_frames) ]

    # Generate periodic orbit positions
    for frame in range(1, total_frames + 1):
        t = (frame - 1) / total_frames
        angle = angles[frame - 1]

        # Distance varies with a slower sine wave
        dist = distance + distance_variation * math.sin(t * 2.0 * math.pi * 0.5)

        # Height varies
        h = height + height_variation * math.sin(t * 2.0 * math.pi * 0.7 + 0.5)

        # Position on orbit
        x = dist * math.cos(angle)
        y = dist * math.sin(angle)
        z = h

        cam_obj.location = (x, y, z)
        cam_obj.keyframe_insert(data_path="location", frame=frame)

    # Set interpolation to Bezier for smoothness
    from ..animation.baking import _get_action_fcurves
    cam_fcurves = _get_action_fcurves(cam_obj, create_action=False)
    if cam_fcurves:
        for fc in cam_fcurves:
            for kf in fc.keyframe_points:
                kf.interpolation = 'BEZIER'
                kf.handle_left_type = 'AUTO_CLAMPED'
                kf.handle_right_type = 'AUTO_CLAMPED'

    print(f"[BlenderBeat] Camera orbit: {total_frames} frames, "
          f"speed={orbit_speed}, dynamic_energy={energy_curve is not None}")


def setup_camera_zoom(
    cam_obj: bpy.types.Object,
    source_obj: bpy.types.Object,
    base_lens: float = 40.0,
    zoom_punch_mm: float = 14.0,
):
    """
    Add audio-reactive zoom punch (Polyfjord beat zoom).

    Drives camera focal length using the kick/beat transient
    signal (bb_camera_zoom or bb_scale), punching in on impacts.
    """
    cam_data = cam_obj.data
    prop_name = get_prop_name("camera_zoom")
    if prop_name not in source_obj:
        prop_name = get_prop_name("scale")
    if prop_name not in source_obj:
        return

    data_path = "lens"
    try:
        cam_data.driver_remove(data_path)
    except Exception:
        pass

    try:
        driver_fc = cam_data.driver_add(data_path)
        driver = driver_fc.driver
        driver.type = 'SCRIPTED'
        driver.expression = f"{base_lens} + {zoom_punch_mm} * var"

        var = driver.variables.new()
        var.name = "var"
        var.type = 'SINGLE_PROP'
        var.targets[0].id = source_obj
        var.targets[0].data_path = f'["{prop_name}"]'

        print(f"[BlenderBeat] Camera zoom driver: {prop_name} → lens (+{zoom_punch_mm}mm)")
    except Exception as e:
        print(f"[BlenderBeat] Camera zoom driver failed: {e}")


def setup_camera_shake(
    cam_obj: bpy.types.Object,
    source_obj: bpy.types.Object,
    max_shake_amplitude: float = 0.15,
):
    """
    Add subtle camera shake driven by audio (bb_camera_shake).

    Uses a noise modifier on the camera's location F-curves,
    with amplitude driven by the audio signal.

    For Phase 1, we apply shake by slightly perturbing the
    camera target empty's position based on the kick signal.
    """
    target = bpy.data.objects.get("BB_CameraTarget")
    if target is None:
        return

    # The camera shake is applied as animated offset on the target
    prop_name = get_prop_name("camera_shake")
    if prop_name not in source_obj:
        return

    # Create animation data on target
    if target.animation_data is None:
        target.animation_data_create()

    if target.animation_data.action is None:
        action = bpy.data.actions.new(name="BB_CameraTarget_Action")
        target.animation_data.action = action

    # Drive target X location with shake: small random-looking offset
    # Use driver expression with noise
    for axis_idx, axis in enumerate(['x', 'y', 'z']):
        data_path = f'location'
        try:
            target.driver_remove(data_path, axis_idx)
        except Exception:
            pass

        try:
            driver_fc = target.driver_add(data_path, axis_idx)
            driver = driver_fc.driver
            driver.type = 'SCRIPTED'

            # Use built-in math (sin) with prime frequency harmonics for safe, auto-exec-free shake
            freq = (axis_idx + 1) * 3.7
            if axis == 'z':
                driver.expression = f'sin(frame * {freq}) * {max_shake_amplitude * 0.3} * var'
            else:
                driver.expression = f'sin(frame * {freq}) * {max_shake_amplitude} * var'

            var = driver.variables.new()
            var.name = "var"
            var.type = 'SINGLE_PROP'
            var.targets[0].id = source_obj
            var.targets[0].data_path = f'["{prop_name}"]'

        except Exception as e:
            print(f"[BlenderBeat] Camera shake driver failed ({axis}): {e}")


def _fov_to_focal_length(fov_degrees: float, sensor_width: float = 36.0) -> float:
    """Convert field of view in degrees to focal length in mm."""
    fov_rad = math.radians(fov_degrees)
    return sensor_width / (2.0 * math.tan(fov_rad / 2.0))
