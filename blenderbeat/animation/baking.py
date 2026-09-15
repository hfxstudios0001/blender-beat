"""
BlenderBeat — F-curve baking engine.

Takes processed audio signals and bakes them as keyframes
on custom properties of Blender objects. These properties
are then read by drivers on visual parameters.
"""

import bpy
import numpy as np
from typing import Dict, List, Optional

from ..audio.analyzer import AnalysisResult
from .smoothing import process_signal
from .mapping import AudioMapping, MappingPreset
from .looping import (
    align_signal_to_loop,
    crossfade_loop_signal,
    calculate_loop_frames,
    calculate_loop_duration,
)
from ..utils.performance import Timer


# Custom property prefix to avoid collisions
PROP_PREFIX = "bb_"


def get_prop_name(target: str) -> str:
    """Generate a Blender custom property name for a mapping target."""
    return f"{PROP_PREFIX}{target}"


def bake_audio_to_fcurves(
    obj: bpy.types.Object,
    analysis: AnalysisResult,
    preset: MappingPreset,
    bpm: float,
    fps: float,
    loop_bars: int = 8,
    beats_per_bar: int = 4,
    loop_start_beat: int = 0,
    full_song: bool = False,
) -> Dict[str, int]:
    """
    Bake all mapped audio signals as keyframes on the object's
    custom properties.

    For each mapping in the preset:
        1. Extract the source signal from analysis
        2. Align to loop timing (or full track duration if full_song is True)
        3. Apply smoothing/processing
        4. Apply loop crossfade
        5. Bake as keyframes

    Args:
        obj: The Blender object to bake properties onto.
        analysis: Audio analysis results.
        preset: Mapping preset defining audio→visual connections.
        bpm: BPM for loop timing.
        fps: Scene FPS.
        loop_bars: Number of bars in the loop.
        beats_per_bar: Beats per bar.
        loop_start_beat: Which beat to start the loop at.
        full_song: If True, bake across entire song duration instead of loop_bars.

    Returns:
        Dict mapping property names to number of keyframes baked.
    """
    with Timer("F-curve baking"):
        if full_song and analysis.duration > 0.0:
            loop_duration = analysis.duration
            total_frames = max(1, int(round(loop_duration * fps)))
            loop_start_time = 0.0
            print(f"[BlenderBeat] Baking FULL SONG: {total_frames} frames, "
                  f"{loop_duration:.2f}s, BPM={bpm}")
        else:
            loop_duration = calculate_loop_duration(bpm, loop_bars, beats_per_bar)
            total_frames = calculate_loop_frames(bpm, fps, loop_bars, beats_per_bar)
            loop_start_time = loop_start_beat * (60.0 / bpm)
            print(f"[BlenderBeat] Baking LOOP: {total_frames} frames, "
                  f"{loop_duration:.2f}s loop, BPM={bpm}")


        # Clear existing animation data
        _clear_bb_animation(obj)

        baked_counts = {}

        for mapping in preset.mappings:
            prop_name = get_prop_name(mapping.target)

            # 1. Get the source signal
            source_signal = analysis.get_signal(mapping.source)
            if len(source_signal) == 0:
                print(f"[BlenderBeat] Warning: signal '{mapping.source}' is empty")
                continue

            # 2. Align to loop
            loop_signal = align_signal_to_loop(
                source_signal,
                analysis.hop_length,
                analysis.sample_rate,
                loop_start_time,
                loop_duration,
                total_frames,
                fps,
            )

            # 2b. Peak normalization: if loop segment is quieter than full track peak,
            # normalize local maximum to 1.0 so animations hit full dynamic punch.
            sig_max = np.max(loop_signal)
            if sig_max > 0.01:
                loop_signal = loop_signal / sig_max

            # 3. Process (smooth, remap, spring, etc.)
            processed = process_signal(
                loop_signal,
                smooth_attack=mapping.smooth_attack,
                smooth_release=mapping.smooth_release,
                remap_min=mapping.remap_min,
                remap_max=mapping.remap_max,
                multiply=mapping.strength,
                spring_enabled=mapping.spring_enabled,
                spring_stiffness=mapping.spring_stiffness,
                spring_damping=mapping.spring_damping,
                power=mapping.power,
            )

            # 4. Invert if needed
            if mapping.invert:
                processed = 1.0 - processed

            # 5. Apply loop crossfade
            blend_frames = max(2, int(fps * 0.3))  # 0.3s blend zone
            processed = crossfade_loop_signal(processed, blend_frames)

            # 6. Bake as keyframes
            n_keys = _bake_signal_to_property(
                obj, prop_name, processed, start_frame=1
            )

            baked_counts[prop_name] = n_keys

        # Set frame range
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = total_frames

    total_keys = sum(baked_counts.values())
    print(f"[BlenderBeat] Baked {total_keys} keyframes across "
          f"{len(baked_counts)} properties")

    return baked_counts


