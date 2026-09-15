"""
BlenderBeat — Scene generation orchestrator.

The top-level module that coordinates all subsystems to generate
a complete music-reactive visualizer scene. This is the main
entry point called by operators.
"""

import bpy
from typing import Optional

from ..audio.analyzer import AnalysisResult
from ..audio.cache import save_analysis, load_analysis
from ..animation.baking import bake_audio_to_fcurves
from ..animation.mapping import get_default_audio_sphere_mappings
from ..animation.looping import get_loop_info, calculate_loop_frames
from ..nodes.geometry_nodes import (
    create_audio_sphere_nodes,
    create_quantum_field_nodes,
    setup_gn_drivers,
)
from ..nodes.shader_nodes import create_world_material
from .geometry import (
    create_visualizer_object,
    clear_blenderbeat_objects,
    set_object_material,
)
from .presets import VisualPreset, PRESET_AUDIO_SPHERE, get_preset
from .materials import create_materials_from_preset, apply_materials
from .camera import create_camera, animate_camera_orbit, setup_camera_shake, setup_camera_zoom
from .lighting import (
    create_lighting_setup,
    setup_light_drivers,
    setup_render_settings,
)
from ..utils.performance import Timer


def generate_visualizer(
    analysis: AnalysisResult,
    preset_name: str = "Audio Sphere",
    bpm: float = 0.0,
    loop_bars: int = 8,
    beats_per_bar: int = 4,
    fps: int = 30,
    renderer: str = 'BLENDER_EEVEE',
    resolution_x: int = 1920,
    resolution_y: int = 1080,
    complexity: float = 0.5,
    seed: int = 0,
    full_song: bool = False,
) -> dict:
    """
    Generate a complete music-reactive visualizer scene.

    This is the main entry point — it orchestrates all subsystems.

    Args:
        analysis: Audio analysis results.
        preset_name: Visual preset to use.
        bpm: BPM override (0 = use detected).
        loop_bars: Number of bars in the loop.
        beats_per_bar: Beats per bar.
        fps: Frame rate.
        renderer: Render engine.
        resolution_x: Output width.
        resolution_y: Output height.
        complexity: Visual complexity (0–1).
        seed: Random seed for variation.

    Returns:
        Dict with generation info.
    """
    with Timer("Scene generation"):
        # Use detected BPM if not overridden
        if bpm <= 0:
            bpm = analysis.bpm

        # Get preset
        preset = get_preset(preset_name)
        if preset is None:
            preset = PRESET_AUDIO_SPHERE

        # Calculate loop info
        loop_info = get_loop_info(
            bpm,
            fps,
            loop_bars,
            beats_per_bar,
            full_song=full_song,
            total_duration=analysis.duration if hasattr(analysis, "duration") else 0.0,
        )
        total_frames = loop_info["total_frames"]

        mode_str = "FULL SONG" if full_song else f"loop={loop_bars} bars"
        print(f"[BlenderBeat] Generating: preset={preset.name}, "
              f"BPM={bpm}, {mode_str} ({total_frames} frames)")

        # --- Check for Modular Preset Architecture (Black Hole Tunnel, etc.) ---
        from ..presets.registry import PresetRegistry
        modular_preset = PresetRegistry.get_by_name(preset_name)
        if modular_preset is not None:
            # 1. Clear previous objects
            clear_blenderbeat_objects()
            # 2. Bake audio to F-curves onto scene/viz
            mapping_preset = modular_preset.get_mappings()
            viz_dummy = create_visualizer_object("BB_Visualizer")
            baked = bake_audio_to_fcurves(
                viz_dummy,
                analysis,
                mapping_preset,
                bpm=bpm,
                fps=fps,
                loop_bars=loop_bars,
                beats_per_bar=beats_per_bar,
                full_song=full_song,
            )
            # 3. Create modular preset scene
            bb_vis = bpy.context.scene.bb_visual
            preset_settings = {
                "bpm": bpm,
                "fps": fps,
                "total_frames": total_frames,
                "complexity": complexity,
                "seed": seed,
                "tunnel_ring_count": getattr(bb_vis, "tunnel_ring_count", 45),
                "tunnel_radius": getattr(bb_vis, "tunnel_radius", 3.5),
                "color_mode": getattr(bb_vis, "tunnel_color_mode", 'SPECTRUM'),
                "custom_color": tuple(getattr(bb_vis, "tunnel_custom_color", (0.0, 0.8, 1.0))),
                "min_glow": getattr(bb_vis, "tunnel_glow_min", 0.02),
                "peak_emission": getattr(bb_vis, "tunnel_glow_max", 35.0),
                "enable_debris": getattr(bb_vis, "tunnel_enable_debris", False),
                # Cosmic Blossom Settings
                "blossom_outer_petals": getattr(bb_vis, "blossom_outer_petals", 14),
                "blossom_open_factor": getattr(bb_vis, "blossom_open_factor", 0.45),
                "blossom_core_energy": getattr(bb_vis, "blossom_core_energy", 40.0),
                "blossom_shard_count": getattr(bb_vis, "blossom_shard_count", 45),
                "blossom_color_palette": getattr(bb_vis, "blossom_color_palette", 'CELESTIAL_GOLD'),
                "blossom_water_reflections": getattr(bb_vis, "blossom_water_reflections", True),
                # Infinite Light Grid Settings
                "grid_frame_count": getattr(bb_vis, "grid_frame_count", 35),
                "grid_frame_size": getattr(bb_vis, "grid_frame_size", 3.0),
                "grid_twist_amount": getattr(bb_vis, "grid_twist_amount", 0.05),
            }
            preset_objects = modular_preset.create(bpy.context, analysis, preset_settings)
            
            # Setup render settings & frame range
            setup_render_settings(
                resolution_x=resolution_x,
                resolution_y=resolution_y,
                fps=fps,
                renderer=renderer,
            )
            bpy.context.scene.frame_start = 1
            bpy.context.scene.frame_end = total_frames
            bpy.context.scene.frame_current = 1

            return {
                "preset": modular_preset.name,
                "bpm": bpm,
                "loop_bars": loop_bars,
                "total_frames": total_frames,
                "loop_duration": loop_info["duration_seconds"],
                "baked_properties": len(baked),
                "total_keyframes": sum(baked.values()),
                "visualizer_object": "BB_Visualizer",
                "camera": "BB_Camera",
            }

        # --- Legacy Path: Audio Sphere / Quantum Field ---
        # --- Step 1: Clean slate ---
        clear_blenderbeat_objects()

        # --- Step 2: Create visualizer object ---
        viz_obj = create_visualizer_object("BB_Visualizer")

        # --- Step 3: Create material ---
        material = create_materials_from_preset(preset)
        apply_materials(viz_obj, material)

        # --- Step 4: Create Geometry Nodes ---
        subdivisions = _complexity_to_subdivisions(complexity)
        if preset.geometry_type == "quantum_field":
            node_tree = create_quantum_field_nodes(
                viz_obj,
                density=complexity,
                material=material,
            )
        else:
            node_tree = create_audio_sphere_nodes(
                viz_obj,
                subdivisions=subdivisions,
                material=material,
            )

        # Set GN modifier default values from preset
        mod = viz_obj.modifiers.get("BlenderBeat_GN")
        if mod and node_tree:
            _set_gn_defaults(mod, node_tree, preset)

        # --- Step 5: Bake audio to F-curves ---
        mapping_preset = preset.get_mappings()

        baked = bake_audio_to_fcurves(
            viz_obj,
            analysis,
            mapping_preset,
            bpm=bpm,
            fps=fps,
            loop_bars=loop_bars,
            beats_per_bar=beats_per_bar,
            full_song=full_song,
        )

        # --- Step 6: Set up drivers (audio props → GN & Material inputs) ---
        setup_gn_drivers(viz_obj, node_tree)
        from ..nodes.shader_nodes import setup_material_drivers
        setup_material_drivers(viz_obj, material)

        # --- Step 7: Camera ---
        # Eduard OV style uses macro shallow DOF focused on the crests of the wave field
        is_qf = preset.geometry_type == "quantum_field"
        fstop = 1.1 if is_qf else 4.0
        camera = create_camera(
            distance=preset.camera_distance,
            height=preset.camera_height,
            fov_degrees=preset.camera_fov,
            focus_distance=preset.camera_distance * 0.95,
            fstop=fstop,
        )

        # Sample energy envelope curve for dynamic orbit velocity
        energy_curve = None
        if hasattr(analysis, "energy") and len(analysis.energy) > 0:
            import numpy as np
            x_old = np.linspace(0, 1, len(analysis.energy))
            x_new = np.linspace(0, 1, total_frames)
            energy_curve = np.interp(x_new, x_old, analysis.energy)

        animate_camera_orbit(
            camera,
            total_frames=total_frames,
            orbit_speed=preset.camera_orbit_speed,
            distance=preset.camera_distance,
            height=preset.camera_height,
            height_variation=0.08 if is_qf else 1.0,
            distance_variation=0.15 if is_qf else 1.5,
            energy_curve=energy_curve,
        )

        setup_camera_shake(camera, viz_obj)
        setup_camera_zoom(camera, viz_obj, base_lens=camera.data.lens, zoom_punch_mm=20.0)

        # --- Step 8: Lighting ---
        fill_intensity = 8.0 if is_qf else 100.0
        rim_intensity = 550.0 if is_qf else 300.0
        lights = create_lighting_setup(
            key_color=preset.key_color,
            fill_color=preset.fill_color,
            rim_color=preset.rim_color,
            key_intensity=preset.key_intensity,
            fill_intensity=fill_intensity,
            rim_intensity=rim_intensity,
        )

        setup_light_drivers(viz_obj, lights)

        # --- Step 9: Render settings ---
        setup_render_settings(
            resolution_x=resolution_x,
            resolution_y=resolution_y,
            fps=fps,
            renderer=renderer,
        )

        # --- Step 10: Frame range ---
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = total_frames
        bpy.context.scene.frame_current = 1

        # --- Step 11: Load audio into Blender for playback ---
        # (Audio strip in the VSE or scene speaker)
        # This is handled separately by the operator

    result = {
        "preset": preset.name,
        "bpm": bpm,
        "loop_bars": loop_bars,
        "total_frames": total_frames,
        "loop_duration": loop_info["duration_seconds"],
        "baked_properties": len(baked),
        "total_keyframes": sum(baked.values()),
        "subdivisions": subdivisions,
        "visualizer_object": viz_obj.name,
        "camera": camera.name,
    }

    print(f"[BlenderBeat] Generation complete: {total_frames} frames, "
          f"{sum(baked.values())} keyframes")

    return result


