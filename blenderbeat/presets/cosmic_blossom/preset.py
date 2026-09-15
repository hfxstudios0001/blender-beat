"""
BlenderBeat — Cosmic Blossom Preset Implementation.
"""

import bpy
import math
from typing import Dict, Any

from ..base import BasePreset
from .materials import create_cosmic_blossom_materials
from .master_petal import create_master_petal_mesh
from .flower_nodes import create_flower_geometry_nodes
from .core_nodes import create_energy_core_system
from .ring_system import create_cosmic_ring_system
from .environment import create_cosmic_environment
from .particles import create_floating_shards_system
from ...audio.analyzer import AnalysisResult
from ...animation.mapping import MappingPreset, AudioMapping
from ...visual.geometry import create_visualizer_object


class CosmicBlossomPreset(BasePreset):
    id = "COSMIC_BLOSSOM"
    name = "Cosmic Blossom"
    description = "Gigantic futuristic alien cosmic flower floating over a reflective temple lake"
    category = "Sci-Fi Organism"
    collection_name = "BB_CosmicBlossom_Collection"

    def get_mappings(self) -> MappingPreset:
        return MappingPreset(
            name="Cosmic Blossom",
            mappings=[
                AudioMapping(
                    source="kick",
                    target="camera_zoom",
                    strength=1.0,
                    smooth_attack=0.95,
                    smooth_release=0.08,
                    remap_min=0.0,
                    remap_max=1.0,
                    spring_enabled=True,
                    spring_stiffness=0.55,
                    spring_damping=0.65,
                ),
                AudioMapping(
                    source="bass",
                    target="scale",
                    strength=1.0,
                    smooth_attack=0.45,
                    smooth_release=0.12,
                    remap_min=0.15,
                    remap_max=1.0,
                    spring_enabled=True,
                    spring_stiffness=0.4,
                    spring_damping=0.7,
                ),
                AudioMapping(
                    source="mid",
                    target="rotation_z",
                    strength=0.85,
                    smooth_attack=0.3,
                    smooth_release=0.15,
                    remap_min=0.0,
                    remap_max=1.0,
                ),
                AudioMapping(
                    source="energy",
                    target="emission_strength",
                    strength=1.0,
                    smooth_attack=0.35,
                    smooth_release=0.1,
                    remap_min=0.2,
                    remap_max=1.5,
                ),
                AudioMapping(
                    source="onset_strength",
                    target="camera_shake",
                    strength=0.6,
                    smooth_attack=0.85,
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
        col = self.get_collection()

        outer_petals = settings.get("blossom_outer_petals", 14)
        open_factor = settings.get("blossom_open_factor", 0.45)
        core_energy = settings.get("blossom_core_energy", 10.0)
        shard_count = settings.get("blossom_shard_count", 45)
        palette = settings.get("blossom_color_palette", "CELESTIAL_GOLD")
        total_frames = settings.get("total_frames", 446)

        materials = create_cosmic_blossom_materials(palette=palette)

        master_petal = create_master_petal_mesh(
            name="BB_MasterPetal",
            length=6.8,
            max_width=3.2,
            curvature=0.22,
            thickness=0.035,
            materials_dict=materials,
        )
        if master_petal.name not in col.objects:
            col.objects.link(master_petal)
        master_petal.hide_viewport = True
        master_petal.hide_render = True

        viz_obj = create_visualizer_object("BB_Visualizer")
        if viz_obj.name not in col.objects:
            col.objects.link(viz_obj)

        viz_obj.data.materials.clear()
        for mat in master_petal.data.materials:
            viz_obj.data.materials.append(mat)

        flower_gn_tree = create_flower_geometry_nodes(
            viz_obj=viz_obj,
            petal_obj=master_petal,
            outer_petals=outer_petals,
            open_factor=open_factor,
        )

        core_objs = create_energy_core_system(
            materials_dict=materials,
            core_radius=0.95,
            parent_collection=col,
        )

        ring_objs = create_cosmic_ring_system(
            materials_dict=materials,
            radius=5.2,
            parent_collection=col,
        )

        env_objs = create_cosmic_environment(
            materials_dict=materials,
            platform_radius=32.0,
            parent_collection=col,
        )

        shards_obj = create_floating_shards_system(
            materials_dict=materials,
            shard_count=shard_count,
            parent_collection=col,
        )

        self._setup_blossom_drivers(viz_obj, flower_gn_tree, materials, core_objs, ring_objs, core_energy)

        cam = self._setup_blossom_camera(total_frames=total_frames)
        if cam.name not in col.objects:
            col.objects.link(cam)

        self._setup_blossom_lighting(col)

        print("[BlenderBeat] Cosmic Blossom ecosystem successfully instantiated!")
        return {
            "visualizer": viz_obj,
            "master_petal": master_petal,
            "core": core_objs,
            "rings": ring_objs,
            "environment": env_objs,
            "shards": shards_obj,
            "camera": cam,
        }

    def _setup_blossom_drivers(
        self,
        viz_obj: bpy.types.Object,
        flower_gn_tree: bpy.types.NodeTree,
        materials: Dict[str, bpy.types.Material],
        core_objs: Dict[str, bpy.types.Object],
        ring_objs: Dict[str, bpy.types.Object],
        core_energy: float = 40.0,
    ):
        driver_configs = [
            ("BB_BlossomBassVal", "bb_scale", "var"),
            ("BB_BlossomKickVal", "bb_camera_zoom", "var"),
            ("BB_BlossomTimeVal", "bb_rotation_z", "var * 1.5"),
        ]
        for node_name, prop_name, expr in driver_configs:
            node = flower_gn_tree.nodes.get(node_name)
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
                    print(f"[BlenderBeat] GN Driver error on {node_name}: {e}")

        for mat_key in ['core', 'energy_vein', 'beam']:
            mat = materials.get(mat_key)
            if mat and mat.node_tree:
                val_node = mat.node_tree.nodes.get("BB_AudioEmission")
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
                        print(f"[BlenderBeat] Material emission driver error on {mat_key}: {e}")

        gyro_z = core_objs.get("BB_Core_Gyro_Z")
        if gyro_z:
            try:
                df = gyro_z.driver_add("rotation_euler", 2)
                d = df.driver
                d.type = 'SCRIPTED'
                d.expression = "var * 4.0"
                var = d.variables.new()
                var.name = "var"
                var.type = 'SINGLE_PROP'
                var.targets[0].id = viz_obj
                var.targets[0].data_path = '["bb_rotation_z"]'
            except Exception as e:
                print(f"[BlenderBeat] Gyro driver error: {e}")

    def _setup_blossom_camera(self, total_frames: int = 446) -> bpy.types.Object:
        """
        Positions camera along the ceremonial causeway looking forward & upward at the flower,
        framed to capture the full blossom overhead and the illuminated causeway below.
        """
        cam_name = "BB_Camera"
        cam_obj = bpy.data.objects.get(cam_name)
        if cam_obj is None:
            cam_data = bpy.data.cameras.new(cam_name)
            cam_obj = bpy.data.objects.new(cam_name, cam_data)
            bpy.context.scene.collection.objects.link(cam_obj)

        bpy.context.scene.camera = cam_obj
        cam_obj.data.lens = 26.0
        cam_obj.data.clip_end = 350.0

        if cam_obj.animation_data and cam_obj.animation_data.action:
            bpy.data.actions.remove(cam_obj.animation_data.action)

        cam_obj.animation_data_create()

        # Camera at y = 20.0 to 18.5, height z = 1.2
        # Looking toward y = 0.0 with upward pitch
        for frame in range(1, total_frames + 1):
            t = (frame - 1) / total_frames
            y = 24.0 - (math.sin(t * math.pi) * 1.5)
            x = math.sin(t * 2.0 * math.pi) * 0.12
            z = 1.8 + math.cos(t * 2.0 * math.pi) * 0.04

            cam_obj.location = (x, y, z)
            # Pitch 80 degrees (pitch upward towards z=1.5..4.0 at y=0)
            pitch = math.radians(62.0)
            cam_obj.rotation_euler = (pitch, 0.0, math.pi)
            cam_obj.keyframe_insert(data_path="location", frame=frame)
            cam_obj.keyframe_insert(data_path="rotation_euler", frame=frame)

        viz_obj = bpy.data.objects.get("BB_Visualizer")
        if viz_obj:
            from ...visual.camera import setup_camera_zoom
            setup_camera_zoom(cam_obj, viz_obj, base_lens=26.0, zoom_punch_mm=5.0)

        return cam_obj

    def _setup_blossom_lighting(self, col: bpy.types.Collection):
        scene = bpy.context.scene
        if hasattr(scene, 'eevee'):
            scene.eevee.use_raytracing = True
            scene.eevee.fast_gi_quality = 1.0

        if scene.world and scene.world.use_nodes:
            bg = scene.world.node_tree.nodes.get("Background")
            if bg:
                bg.inputs["Color"].default_value = (0.0015, 0.002, 0.006, 1.0)
                bg.inputs["Strength"].default_value = 0.02

        # 1. Central Core Point Light
        light_core_name = "BB_Light_Core"
        light_core = bpy.data.objects.get(light_core_name)
        if light_core is None:
            ldata = bpy.data.lights.new(light_core_name, 'POINT')
            light_core = bpy.data.objects.new(light_core_name, ldata)
            col.objects.link(light_core)
        light_core.location = (0.0, 0.0, 0.8)
        light_core.data.energy = 650.0
        light_core.data.color = (1.0, 0.90, 0.70)
        light_core.data.shadow_soft_size = 0.3

        # 2. Back-Rim Light
        light_rim_name = "BB_Light_BackRim"
        light_rim = bpy.data.objects.get(light_rim_name)
        if light_rim is None:
            ldata_rim = bpy.data.lights.new(light_rim_name, 'SPOT')
            light_rim = bpy.data.objects.new(light_rim_name, ldata_rim)
            col.objects.link(light_rim)
        light_rim.location = (0.0, -10.0, 16.0)
        light_rim.rotation_euler = (math.radians(32.0), 0.0, 0.0)
        light_rim.data.energy = 2200.0
        light_rim.data.color = (1.0, 0.95, 0.88)
        light_rim.data.spot_size = math.radians(70.0)
        light_rim.data.spot_blend = 0.5

        # 3. Soft Front Fill Light
        light_fill_name = "BB_Light_FrontFill"
        light_fill = bpy.data.objects.get(light_fill_name)
        if light_fill is None:
            ldata_fill = bpy.data.lights.new(light_fill_name, 'POINT')
            light_fill = bpy.data.objects.new(light_fill_name, ldata_fill)
            col.objects.link(light_fill)
        light_fill.location = (0.0, 14.0, 2.5)
        light_fill.data.energy = 350.0
        light_fill.data.color = (0.80, 0.88, 1.0)
        light_fill.data.shadow_soft_size = 3.0

        from ...visual.lighting import setup_realtime_glow_compositor
        setup_realtime_glow_compositor()
