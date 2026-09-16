"""
BlenderBeat — Signal Drift Preset Implementation.

Orchestrates:
1. Authentic human mesh loading (`human_base.blend`, 1.80m tall, anatomical fidelity)
2. Self-contained multi-scale Geometry Nodes system (Micro dot matrix, Meso vertical bars, Macro streaks)
3. Dual-tone spectral material (Violet -> Cyan with white-hot beat punch)
4. Cinematic 35mm Orbit camera
5. EEVEE Next lighting and Compositor Fog Glow
6. Audio driver connections
"""

import bpy
import math
from typing import Dict, Any

from ..base import BasePreset
from .mannequin import create_mannequin_mesh
from .drift_nodes import create_drift_geometry_nodes
from .drift_materials import create_signal_drift_material
from .drift_camera import setup_drift_camera
from ...audio.analyzer import AnalysisResult
from ...animation.mapping import MappingPreset, AudioMapping
from ...visual.geometry import create_visualizer_object


class SignalDriftPreset(BasePreset):
    """
    Digital Apparition — spectral humanoid dissolving into light fragments.
    """
    id = "SIGNAL_DRIFT"
    name = "Signal Drift"
    description = (
        "Digital apparition — spectral humanoid dissolving "
        "into radial light fragments and temporal echoes"
    )
    category = "Abstract VFX"
    collection_name = "BB_SignalDrift_Collection"

    def get_mappings(self) -> MappingPreset:
        """Audio mappings tuned for the spectral apparition aesthetic."""
        return MappingPreset(
            name="Signal Drift",
            mappings=[
                # Kick → explosive zoom punch and radial fragment displacement
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
                # Bass → subtle figure breathing / radial displacement
                AudioMapping(
                    source="bass",
                    target="displacement",
                    strength=1.0,
                    smooth_attack=0.5,
                    smooth_release=0.1,
                    remap_min=0.0,
                    remap_max=1.0,
                    spring_enabled=True,
                    spring_stiffness=0.4,
                    spring_damping=0.7,
                ),
                # Energy → overall emission intensity
                AudioMapping(
                    source="energy",
                    target="emission_strength",
                    strength=1.0,
                    smooth_attack=0.3,
                    smooth_release=0.1,
                    remap_min=0.3,
                    remap_max=1.5,
                ),
                # Mid → subtle figure rotation
                AudioMapping(
                    source="mid",
                    target="rotation_z",
                    strength=0.6,
                    smooth_attack=0.2,
                    smooth_release=0.15,
                    remap_min=0.0,
                    remap_max=0.5,
                ),
                # Onset → transient camera shake
                AudioMapping(
                    source="onset_strength",
                    target="camera_shake",
                    strength=0.4,
                    smooth_attack=0.8,
                    smooth_release=0.05,
                    remap_min=0.0,
                    remap_max=0.3,
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
        Generate the Signal Drift scene with authentic human silhouette.
        """
        col = self.get_collection()

        # ── 1. Configuration ──────────────────────────────────────────
        head_only = settings.get("head_only", True)
        human_height = settings.get("human_height", 0.60 if head_only else 1.80)
        
        # Sampling optimized for high framerate and zero viewport lag:
        # Head only requires ~18k-22k points total instead of 60k+ full body points
        poisson_dist_micro = settings.get("poisson_dist_micro", 0.0038 if head_only else 0.0055)
        density_max_micro = settings.get("density_max_micro", 32000.0 if head_only else 45000.0)
        poisson_dist_bars = settings.get("poisson_dist_bars", 0.009 if head_only else 0.015)
        density_max_bars = settings.get("density_max_bars", 8000.0 if head_only else 12000.0)
        streak_count = settings.get("streak_count", 150 if head_only else 300)
        ghost_copies = settings.get("ghost_copies", 2 if head_only else 3)
        total_frames = settings.get("total_frames", 446)

        # ── 2. Material ───────────────────────────────────────────────
        min_glow = settings.get("min_glow", 1.2)
        peak_emission = settings.get("peak_emission", 32.0)
        scan_density = settings.get("scan_line_density", 85.0 if head_only else 60.0)
        scan_strength = settings.get("scan_line_strength", 0.35)

        mat_drift = create_signal_drift_material(
            name="BB_Mat_SignalDrift",
            min_glow=min_glow,
            peak_emission=peak_emission,
            scan_line_density=scan_density,
            scan_line_strength=scan_strength,
        )

        # ── 3. Authentic Human Face Source Mesh ───────────────────────
        mannequin = create_mannequin_mesh(
            name="BB_SD_Mannequin",
            total_height=human_height,
            head_only=head_only,
        )
        if mannequin.name not in col.objects:
            col.objects.link(mannequin)

        # ── 4. Visualizer Object ──────────────────────────────────────
        viz_obj = create_visualizer_object("BB_Visualizer")
        if viz_obj.name not in col.objects:
            col.objects.link(viz_obj)

        viz_obj.data.materials.clear()
        viz_obj.data.materials.append(mat_drift)

        # ── 5. Geometry Nodes System ──────────────────────────────────
        node_tree = create_drift_geometry_nodes(
            viz_obj=viz_obj,
            mannequin_obj=mannequin,
            poisson_dist_micro=poisson_dist_micro,
            density_max_micro=density_max_micro,
            poisson_dist_bars=poisson_dist_bars,
            density_max_bars=density_max_bars,
            streak_count=streak_count,
            ghost_copies=ghost_copies,
            center_z=0.0 if head_only else 1.0,
        )

        # ── 6. Drivers ───────────────────────────────────────────────
        self._setup_drift_drivers(viz_obj, node_tree, mat_drift)

        # ── 7. Camera (Framed specifically for Face Portrait) ───────────
        cam = setup_drift_camera(
            orbit_radius=settings.get("orbit_radius", 0.75 if head_only else 3.0),
            orbit_height=settings.get("orbit_height", 0.02 if head_only else 1.0),
            total_frames=total_frames,
            lens_mm=settings.get("lens_mm", 70.0 if head_only else 38.0),
            target_z=0.0 if head_only else 1.0,
            collection=col,
        )

        # ── 8. Lighting & Compositor ─────────────────────────────────
        self._setup_drift_lighting(col)

        print("[BlenderBeat] Signal Drift preset generated successfully with anatomical human!")
        return {
            "visualizer": viz_obj,
            "mannequin": mannequin,
            "camera": cam,
        }

    def _setup_drift_drivers(
        self,
        viz_obj: bpy.types.Object,
        node_tree: bpy.types.NodeTree,
        mat: bpy.types.Material,
    ):
        """Connect baked audio properties to GN value nodes and material."""
        driver_configs = [
            ("BB_SDriftBassVal", "bb_displacement", "var"),
            ("BB_SDriftKickVal", "bb_camera_zoom", "var"),
            ("BB_SDriftEnergyVal", "bb_emission_strength", "var"),
            ("BB_SDriftTimeVal", "bb_rotation_z", "var * 2.0"),
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
                    print(f"[BlenderBeat] Signal Drift GN driver error on {node_name}: {e}")

        # Material emission driver
        if mat and mat.node_tree:
            val_node = mat.node_tree.nodes.get("BB_SDriftAudioEmission")
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
                    print(f"[BlenderBeat] Signal Drift material emission driver error: {e}")

    def _setup_drift_lighting(self, col: bpy.types.Collection):
        """Configure black background, EEVEE settings, and Fog Glow."""
        scene = bpy.context.scene

        if hasattr(scene, 'eevee'):
            try:
                scene.eevee.use_raytracing = True
                scene.eevee.fast_gi_quality = 1.0
            except AttributeError:
                pass

        if scene.world and scene.world.use_nodes:
            bg = scene.world.node_tree.nodes.get("Background")
            if bg:
                bg.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
                bg.inputs["Strength"].default_value = 0.0

        from ...visual.lighting import setup_realtime_glow_compositor
        setup_realtime_glow_compositor()

        print("[BlenderBeat] Signal Drift lighting configured.")