def _complexity_to_subdivisions(complexity: float) -> int:
    """
    Map complexity value (0–1) to icosphere subdivisions.

    0.0 → 2 (low poly, ~80 faces)
    0.5 → 3 (~320 faces)
    1.0 → 4 (~1280 faces)
    """
    if complexity < 0.3:
        return 2
    elif complexity < 0.7:
        return 3
    else:
        return 4


def _set_gn_defaults(
    modifier: bpy.types.Modifier,
    node_tree: bpy.types.NodeTree,
    preset: VisualPreset,
):
    """Set Geometry Nodes modifier input defaults from preset."""
    input_map = {}
    for item in node_tree.interface.items_tree:
        if hasattr(item, 'socket_type') and item.in_out == 'INPUT':
            input_map[item.name] = item.identifier

    defaults = {
        "Sphere Radius": preset.sphere_radius,
        "Bar Base Scale": preset.bar_base_scale,
        "Bar Max Length": preset.bar_max_length,
        "Variation": preset.variation,
        "Particle Size": preset.bar_base_scale,
        "Beat Glow": 0.0,
        "Audio Scale": 0.5,
        "Audio Rotation": 0.0,
    }

    for name, value in defaults.items():
        if name in input_map:
            identifier = input_map[name]
            # Blender 5.x:
            try:
                modifier.properties.inputs[identifier]["value"] = value
                continue
            except Exception:
                pass
            # Blender 4.x fallback:
            try:
                modifier[identifier] = value
            except Exception:
                pass
