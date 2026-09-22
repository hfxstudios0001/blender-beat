"""
BlenderBeat — Pulse Tunnel Preset Implementation (Rebuilt).

Head-on radial spoke LED tunnel:
  - Concentric ring zones with radial bar segments (dartboard pattern)
  - Per-segment stochastic ON/OFF synced to beat
  - Alternating cyan / magenta coloring
  - Constant-speed forward camera (ZERO audio reactivity)
  - Deep infinite tunnel illusion
"""

import bpy
import math
from typing import Dict, Any

from ..base import BasePreset
from .tunnel_ring import create_master_ring_mesh
from .tunnel_materials import create_pulse_tunnel_materials
from .tunnel_nodes import create_pulse_tunnel_geometry_nodes
from .tunnel_camera import setup_pulse_tunnel_camera
from .tunnel_lighting import setup_pulse_tunnel_lighting
from ...audio.analyzer import AnalysisResult
from ...animation.mapping import MappingPreset, AudioMapping
from ...visual.geometry import create_visualizer_object


class PulseTunnelPreset(BasePreset):
    """
    Pulse Tunnel — Head-on radial spoke LED tunnel where every segment
    fires stochastically on beat with cyan/magenta alternation.
    """
    id = "PULSE_TUNNEL"
    name = "Pulse Tunnel"
    description = (
        "Futuristic circular tunnel with radial LED spokes, "
        "per-segment ON/OFF synced to beat, and constant-speed camera"
    )
    category = "Sci-Fi Tunnel"
    collection_name = "BB_PulseTunnel_Collection"

    def get_mappings(self) -> MappingPreset:
        """Audio mappings for the tunnel lighting performance."""
        return MappingPreset(
            name="Pulse Tunnel",
            mappings=[
                # Kick → drives segment ON/OFF probability + white-hot
                AudioMapping(
                    source="kick",
                    target="scale",
                    strength=1.0,
                    smooth_attack=0.95,
                    smooth_release=0.04,
                    remap_min=0.0,
                    remap_max=1.0,
                ),
                # Bass → color shifting
                AudioMapping(
                    source="bass",
                    target="rotation_z",
                    strength=1.0,
                    smooth_attack=0.4,
                    smooth_release=0.12,
                    remap_min=0.1,
                    remap_max=1.0,
                ),
                # Energy → overall emission boost
                AudioMapping(
                    source="energy",
                    target="emission_strength",
                    strength=1.0,
                    smooth_attack=0.3,
                    smooth_release=0.15,
                    remap_min=0.15,
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
        """Generate the complete Pulse Tunnel scene."""
        col = self.get_collection()

        # ── Configuration ─────────────────────────────────────────────
        ring_count = settings.get("pt_tunnel_rings", settings.get("tunnel_ring_count", 80))
        spacing = settings.get("spacing", 1.8)
        tunnel_depth = ring_count * spacing
        outer_radius = settings.get("pt_tunnel_radius", settings.get("tunnel_radius", 8.0))
        total_frames = settings.get("total_frames", 446)

        # Palette & Glow settings
        pt_palette = settings.get("pt_color_palette", 'CYBER_CYAN_MAGENTA')
        pt_custom_prim = settings.get("pt_custom_primary", (0.0, 0.9, 1.0))
        pt_custom_sec = settings.get("pt_custom_secondary", (1.0, 0.02, 0.8))
        pt_glow_intensity = settings.get("pt_glow_intensity", 35.0)
        pt_resting_glow = settings.get("pt_resting_glow", 0.0)
        pt_bloom_threshold = settings.get("pt_bloom_threshold", 0.65)
        pt_bloom_size = settings.get("pt_bloom_size", 0.95)

        # ── Materials ─────────────────────────────────────────────────
        materials = create_pulse_tunnel_materials(
            palette_name=pt_palette,
            custom_primary=pt_custom_prim,
            custom_secondary=pt_custom_sec,
            glow_intensity=pt_glow_intensity,
            resting_glow=pt_resting_glow,
        )

        # ── Master Radial Disk Mesh ───────────────────────────────────
        ring_obj = create_master_ring_mesh(
            name="BB_PT_MasterRing",
            outer_radius=outer_radius,
            segments_per_zone=32,
            mat_hull=materials["hull"],
            mat_led=materials["led_primary"],
            mat_glow=materials["led_accent"],
        )
        if ring_obj.name not in col.objects:
            col.objects.link(ring_obj)

        # ── Visualizer Object ─────────────────────────────────────────
        viz_obj = create_visualizer_object("BB_Visualizer")
        if viz_obj.name not in col.objects:
            col.objects.link(viz_obj)

        # Copy materials to visualizer so realized instances render
        viz_obj.data.materials.clear()
        for mat in ring_obj.data.materials:
            viz_obj.data.materials.append(mat)

        # ── Geometry Nodes Tunnel Engine ───────────────────────────────
        node_tree = create_pulse_tunnel_geometry_nodes(
            viz_obj=viz_obj,
            ring_obj=ring_obj,
            ring_count=ring_count,
            spacing=spacing,
        )

        # ── Audio → Shader Drivers ────────────────────────────────────
        self._setup_tunnel_drivers(viz_obj, node_tree, materials, tunnel_depth)

        # ── Atmospheric Lighting & Fog Glow ───────────────────────────
        setup_pulse_tunnel_lighting(
            collection=col,
            tunnel_depth=tunnel_depth,
            haze_density=0.0,
            bloom_threshold=pt_bloom_threshold,
            bloom_size=pt_bloom_size,
        )

        # ── Camera (ZERO audio reactivity) ────────────────────────────
        cam = setup_pulse_tunnel_camera(
            tunnel_depth=tunnel_depth,
            camera_z_start=1.5,
            total_frames=total_frames,
            lens_mm=20.0,
            collection=col,
        )

        print("[BlenderBeat] PULSE TUNNEL preset generated!")
        return {
            "visualizer": viz_obj,
            "master_ring": ring_obj,
            "camera": cam,
        }

    def _setup_tunnel_drivers(
        self,
        viz_obj: bpy.types.Object,
        node_tree: bpy.types.NodeTree,
        materials: dict,
        tunnel_depth: float,
    ):
        """Connect baked audio custom properties to internal shader Value nodes."""
        mat_led = materials.get("led_primary")
        if not mat_led or not mat_led.node_tree:
            print("[BlenderBeat] WARNING: LED material not found for driver setup")
            return

        led_tree = mat_led.node_tree

        # Kick → BB_PT_KickVal
        self._add_value_driver(
            led_tree, "BB_PT_KickVal",
            viz_obj, '["bb_scale"]',
        )

        # Bass → BB_PT_BassVal
        self._add_value_driver(
            led_tree, "BB_PT_BassVal",
            viz_obj, '["bb_rotation_z"]',
        )

        # Energy → BB_PT_EnergyVal
        self._add_value_driver(
            led_tree, "BB_PT_EnergyVal",
            viz_obj, '["bb_emission_strength"]',
        )

        # Wave position: frame-based + kick acceleration
        wave_node = led_tree.nodes.get("BB_PT_WavePos")
        if wave_node:
            try:
                df = wave_node.outputs[0].driver_add("default_value")
                d = df.driver
                d.type = 'SCRIPTED'
                d.expression = f"-((frame * 3.5 + var * 25.0) % {tunnel_depth:.1f})"
                var = d.variables.new()
                var.name = "var"
                var.type = 'SINGLE_PROP'
                var.targets[0].id = viz_obj
                var.targets[0].data_path = '["bb_scale"]'
            except Exception as e:
                print(f"[BlenderBeat] Wave position driver error: {e}")

        # Glow ring energy driver
        mat_glow = materials.get("led_accent")
        if mat_glow and mat_glow.node_tree:
            self._add_value_driver(
                mat_glow.node_tree, "BB_PT_GlowEnergy",
                viz_obj, '["bb_emission_strength"]',
            )

        # GN Value nodes
        gn_configs = [
            ("BB_PT_GN_KickVal", '["bb_scale"]', "var"),
            ("BB_PT_GN_BassVal", '["bb_rotation_z"]', "var"),
            ("BB_PT_GN_EnergyVal", '["bb_emission_strength"]', "var"),
            ("BB_PT_GN_TimeVal", '["bb_rotation_z"]', "var * 2.5"),
        ]
        for node_name, data_path, expr in gn_configs:
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
                    var.targets[0].data_path = data_path
                except Exception as e:
                    print(f"[BlenderBeat] GN driver error on {node_name}: {e}")

        print("[BlenderBeat] Pulse Tunnel drivers configured")

    @staticmethod
    def _add_value_driver(
        node_tree: bpy.types.NodeTree,
        node_name: str,
        source_obj: bpy.types.Object,
        data_path: str,
        expression: str = "var",
    ):
        """Helper to add a driver from source_obj custom prop to a Value node."""
        node = node_tree.nodes.get(node_name)
        if not node:
            print(f"[BlenderBeat] Value node '{node_name}' not found")
            return

        try:
            df = node.outputs[0].driver_add("default_value")
            d = df.driver
            d.type = 'SCRIPTED'
            d.expression = expression
            var = d.variables.new()
            var.name = "var"
            var.type = 'SINGLE_PROP'
            var.targets[0].id = source_obj
            var.targets[0].data_path = data_path
        except Exception as e:
            print(f"[BlenderBeat] Driver error on {node_name}: {e}")