def _get_action_fcurves(obj: bpy.types.Object, create_action: bool = True):
    """
    Get the F-Curves collection for an object across Blender 4.x and 5.x+.

    Blender 5.0 introduced layered/slotted actions where fcurves live in
    action.layers[...].strips[...].channelbag(slot).fcurves rather than action.fcurves.
    """
    if obj.animation_data is None:
        if not create_action:
            return None
        obj.animation_data_create()

    action = obj.animation_data.action
    if action is None:
        if not create_action:
            return None
        action = bpy.data.actions.new(name=f"{obj.name}_BlenderBeat")
        obj.animation_data.action = action

    # Blender 4.x and earlier: action has .fcurves directly
    if hasattr(action, "fcurves"):
        return action.fcurves

    # Blender 5.0+ Slotted / Layered Actions:
    # If the action has no slots or layers yet, keyframe_insert creates them cleanly
    if not getattr(action, "slots", None) or not getattr(action, "layers", None):
        # Insert a temporary keyframe to let Blender initialize the slot and layer hierarchy
        obj.keyframe_insert(data_path="location", index=0, frame=1)

    slot = getattr(obj.animation_data, "action_slot", None)
    if slot is None and getattr(action, "slots", None):
        slot = action.slots[0]

    layer = action.layers[0] if getattr(action, "layers", None) else None
    if layer is None:
        layer = action.layers.new(name="BlenderBeat")

    strip = layer.strips[0] if getattr(layer, "strips", None) else None
    if strip is None:
        strip = layer.strips.new(type='KEYFRAME')

    if hasattr(strip, "channelbag") and slot:
        cb = strip.channelbag(slot)
        if cb and hasattr(cb, "fcurves"):
            return cb.fcurves

    return None


def _bake_signal_to_property(
    obj: bpy.types.Object,
    prop_name: str,
    signal: np.ndarray,
    start_frame: int = 1,
) -> int:
    """
    Bake a signal array as keyframes on a custom property.

    Uses batch keyframe insertion for performance.

    Returns:
        Number of keyframes inserted.
    """
    n_frames = len(signal)

    # Initialize the custom property
    obj[prop_name] = 0.0

    fcurves = _get_action_fcurves(obj, create_action=True)
    if fcurves is None:
        print(f"[BlenderBeat] Error: could not access fcurves for {obj.name}")
        return 0

    data_path = f'["{prop_name}"]'

    # Remove existing F-curve for this property if any
    existing = fcurves.find(data_path)
    if existing:
        fcurves.remove(existing)

    # Create new F-curve
    fcurve = fcurves.new(data_path=data_path)

    # Batch insert keyframes (much faster than per-frame keyframe_insert)
    fcurve.keyframe_points.add(count=n_frames)

    for i in range(n_frames):
        frame = start_frame + i
        value = float(signal[i])
        kf = fcurve.keyframe_points[i]
        kf.co = (frame, value)
        kf.interpolation = 'BEZIER'

    # Update F-curve for smooth interpolation
    fcurve.update()

    return n_frames


def _clear_bb_animation(obj: bpy.types.Object):
    """Remove all BlenderBeat-related F-curves from an object."""
    fcurves = _get_action_fcurves(obj, create_action=False)
    if fcurves is None:
        return

    to_remove = []
    for fc in fcurves:
        if fc.data_path.startswith(f'["{PROP_PREFIX}'):
            to_remove.append(fc)

    for fc in to_remove:
        fcurves.remove(fc)


def get_baked_value(obj: bpy.types.Object, target: str) -> float:
    """
    Read the current value of a baked audio property.

    This reads the evaluated value at the current frame,
    accounting for F-curve interpolation.
    """
    prop_name = get_prop_name(target)
    return obj.get(prop_name, 0.0)


def create_driver(
    target_obj: bpy.types.Object,
    target_data_path: str,
    source_obj: bpy.types.Object,
    source_prop: str,
    expression: str = "var",
    index: int = -1,
) -> Optional[bpy.types.Driver]:
    """
    Create a Blender driver linking a custom property to a visual parameter.

    Args:
        target_obj: Object/data containing the driven property.
        target_data_path: RNA path of the property to drive.
        source_obj: Object containing the source custom property.
        source_prop: Custom property name (e.g., "bb_scale").
        expression: Driver expression (default "var" = direct mapping).
        index: Array index (-1 for non-array properties).

    Returns:
        The created driver, or None on failure.
    """
    try:
        if index >= 0:
            driver_fc = target_obj.driver_add(target_data_path, index)
        else:
            driver_fc = target_obj.driver_add(target_data_path)

        driver = driver_fc.driver
        driver.type = 'SCRIPTED'
        driver.expression = expression

        # Add variable
        var = driver.variables.new()
        var.name = "var"
        var.type = 'SINGLE_PROP'
        var.targets[0].id = source_obj
        var.targets[0].data_path = f'["{source_prop}"]'

        return driver

    except Exception as e:
        print(f"[BlenderBeat] Driver creation failed: {e}")
        return None
