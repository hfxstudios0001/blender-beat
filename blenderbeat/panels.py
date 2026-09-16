"""
BlenderBeat — UI Panels.

Blender sidebar panel with sections for:
Music, Visual, Loop, Camera, Render.
"""

import bpy
from .utils.validation import format_duration, format_file_size


class BB_PT_MainPanel(bpy.types.Panel):
    """BlenderBeat main panel"""
    bl_idname = "BB_PT_MainPanel"
    bl_label = "BlenderBeat"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BlenderBeat"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Music-Reactive 3D Visualizer", icon='PLAY_SOUND')


class BB_PT_MusicPanel(bpy.types.Panel):
    """Audio import and analysis"""
    bl_idname = "BB_PT_MusicPanel"
    bl_label = "Music"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BlenderBeat"
    bl_parent_id = "BB_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        audio = context.scene.bb_audio

        # File info
        box = layout.box()
        col = box.column(align=True)

        if audio.filepath:
            import os
            filename = os.path.basename(bpy.path.abspath(audio.filepath))
            col.label(text=f"File: {filename}", icon='SOUND')

            if audio.duration > 0:
                col.label(text=f"Duration: {format_duration(audio.duration)}")
            if audio.sample_rate > 0:
                col.label(text=f"Sample Rate: {audio.sample_rate} Hz")
        else:
            col.label(text="No audio loaded", icon='INFO')

        # Import button
        layout.operator("blenderbeat.import_audio", icon='FILE_SOUND')

        layout.separator()

        # BPM override
        row = layout.row()
        row.prop(audio, "bpm_override", text="BPM Override")

        # Analysis resolution
        row = layout.row()
        row.prop(audio, "analysis_resolution", text="Resolution")

        # Analyze button
        row = layout.row()
        row.scale_y = 1.5
        if audio.filepath:
            row.operator("blenderbeat.analyze_audio",
                         icon='FCURVE', text="ANALYZE")
        else:
            row.enabled = False
            row.operator("blenderbeat.analyze_audio",
                         icon='FCURVE', text="ANALYZE")

        # Analysis results
        if audio.is_analyzed:
            box = layout.box()
            col = box.column(align=True)
            col.label(text="Analysis Results", icon='CHECKMARK')
            col.label(text=f"BPM: {audio.detected_bpm:.1f}")
            col.label(text=f"Beats: {audio.beat_count}")
            col.label(text=f"Analysis Frames: {audio.n_frames}")


class BB_PT_VisualPanel(bpy.types.Panel):
    """Visual generation settings"""
    bl_idname = "BB_PT_VisualPanel"
    bl_label = "Visual"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BlenderBeat"
    bl_parent_id = "BB_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        visual = context.scene.bb_visual
        audio = context.scene.bb_audio

        # Preset selector
        layout.prop(visual, "preset", text="Preset")

        layout.separator()

        # Parameters
        col = layout.column(align=True)
        col.prop(visual, "complexity", text="Complexity", slider=True)
        col.prop(visual, "density", text="Density", slider=True)
        col.prop(visual, "variation", text="Variation", slider=True)

        layout.separator()

        # Preset-specific controls
        if visual.preset == 'SIGNAL_DRIFT':
            box = layout.box()
            box.label(text="Digital Apparition — Spectral Human", icon='USER')
            box.label(text="Authentic Mesh: 1.80m Human Base", icon='CHECKMARK')
            box.label(text="System: Poisson Dots + Z-Aligned Bars + Streaks", icon='NODETREE')
            box.label(text="Shader: Violet (-X) to Cyan (+X) CRT Scan", icon='MATERIAL')
            box.label(text="Reactivity: Kick Radial Burst & Zoom Punch", icon='DRIVER')
        elif visual.preset == 'COSMIC_BLOSSOM':
            box = layout.box()
            box.label(text="Hero Flower Architecture", icon='OUTLINER_OB_CURVES')
            box.prop(visual, "blossom_color_palette", text="Theme")
            box.prop(visual, "blossom_outer_petals", text="Petal Count")
            box.prop(visual, "blossom_open_factor", text="Bloom Flare", slider=True)

            box_core = layout.box()
            box_core.label(text="Cosmic Energy & FX", icon='LIGHT_SUN')
            box_core.prop(visual, "blossom_core_energy", text="Core Intensity")
            box_core.prop(visual, "blossom_shard_count", text="Floating Shards")
            box_core.prop(visual, "blossom_water_reflections", text="Temple Platform")
        elif visual.preset == 'INFINITE_BLACK_HOLE_TUNNEL':
            box = layout.box()
            box.label(text="Aura Sync Lighting", icon='LIGHT_SUN')
            box.prop(visual, "tunnel_color_mode", text="Mode")
            if visual.tunnel_color_mode == 'CUSTOM':
                box.prop(visual, "tunnel_custom_color", text="Color")
            box.prop(visual, "tunnel_glow_min", text="Resting Opacity", slider=True)
            box.prop(visual, "tunnel_glow_max", text="Peak Glow")
            
            box_geo = layout.box()
            box_geo.label(text="Corridor Architecture", icon='MESH_CYLINDER')
            box_geo.prop(visual, "tunnel_ring_count", text="Rings")
            box_geo.prop(visual, "tunnel_radius", text="Radius")
            box_geo.prop(visual, "tunnel_enable_debris", text="Floating Debris")
        elif visual.preset == 'INFINITE_LIGHT_GRID':
            box = layout.box()
            box.label(text="Aura Sync Lighting", icon='LIGHT_SUN')
            box.prop(visual, "tunnel_color_mode", text="Mode")
            if visual.tunnel_color_mode == 'CUSTOM':
                box.prop(visual, "tunnel_custom_color", text="Color")
            box.prop(visual, "tunnel_glow_min", text="Resting Opacity", slider=True)
            box.prop(visual, "tunnel_glow_max", text="Peak Glow")

            box_geo = layout.box()
            box_geo.label(text="Grid Architecture", icon='MESH_GRID')
            box_geo.prop(visual, "grid_frame_count", text="Frames")
            box_geo.prop(visual, "grid_frame_size", text="Frame Size")
            box_geo.prop(visual, "grid_twist_amount", text="Twist", slider=True)
        elif visual.preset == 'AUDIO_SPHERE':
            col = layout.column(align=True)
            col.prop(visual, "sphere_radius", text="Radius")
            col.prop(visual, "bar_max_length", text="Bar Length")
        elif visual.preset == 'QUANTUM_FIELD':
            col = layout.column(align=True)
            col.prop(visual, "sphere_radius", text="Grid Radius")

        layout.separator()

        # Seed
        row = layout.row(align=True)
        row.prop(visual, "seed", text="Seed")

        layout.separator()

        # Generate button
        row = layout.row()
        row.scale_y = 2.0
        if audio.is_analyzed:
            row.operator("blenderbeat.generate_visual",
                         icon='SHADING_RENDERED',
                         text="GENERATE VISUAL")
        else:
            row.enabled = False
            row.operator("blenderbeat.generate_visual",
                         icon='SHADING_RENDERED',
                         text="GENERATE VISUAL")

        # Status
        if visual.is_generated:
            box = layout.box()
            box.label(text="Visual generated ✓", icon='CHECKMARK')


