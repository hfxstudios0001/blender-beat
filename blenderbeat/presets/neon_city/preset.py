"""
BlenderBeat — Neon Signal City Preset Implementation.

Orchestrates:
1. Procedural Building, Pillar, and Vertical Light Strip Modules
2. Wet Reflective Street Corridor with Puddle Reflections
3. Silhouette Human Scale Figure
4. Geometry Nodes Instancing Engine
5. Hero Audio-Reactive Vertical Light Shaders with Depth Kick Propagation
6. Stable Cinematic Camera (Zero Shake)
7. EEVEE Next Lighting and Real-time Compositor Fog Glow
"""

import bpy
import math
from typing import Dict, Any

from ..base import BasePreset
from .city_builder import create_master_skyscraper_mesh, create_framing_pillar_mesh
from .light_strips import create_vertical_light_strip_mesh, create_overhead_neon_sign_mesh
from .street_ground import create_wet_street_mesh
from .silhouette_figure import create_silhouette_figure
from .city_nodes import create_city_geometry_nodes
from .city_materials import create_city_materials
from .city_camera import setup_city_camera
from ...audio.analyzer import AnalysisResult
from ...animation.mapping import MappingPreset, AudioMapping
from ...visual.geometry import create_visualizer_object


class NeonSignalCityPreset(BasePreset):
    """
    Neon Signal City — futuristic skyscraper corridor with vertical light strips,
    wet reflective street, depth wave propagation, and stable cinematic camera.
    """
    id = "NEON_SIGNAL_CITY"
    name = "Neon Signal City"
    description = (
        "Futuristic cyberpunk skyscraper corridor with vertical LED light columns, "
        "wet reflective ground, kick depth propagation, and stable cinematic camera"
    )
    category = "Sci-Fi Environment"
    collection_name = "BB_NeonCity_Collection"

    def get_mappings(self) -> MappingPreset:
        """Audio mappings tuned for the urban lighting performance."""
        return MappingPreset(
            name="Neon Signal City",
            mappings=[
                # Kick → triggers forward light propagation wave along corridor depth
                AudioMapping(
                    source="kick",
                    target="scale",  # maps to viz custom prop
                    strength=1.0,
                    smooth_attack=0.9,
                    smooth_release=0.08,
                    remap_min=0.0,
                    remap_max=1.0,
                ),
                # Bass → macro breathing of ambient building accents & fog
                AudioMapping(
                    source="bass",
                    target="rotation_z",
                    strength=1.0,
                    smooth_attack=0.4,
                    smooth_release=0.15,
                    remap_min=0.2,
                    remap_max=1.0,
                ),
                # Energy → global reflection & illumination boost
                AudioMapping(
                    source="energy",
                    target="camera_zoom",
                    strength=1.0,
                    smooth_attack=0.3,
                    smooth_release=0.2,
                    remap_min=0.3,
                    remap_max=1.0,
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
        Generate the Neon Signal City scene.
        """
        col = self.get_collection()

        # ── 1. Configuration ──────────────────────────────────────────
        corridor_len = settings.get("corridor_length", 160.0)
        corridor_w = settings.get("corridor_width", 14.0)
        total_frames = settings.get("total_frames", 446)
        cam_reactivity = settings.get("camera_audio_reactivity", 0.0)

        # ── 2. Materials ──────────────────────────────────────────────
        materials = create_city_materials()

        # ── 3. Base Building & Light Modules ──────────────────────────
        bldg_master = create_master_skyscraper_mesh("BB_NC_MasterSkyscraper")
        pillar_master = create_framing_pillar_mesh("BB_NC_FramingPillar")
        strip_master = create_vertical_light_strip_mesh("BB_NC_LightStrip")

        for ob in (bldg_master, pillar_master, strip_master):
            if ob.name not in col.objects:
                col.objects.link(ob)

        # ── 4. Wet Street Ground Plane ────────────────────────────────
        street_obj = create_wet_street_mesh(
            name="BB_NC_WetStreet",
            corridor_length=corridor_len,
            walkway_width=corridor_w * 0.45,
            total_width=corridor_w * 3.2,
        )
        street_obj.data.materials.clear()
        street_obj.data.materials.append(materials["street"])
        if street_obj.name not in col.objects:
            col.objects.link(street_obj)

        # ── 5. Human Silhouette Figure ────────────────────────────────
        figure_obj = create_silhouette_figure(
            name="BB_NC_SilhouetteFigure",
            location=(0.0, 10.0, 0.05),
        )
        figure_obj.scale = (1.25, 1.25, 1.25)
        if figure_obj.name not in col.objects:
            col.objects.link(figure_obj)

        # ── 6. Visualizer Object with Geometry Nodes ──────────────────
        viz_obj = create_visualizer_object("BB_Visualizer")
        if viz_obj.name not in col.objects:
            col.objects.link(viz_obj)

        node_tree = create_city_geometry_nodes(
            viz_obj=viz_obj,
            bldg_obj=bldg_master,
            pillar_obj=pillar_master,
            light_strip_obj=strip_master,
            corridor_length=corridor_len,
            corridor_width=corridor_w,
            materials=materials,
        )

        # ── 7. Setup Drivers & Depth Wave Propagation ─────────────────
        self._setup_city_drivers(viz_obj, node_tree, materials, corridor_len)

        # ── 8. Stable Cinematic Camera (ZERO SHAKE) ───────────────────
        cam = setup_city_camera(
            corridor_length=corridor_len,
            camera_z=1.15,
            camera_start_y=-2.0,
            total_frames=total_frames,
            lens_mm=24.0,
            glide_distance=10.0,
            camera_reactivity=cam_reactivity,
            collection=col,
        )

        # ── 9. Lighting & Real-time Bloom ─────────────────────────────
        self._setup_city_lighting(col, corridor_len)

        print("[BlenderBeat] NEON SIGNAL CITY preset successfully generated!")
        return {
            "visualizer": viz_obj,
            "street": street_obj,
            "figure": figure_obj,
            "camera": cam,
        }

    def _setup_city_drivers(
        self,
        viz_obj: bpy.types.Object,
        node_tree: bpy.types.NodeTree,
        materials: dict,
        corridor_len: float,
    ):
        """Connect audio curves to shader parameters for depth wave propagation."""
        mat_lights = materials.get("lights")
        if not mat_lights or not mat_lights.node_tree:
            return

        lt_tree = mat_lights.node_tree

        # 1. Kick impulse to KickVal in shader
        val_kick = lt_tree.nodes.get("BB_NC_KickVal")
        if val_kick:
            try:
                df = val_kick.outputs[0].driver_add("default_value")
                d = df.driver
                d.type = 'SCRIPTED'
                d.expression = "var"
                var = d.variables.new()
                var.name = "var"
                var.type = 'SINGLE_PROP'
                var.targets[0].id = viz_obj
                var.targets[0].data_path = '["bb_scale"]'
            except Exception as e:
                print(f"[BlenderBeat] Kick driver error: {e}")

        # 2. Bass macro ambient to BassVal in shader
        val_bass = lt_tree.nodes.get("BB_NC_BassVal")
        if val_bass:
            try:
                df = val_bass.outputs[0].driver_add("default_value")
                d = df.driver
                d.type = 'SCRIPTED'
                d.expression = "var"
                var = d.variables.new()
                var.name = "var"
                var.type = 'SINGLE_PROP'
                var.targets[0].id = viz_obj
                var.targets[0].data_path = '["bb_rotation_z"]'
            except Exception as e:
                print(f"[BlenderBeat] Bass driver error: {e}")

        # 3. Propagating Wave Position along Y (moves forward on beat/time)
        val_wave = lt_tree.nodes.get("BB_NC_WavePos")
        if val_wave:
            try:
                df = val_wave.outputs[0].driver_add("default_value")
                d = df.driver
                d.type = 'SCRIPTED'
                # Travels from Y=0 to Y=corridor_len continuously with audio modulation
                d.expression = f"(frame * 2.5) % {corridor_len:.1f}"
            except Exception as e:
                print(f"[BlenderBeat] Wave driver error: {e}")

    def _setup_city_lighting(self, col: bpy.types.Collection, corridor_len: float):
        """Configure pitch-black world, atmospheric depth fog, subtle architectural rim lights, and Compositor Fog Glow."""
        scene = bpy.context.scene

        # World background pitch black
        if scene.world and scene.world.use_nodes:
            bg = scene.world.node_tree.nodes.get("Background")
            if bg:
                bg.inputs["Color"].default_value = (0.001, 0.002, 0.004, 1.0)
                bg.inputs["Strength"].default_value = 0.02

        # Atmospheric Volume Scatter Cube (Optimized density so black levels stay crisp)
        vol_name = "BB_NC_Atmosphere"
        vol_obj = bpy.data.objects.get(vol_name)
        if vol_obj is None:
            mesh = bpy.data.meshes.new(f"{vol_name}_Mesh")
            vol_obj = bpy.data.objects.new(vol_name, mesh)
            import bmesh
            from mathutils import Vector, Matrix
            bm = bmesh.new()
            bmesh.ops.create_cube(
                bm,
                size=1.0,
                matrix=Matrix.Translation(Vector((0, corridor_len / 2.0, 30.0))) @ Matrix.Diagonal(Vector((80.0, corridor_len + 20.0, 65.0, 1.0))),
            )
            bm.to_mesh(mesh)
            bm.free()
            col.objects.link(vol_obj)

        mat_vol = bpy.data.materials.get("BB_Mat_CityAtmosphere") or bpy.data.materials.new("BB_Mat_CityAtmosphere")
        mat_vol.use_nodes = True
        v_tree = mat_vol.node_tree
        v_tree.nodes.clear()
        out_v = v_tree.nodes.new("ShaderNodeOutputMaterial")
        scat = v_tree.nodes.new("ShaderNodeVolumeScatter")
        scat.inputs["Color"].default_value = (0.02, 0.45, 0.65, 1.0)  # Deep cyan volumetric mist
        scat.inputs["Density"].default_value = 0.0018  # Subtle, non-milky atmospheric haze
        scat.inputs["Anisotropy"].default_value = 0.82 # Strong forward scattering towards camera
        v_tree.links.new(scat.outputs["Volume"], out_v.inputs["Volume"])

        vol_obj.data.materials.clear()
        vol_obj.data.materials.append(mat_vol)

        # ── Selective Subtle Architectural Key Lights ─────────────────────
        # Soft backlight behind the silhouette figure (Y = 19.5m) to rim the head and shoulders
        # without spilling a circular hotspot onto the foreground floor
        key_light_data = bpy.data.lights.new("BB_NC_CorridorKey_Data", type='AREA')
        key_light_data.shape = 'RECTANGLE'
        key_light_data.size = 2.0
        key_light_data.size_y = 6.0
        key_light_data.energy = 45.0
        key_light_data.color = (0.1, 0.85, 0.95)  # Cyan backlight
        
        key_light_obj = bpy.data.objects.get("BB_NC_CorridorKey")
        if key_light_obj is None:
            key_light_obj = bpy.data.objects.new("BB_NC_CorridorKey", key_light_data)
            col.objects.link(key_light_obj)
        # Positioned behind the figure pointing slightly forward/upward as a rim kicker
        key_light_obj.location = (0.0, 18.5, 1.8)
        key_light_obj.rotation_euler = (1.57, 0.0, 0.0)

        # Distant soft magenta fill light (Y = 45m)
        accent_light_data = bpy.data.lights.new("BB_NC_CorridorAccent_Data", type='POINT')
        accent_light_data.energy = 80.0
        accent_light_data.color = (0.85, 0.05, 0.75)  # Magenta accent
        accent_light_data.shadow_soft_size = 5.0

        accent_light_obj = bpy.data.objects.get("BB_NC_CorridorAccent")
        if accent_light_obj is None:
            accent_light_obj = bpy.data.objects.new("BB_NC_CorridorAccent", accent_light_data)
            col.objects.link(accent_light_obj)
        accent_light_obj.location = (-6.5, 45.0, 8.0)

        # Real-time Compositor Fog Glow bloom
        from ...visual.lighting import setup_realtime_glow_compositor
        setup_realtime_glow_compositor()
        print("[BlenderBeat] Atmospheric haze, accent lights, and Fog Glow configured.")
