"""
BlenderBeat — Infinite Light Grid Preset Implementation.

Orchestrates:
1. Procedural Master Frame generation (square LED corridor section)
2. Grid instancing with Geometry Nodes (traveling shockwave + twist spiral)
3. Glowing terminus at tunnel end (inverted singularity)
4. Forward flythrough camera with kick zoom punch
5. Aura Sync LED color modes and audio-reactive emission
"""

import bpy
import math
from typing import Dict, Any

from ..base import BasePreset
from .master_frame import create_master_frame_mesh
from .grid_nodes import create_grid_geometry_nodes
from .grid_terminus import create_grid_terminus
from .grid_camera import setup_grid_camera
from ...audio.analyzer import AnalysisResult
from ...animation.mapping import MappingPreset, AudioMapping
from ...visual.geometry import create_visualizer_object


class InfiniteLightGridPreset(BasePreset):
    """
    Deep square-framed LED tunnel corridor with mechanical chrome joints,
    per-frame shockwave LED pulses, and audio-reactive emission.
    Inspired by real-world light tunnel installations.
    """
    id = "INFINITE_LIGHT_GRID"
    name = "Infinite Light Grid"
    description = "Deep square-framed LED tunnel with mechanical joints and audio-reactive light propagation"
    category = "Sci-Fi Tunnel"
    collection_name = "BB_Grid_Collection"

    def get_mappings(self) -> MappingPreset:
        """Audio mappings tuned for the square light grid aesthetic."""
        return MappingPreset(
            name="Infinite Light Grid",
            mappings=[
                # Kick → explosive zoom punch (punchy camera response)
                AudioMapping(
                    source="kick",
                    target="camera_zoom",
                    strength=1.0,
                    smooth_attack=0.9,
                    smooth_release=0.06,
                    remap_min=0.0,
                    remap_max=1.0,
                    spring_enabled=True,
                    spring_stiffness=0.5,
                    spring_damping=0.6,
                ),
                # Bass → frame scale breathing (macro tunnel expansion)
                AudioMapping(
                    source="bass",
                    target="scale",
                    strength=1.0,
                    smooth_attack=0.4,
                    smooth_release=0.1,
                    remap_min=0.2,
                    remap_max=1.0,
                    spring_enabled=True,
                    spring_stiffness=0.35,
                    spring_damping=0.7,
                ),
                # Mid → frame twist rotation velocity
                AudioMapping(
                    source="mid",
                    target="rotation_z",
                    strength=0.8,
                    smooth_attack=0.3,
                    smooth_release=0.15,
                    remap_min=0.0,
                    remap_max=1.0,
                ),
                # Energy → LED emission intensity (global brightness)
                AudioMapping(
                    source="energy",
                    target="emission_strength",
                    strength=1.0,
                    smooth_attack=0.3,
                    smooth_release=0.1,
                    remap_min=0.2,
                    remap_max=1.5,
                ),
                # Onset/Snare → camera shake + edge flicker trigger
                AudioMapping(
                    source="onset_strength",
                    target="camera_shake",
                    strength=0.5,
                    smooth_attack=0.8,
                    smooth_release=0.05,
                    remap_min=0.0,
                    remap_max=0.4,
                ),
            ],
        )

    def create(
        self,
        context: bpy.types.Context,
        analysis: AnalysisResult,
        settings: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate the Infinite Light Grid scene.
        """
        col = self.get_collection()

        # ── 1. Configuration ──────────────────────────────────────────
        frame_size = settings.get("grid_frame_size", 3.0)
        frame_count = settings.get("grid_frame_count", 35)
        twist_amount = settings.get("grid_twist_amount", 0.05)
        spacing = 2.0
        tunnel_depth = frame_count * spacing

        # ── 2. Materials ──────────────────────────────────────────────
        from .grid_materials import create_grid_led_material
        color_mode = settings.get("color_mode", "SPECTRUM")
        custom_color = settings.get("custom_color", (0.0, 0.8, 1.0))
        min_glow = settings.get("min_glow", 6.0)
        peak_emission = settings.get("peak_emission", 65.0)

        mat_led = create_grid_led_material(
            name="BB_Mat_GridLED",
            color_mode=color_mode,
            custom_color=custom_color,
            min_glow=min_glow,
            peak_emission=peak_emission,
        )

        # ── 3. Master Frame Mesh ──────────────────────────────────────
        frame_obj = create_master_frame_mesh(
            name="BB_MasterFrame",
            frame_size=frame_size,
            depth=0.35,
            mat_led=mat_led,
        )

        # Ensure updated LED material is in slot 2
        if len(frame_obj.data.materials) > 2:
            frame_obj.data.materials[2] = mat_led

        # Link to collection, hide as instancing source
        if frame_obj.name not in col.objects:
            col.objects.link(frame_obj)
        frame_obj.hide_viewport = True
        frame_obj.hide_render = True

        # ── 4. Visualizer Object ──────────────────────────────────────
        viz_obj = create_visualizer_object("BB_Visualizer")
        if viz_obj.name not in col.objects:
            col.objects.link(viz_obj)

        # Copy materials to visualizer (needed for realized GN instances)
        viz_obj.data.materials.clear()
        for mat in frame_obj.data.materials:
            viz_obj.data.materials.append(mat)

        # ── 5. Geometry Nodes Grid System ─────────────────────────────
        node_tree = create_grid_geometry_nodes(
            viz_obj=viz_obj,
            frame_obj=frame_obj,
            frame_count=frame_count,
            spacing=spacing,
            twist_per_frame=twist_amount,
        )

        # ── 6. Terminus (vanishing point glow) ────────────────────────
        terminus = create_grid_terminus(
            name="BB_GridTerminus",
            radius=frame_size * 0.12,
            location_z=-(tunnel_depth + 5.0),
            color=(0.4, 0.7, 1.0),
            emission_strength=4.0,
        )
        if terminus.name not in col.objects:
            col.objects.link(terminus)

        # Also link the terminus light if it exists
        terminus_light = bpy.data.objects.get("BB_GridTerminus_Light")
        if terminus_light:
            if terminus_light.name not in col.objects:
                try:
                    col.objects.link(terminus_light)
                except RuntimeError:
                    pass

        # ── 7. Drivers ────────────────────────────────────────────────
        self._setup_grid_drivers(viz_obj, node_tree)

        # ── 8. Camera ────────────────────────────────────────────────
        cam = setup_grid_camera(
            tunnel_depth=tunnel_depth,
            total_frames=settings.get("total_frames", 446),
            collection=col,
        )

        # ── 9. Lighting & Compositor ──────────────────────────────────
        self._setup_grid_lighting(col)

        print("[BlenderBeat] Infinite Light Grid Preset generated successfully!")
        return {
            "visualizer": viz_obj,
            "master_frame": frame_obj,
            "terminus": terminus,
            "camera": cam,
        }

    def _setup_grid_drivers(
        self,
        viz_obj: bpy.types.Object,
        node_tree: bpy.types.NodeTree,
    ):
        """Connect baked audio properties to GN internal Value nodes."""
        driver_configs = [
            ("BB_GridBassVal", "bb_scale", "var"),
            ("BB_GridKickVal", "bb_camera_zoom", "var"),
            ("BB_GridTimeVal", "bb_rotation_z", "var * 3.0"),
        ]
        for node_name, prop_name, expr in driver_configs:
            node = node_tree.nodes.get(node_name)
            if node:
                try:
                    df = node.outputs[0].driver_add("default_value")
                    d = df.driver
                    d.type = 'SCRIPTED'
                    d.expression = expr
                    var = d.variables.new()
                    var.name = "var"
                    var.type = 'SINGLE_PROP'
                    var.targets[0].id = viz_obj
                    var.targets[0].data_path = f'["{prop_name}"]'
                except Exception as e:
                    print(f"[BlenderBeat] Grid driver error on {node_name}: {e}")

        # Drive BB_GridAudioEmission in material
        mat_grid = bpy.data.materials.get("BB_Mat_GridLED")
        if mat_grid and mat_grid.node_tree:
            val_node = mat_grid.node_tree.nodes.get("BB_GridAudioEmission")
            if val_node:
                try:
                    df = val_node.outputs[0].driver_add("default_value")
                    d = df.driver
                    d.type = 'SCRIPTED'
                    d.expression = "var"
                    var = d.variables.new()
                    var.name = "var"
                    var.type = 'SINGLE_PROP'
                    var.targets[0].id = viz_obj
                    var.targets[0].data_path = '["bb_emission_strength"]'
                except Exception as e:
                    print(f"[BlenderBeat] Grid material emission driver error: {e}")

    def _setup_grid_lighting(self, col: bpy.types.Collection):
        """Configure black background, Eevee settings, and real-time Fog Glow."""
        scene = bpy.context.scene

        # Enable Eevee raytracing if available
        if hasattr(scene, 'eevee'):
            try:
                scene.eevee.use_raytracing = True
                scene.eevee.fast_gi_quality = 1.0
            except AttributeError:
                pass

        # Absolute black background (the LED frames are the ONLY light)
        if scene.world and scene.world.use_nodes:
            bg = scene.world.node_tree.nodes.get("Background")
            if bg:
                bg.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
                bg.inputs["Strength"].default_value = 0.0

        # Real-time Compositor Fog Glow bloom
        from ...visual.lighting import setup_realtime_glow_compositor
        setup_realtime_glow_compositor()

        # Remove any legacy point rimlights
        light_name = "BB_Grid_RimLight"
        old_light = bpy.data.objects.get(light_name)
        if old_light:
            bpy.data.objects.remove(old_light, do_unlink=True)
