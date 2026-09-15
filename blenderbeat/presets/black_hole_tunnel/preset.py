"""
BlenderBeat — Infinite Black Hole Tunnel Preset Implementation.

Orchestrates:
1. Procedural Master Ring generation
2. Tunnel instancing with Geometry Nodes
3. Black Hole Singularity at tunnel terminus
4. Deep corridor camera flythrough with kick zoom punch
5. Amber LED chase and pulse audio mappings
"""

import bpy
import math
from typing import Dict, Any

from ..base import BasePreset
from .master_ring import create_master_ring_mesh
from .tunnel_nodes import create_tunnel_geometry_nodes
from .black_hole import create_black_hole_singularity
from ...audio.analyzer import AnalysisResult
from ...animation.mapping import MappingPreset, AudioMapping
from ...visual.geometry import create_visualizer_object


class InfiniteBlackHoleTunnelPreset(BasePreset):
    """
    A gigantic futuristic wormhole corridor composed of concentric mechanical rings
    with intense amber glowing LED strips leading down to a deep black void singularity.
    """
    id = "INFINITE_BLACK_HOLE_TUNNEL"
    name = "Infinite Black Hole Tunnel"
    description = "Gigantic mechanical corridor with amber LED pulse rings leading to a black hole"
    category = "Sci-Fi Tunnel"
    collection_name = "BB_Tunnel_Collection"

    def get_mappings(self) -> MappingPreset:
        """Audio mappings tailored for high-energy tunnel visuals."""
        return MappingPreset(
            name="Black Hole Tunnel",
            mappings=[
                # Kick → explosive LED pulse & camera zoom punch
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
                # Bass → tunnel radius breathing & ring expansion
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
                # Mid → mechanical rotation velocity
                AudioMapping(
                    source="mid",
                    target="rotation_z",
                    strength=0.8,
                    smooth_attack=0.3,
                    smooth_release=0.15,
                    remap_min=0.0,
                    remap_max=1.0,
                ),
                # Energy → amber LED emission intensity
                AudioMapping(
                    source="energy",
                    target="emission_strength",
                    strength=1.0,
                    smooth_attack=0.3,
                    smooth_release=0.1,
                    remap_min=0.2,
                    remap_max=1.5,
                ),
                # Treble / Onset → camera shake & spark flashes
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
        Generate the Infinite Black Hole Tunnel scene.
        """
        col = self.get_collection()

        # 1. Procedural Master Ring
        outer_r = settings.get("tunnel_radius", 3.5)
        ring_count = settings.get("tunnel_ring_count", 45)
        spacing = settings.get("spacing", 1.8)  # Generous spacing for deep, clean sci-fi corridor
        tunnel_depth = ring_count * spacing

        # Configure Aura Sync LED material
        from ...visual.materials_library import create_amber_led_material
        color_mode = settings.get("color_mode", "SPECTRUM")
        custom_color = settings.get("custom_color", (0.0, 0.8, 1.0))
        min_glow = settings.get("min_glow", 0.02)
        peak_emission = settings.get("peak_emission", 35.0)

        mat_aura = create_amber_led_material(
            name="BB_Mat_AmberLED",
            color_mode=color_mode,
            custom_color=custom_color,
            min_glow=min_glow,
            peak_emission=peak_emission,
        )

        ring_obj = create_master_ring_mesh(
            name="BB_MasterRing",
            outer_radius=outer_r,
            depth=spacing,
            segments=32,
            mat_led=mat_aura,
        )
        # Ensure updated material is assigned to the master ring slot 2
        if len(ring_obj.data.materials) > 2:
            ring_obj.data.materials[2] = mat_aura

        # Move to hidden or utility part of collection
        if ring_obj.name not in col.objects:
            col.objects.link(ring_obj)
        ring_obj.hide_viewport = True
        ring_obj.hide_render = True

        # 2. Main Visualizer Object
        viz_obj = create_visualizer_object("BB_Visualizer")
        if viz_obj.name not in col.objects:
            col.objects.link(viz_obj)

        # Copy materials to visualizer so realized GN geometry renders with full shader shading
        viz_obj.data.materials.clear()
        for mat in ring_obj.data.materials:
            viz_obj.data.materials.append(mat)

        # 3. Geometry Nodes Tunnel System (Debris disabled by default for clean view)
        enable_debris = settings.get("enable_debris", False)
        debris_count = settings.get("debris_count", 50) if enable_debris else 0

        node_tree = create_tunnel_geometry_nodes(
            viz_obj=viz_obj,
            ring_obj=ring_obj,
            ring_count=ring_count,
            spacing=spacing,
            debris_count=debris_count,
        )

        # 4. Black Hole Singularity at tunnel terminus
        singularity = create_black_hole_singularity(
            name="BB_BlackHole_Singularity",
            radius=outer_r * 0.95,
            location_z=-(tunnel_depth + 4.0),
        )
        if singularity.name not in col.objects:
            col.objects.link(singularity)

        # 5. Connect Drivers: bb_scale, bb_camera_zoom, bb_rotation_z to GN internal value nodes
        self._setup_tunnel_drivers(viz_obj, node_tree)

        # 6. Camera Setup: looking down the tunnel toward the black hole
        cam = self._setup_tunnel_camera(
            tunnel_depth=tunnel_depth,
            total_frames=settings.get("total_frames", 446),
        )
        if cam.name not in col.objects:
            col.objects.link(cam)

        # 7. Subtle amber rim and fill lights
        self._setup_tunnel_lighting(col)

        print("[BlenderBeat] Infinite Black Hole Tunnel Preset generated successfully!")
        return {
            "visualizer": viz_obj,
            "master_ring": ring_obj,
            "singularity": singularity,
            "camera": cam,
        }

    def _setup_tunnel_drivers(self, viz_obj: bpy.types.Object, node_tree: bpy.types.NodeTree):
        """Connect baked properties to internal Value nodes inside the tunnel GN tree."""
        # BB_TunnelBassVal -> bb_scale
        # BB_TunnelKickVal -> bb_camera_zoom
        # BB_TunnelTimeVal -> bb_rotation_z
        driver_configs = [
            ("BB_TunnelBassVal", "bb_scale", "var"),
            ("BB_TunnelKickVal", "bb_camera_zoom", "var"),
            ("BB_TunnelTimeVal", "bb_rotation_z", "var * 3.0"),
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
                    print(f"[BlenderBeat] Driver error on {node_name}: {e}")

        # Also drive BB_AudioEmission in material if present
        mat_amber = bpy.data.materials.get("BB_Mat_AmberLED")
        if mat_amber and mat_amber.node_tree:
            val_node = mat_amber.node_tree.nodes.get("BB_AudioEmission")
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
                    print(f"[BlenderBeat] Material emission driver error: {e}")

    def _setup_tunnel_camera(self, tunnel_depth: float, total_frames: int) -> bpy.types.Object:
        """Create forward flythrough camera with audio-reactive zoom punch."""
        cam_name = "BB_Camera"
        cam_obj = bpy.data.objects.get(cam_name)
        if cam_obj is None:
            cam_data = bpy.data.cameras.new(cam_name)
            cam_obj = bpy.data.objects.new(cam_name, cam_data)
            bpy.context.scene.collection.objects.link(cam_obj)

        bpy.context.scene.camera = cam_obj
        cam_obj.data.lens = 18.0  # Ultra-wide cinematic FOV
        cam_obj.data.clip_end = 300.0

        # Animate forward motion along Z with seamless looping
        if cam_obj.animation_data and cam_obj.animation_data.action:
            bpy.data.actions.remove(cam_obj.animation_data.action)

        cam_obj.animation_data_create()
        cam_obj.rotation_euler = (0.0, 0.0, 0.0)

        for frame in range(1, total_frames + 1):
            t = (frame - 1) / total_frames
            z = 2.0 - (t * 12.0)
            x = math.sin(t * 2.0 * math.pi) * 0.2
            y = math.cos(t * 2.0 * math.pi) * 0.12
            cam_obj.location = (x, y, z)
            cam_obj.keyframe_insert(data_path="location", frame=frame)

        # Setup zoom punch driver on lens (+14mm on kick hits)
        viz_obj = bpy.data.objects.get("BB_Visualizer")
        if viz_obj:
            from ...visual.camera import setup_camera_zoom
            setup_camera_zoom(cam_obj, viz_obj, base_lens=18.0, zoom_punch_mm=12.0)

        return cam_obj

    def _setup_tunnel_lighting(self, col: bpy.types.Collection):
        """Configure Eevee raytracing, world background contrast, and real-time Fog Glow Compositor bloom."""
        scene = bpy.context.scene
        if hasattr(scene, 'eevee'):
            scene.eevee.use_raytracing = True
            scene.eevee.fast_gi_quality = 1.0

        # Black background for high sci-fi negative space contrast
        if scene.world and scene.world.use_nodes:
            bg = scene.world.node_tree.nodes.get("Background")
            if bg:
                bg.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
                bg.inputs["Strength"].default_value = 0.0

        # Real-time Compositor Fog Glow
        from ...visual.lighting import setup_realtime_glow_compositor
        setup_realtime_glow_compositor()

        # Remove any legacy point rimlights that wash out the contrast
        light_name = "BB_Tunnel_RimLight"
        old_light = bpy.data.objects.get(light_name)
        if old_light:
            bpy.data.objects.remove(old_light, do_unlink=True)