class BB_PT_LoopPanel(bpy.types.Panel):
    """Loop settings"""
    bl_idname = "BB_PT_LoopPanel"
    bl_label = "Loop"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BlenderBeat"
    bl_parent_id = "BB_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        loop = context.scene.bb_loop
        audio = context.scene.bb_audio

        layout.prop(loop, "full_song", text="Full Song (Entire Track)", icon='TIME')

        col = layout.column(align=True)
        if loop.full_song:
            col.enabled = False
        col.prop(loop, "loop_bars", text="Bars")
        col.prop(loop, "beats_per_bar", text="Beats/Bar")

        if loop.loop_frames > 0:
            layout.separator()
            box = layout.box()
            col = box.column(align=True)
            col.label(text=f"Frames: {loop.loop_frames}")
            col.label(text=f"Duration: {format_duration(loop.loop_duration)}")



class BB_PT_CameraPanel(bpy.types.Panel):
    """Camera settings"""
    bl_idname = "BB_PT_CameraPanel"
    bl_label = "Camera"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BlenderBeat"
    bl_parent_id = "BB_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        cam = context.scene.bb_camera

        layout.prop(cam, "mode", text="Mode")

        layout.separator()

        col = layout.column(align=True)
        col.prop(cam, "distance", text="Distance")
        col.prop(cam, "height", text="Height")
        col.prop(cam, "fov", text="FOV")

        if cam.mode == 'ORBIT':
            col.prop(cam, "orbit_speed", text="Orbit Speed")

        layout.separator()
        layout.prop(cam, "shake_intensity", text="Shake", slider=True)


class BB_PT_RenderPanel(bpy.types.Panel):
    """Render settings"""
    bl_idname = "BB_PT_RenderPanel"
    bl_label = "Render"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BlenderBeat"
    bl_parent_id = "BB_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        render_props = context.scene.bb_render
        visual = context.scene.bb_visual

        # Renderer
        layout.prop(render_props, "renderer", text="Engine")

        layout.separator()

        # Resolution
        row = layout.row(align=True)
        row.prop(render_props, "resolution_x", text="W")
        row.prop(render_props, "resolution_y", text="H")

        # FPS
        layout.prop(render_props, "fps", text="FPS")

        # Output path
        layout.prop(render_props, "output_path", text="Output")

        layout.separator()

        # Render button
        row = layout.row()
        row.scale_y = 1.5
        if visual.is_generated:
            row.operator("blenderbeat.render_animation",
                         icon='RENDER_ANIMATION',
                         text="RENDER")
        else:
            row.enabled = False
            row.operator("blenderbeat.render_animation",
                         icon='RENDER_ANIMATION',
                         text="RENDER")

        layout.separator()

        # Clear button
        layout.operator("blenderbeat.clear_scene",
                        icon='TRASH', text="Clear Scene")


class BB_PT_DependenciesPanel(bpy.types.Panel):
    """Dependencies status"""
    bl_idname = "BB_PT_DependenciesPanel"
    bl_label = "Dependencies"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BlenderBeat"
    bl_parent_id = "BB_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        from .utils.dependencies import check_all_dependencies
        deps = check_all_dependencies()

        col = layout.column(align=True)
        for dep_name, available in deps.items():
            icon = 'CHECKMARK' if available else 'ERROR'
            status = "Installed" if available else "Not installed"
            col.label(text=f"{dep_name}: {status}", icon=icon)

        if not deps.get("scipy", False):
            layout.separator()
            layout.operator("blenderbeat.install_deps",
                           icon='IMPORT',
                           text="Install scipy")


# All panel classes to register
PANEL_CLASSES = [
    BB_PT_MainPanel,
    BB_PT_MusicPanel,
    BB_PT_VisualPanel,
    BB_PT_LoopPanel,
    BB_PT_CameraPanel,
    BB_PT_RenderPanel,
    BB_PT_DependenciesPanel,
]


def register_panels():
    """Register all panels."""
    for cls in PANEL_CLASSES:
        bpy.utils.register_class(cls)


def unregister_panels():
    """Unregister all panels."""
    for cls in reversed(PANEL_CLASSES):
        bpy.utils.unregister_class(cls)
