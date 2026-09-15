"""
BlenderBeat — Operators.

All Blender operator classes that handle user actions:
importing audio, analyzing, generating visuals, rendering.
"""

import bpy
import os
import traceback
from bpy.props import StringProperty

from .utils.validation import validate_audio_file, format_duration, format_file_size
from .utils.performance import Timer


class BB_OT_ImportAudio(bpy.types.Operator):
    """Import an audio file for visualization"""
    bl_idname = "blenderbeat.import_audio"
    bl_label = "Import Audio"
    bl_description = "Select an audio file (WAV, MP3, FLAC, OGG) for analysis and visualization"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        subtype='FILE_PATH',
        default="",
    )

    filter_glob: StringProperty(
        default="*.wav;*.wave;*.mp3;*.flac;*.ogg",
        options={'HIDDEN'},
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        audio = context.scene.bb_audio

        # Validate
        valid, msg = validate_audio_file(self.filepath)
        if not valid:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        audio.filepath = self.filepath
        audio.is_analyzed = False

        # Get quick file info
        from .audio.loader import get_audio_info
        info = get_audio_info(self.filepath)

        if "error" in info:
            self.report({'WARNING'}, f"Could not read metadata: {info['error']}")
        else:
            audio.duration = info.get("duration", 0)
            audio.sample_rate = info.get("sample_rate", 0)

        filename = os.path.basename(self.filepath)
        self.report({'INFO'}, f"Audio loaded: {filename}")

        return {'FINISHED'}


class BB_OT_AnalyzeAudio(bpy.types.Operator):
    """Analyze the imported audio file"""
    bl_idname = "blenderbeat.analyze_audio"
    bl_label = "Analyze Audio"
    bl_description = "Run audio analysis: BPM, beats, frequency bands, sections"
    bl_options = {'REGISTER'}

    def execute(self, context):
        audio = context.scene.bb_audio

        if not audio.filepath:
            self.report({'ERROR'}, "No audio file imported. Import a WAV file first.")
            return {'CANCELLED'}

        valid, msg = validate_audio_file(bpy.path.abspath(audio.filepath))
        if not valid:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        filepath = bpy.path.abspath(audio.filepath)

        # Check for cached analysis
        from .audio.cache import load_analysis, save_analysis, is_cache_valid

        if is_cache_valid(filepath):
            analysis = load_analysis(filepath)
            if analysis is not None:
                self._store_analysis(context, analysis)
                self.report({'INFO'},
                    f"Loaded from cache: BPM={analysis.bpm}, "
                    f"beats={len(analysis.beat_times)}")
                return {'FINISHED'}

        # Run fresh analysis
        try:
            # Try installing scipy first
            from .utils.dependencies import ensure_scipy
            scipy_ok, scipy_msg = ensure_scipy()
            if not scipy_ok:
                self.report({'WARNING'},
                    f"scipy not available ({scipy_msg}). "
                    "Using basic analysis mode.")

            from .audio.analyzer import analyze_audio

            hop_map = {'LOW': 1024, 'MEDIUM': 512, 'HIGH': 256}
            hop_length = hop_map.get(audio.analysis_resolution, 512)

            user_bpm = audio.bpm_override if audio.bpm_override > 0 else None

            with Timer("Full analysis"):
                analysis = analyze_audio(
                    filepath,
                    hop_length=hop_length,
                    user_bpm=user_bpm,
                )

            # Cache the results
            save_analysis(analysis, filepath)

            # Store in scene properties
            self._store_analysis(context, analysis)

            # Store the analysis object on the scene for later use
            # (using a module-level cache since we can't store Python
            # objects in Blender properties)
            _analysis_cache[filepath] = analysis

            self.report({'INFO'},
                f"Analysis complete: BPM={analysis.bpm}, "
                f"beats={len(analysis.beat_times)}, "
                f"frames={analysis.n_frames}")

        except Exception as e:
            traceback.print_exc()
            self.report({'ERROR'}, f"Analysis failed: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def _store_analysis(self, context, analysis):
        """Store analysis results in scene properties."""
        audio = context.scene.bb_audio
        audio.detected_bpm = analysis.bpm
        audio.duration = analysis.duration
        audio.sample_rate = analysis.sample_rate
        audio.is_analyzed = True
        audio.beat_count = len(analysis.beat_times)
        audio.n_frames = analysis.n_frames

        filepath = bpy.path.abspath(audio.filepath)
        _analysis_cache[filepath] = analysis


class BB_OT_GenerateVisual(bpy.types.Operator):
    """Generate the music-reactive visual scene"""
    bl_idname = "blenderbeat.generate_visual"
    bl_label = "Generate Visual"
    bl_description = "Generate a procedural music-reactive 3D visualizer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        audio = context.scene.bb_audio
        visual = context.scene.bb_visual
        loop = context.scene.bb_loop
        render_props = context.scene.bb_render
        camera = context.scene.bb_camera

        # Validate analysis
        if not audio.is_analyzed:
            self.report({'ERROR'},
                "Audio not analyzed yet. Click 'Analyze' first.")
            return {'CANCELLED'}

        filepath = bpy.path.abspath(audio.filepath)

        # Get analysis from cache
        analysis = _analysis_cache.get(filepath)
        if analysis is None:
            # Try loading from disk cache
            from .audio.cache import load_analysis
            analysis = load_analysis(filepath)
            if analysis is None:
                self.report({'ERROR'},
                    "Analysis data not found. Re-analyze the audio.")
                return {'CANCELLED'}
            _analysis_cache[filepath] = analysis

        # Map preset enum to name
        preset_map = {
            'COSMIC_BLOSSOM': "Cosmic Blossom",
            'INFINITE_BLACK_HOLE_TUNNEL': "Infinite Black Hole Tunnel",
            'INFINITE_LIGHT_GRID': "Infinite Light Grid",
            'AUDIO_SPHERE': "Audio Sphere",
            'QUANTUM_FIELD': "Quantum Field",
        }
        preset_name = preset_map.get(visual.preset, "Cosmic Blossom")

        # Determine BPM
        bpm = audio.bpm_override if audio.bpm_override > 0 else audio.detected_bpm
        if bpm <= 0:
            bpm = 120.0

        try:
            from .visual.generator import generate_visualizer

            result = generate_visualizer(
                analysis=analysis,
                preset_name=preset_name,
                bpm=bpm,
                loop_bars=loop.loop_bars,
                beats_per_bar=loop.beats_per_bar,
                fps=render_props.fps,
                renderer=render_props.renderer,
                resolution_x=render_props.resolution_x,
                resolution_y=render_props.resolution_y,
                complexity=visual.complexity,
                seed=visual.seed,
                full_song=loop.full_song,
            )

            # Update UI properties
            visual.is_generated = True
            loop.loop_frames = result["total_frames"]
            loop.loop_duration = result["loop_duration"]

            # Load audio for playback in Blender
            self._load_audio_for_playback(context, filepath)

            self.report({'INFO'},
                f"Generated: {result['total_frames']} frames, "
                f"{result['total_keyframes']} keyframes, "
                f"BPM={bpm}")

        except Exception as e:
            traceback.print_exc()
            self.report({'ERROR'}, f"Generation failed: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def _load_audio_for_playback(self, context, filepath):
        """Load audio into Blender's sequencer for timeline playback."""
        try:
            scene = context.scene

            # Ensure scene has a sequence editor
            if not scene.sequence_editor:
                scene.sequence_editor_create()

            # Remove existing BB audio strips across Blender versions
            seq_editor = scene.sequence_editor
            strip_list = getattr(seq_editor, "strips_all", None) or getattr(seq_editor, "sequences_all", None) or getattr(seq_editor, "sequences", [])
            for strip in list(strip_list):
                if strip.name.startswith("BB_Audio"):
                    if hasattr(seq_editor, "strips"):
                        seq_editor.strips.remove(strip)
                    elif hasattr(seq_editor, "sequences"):
                        seq_editor.sequences.remove(strip)

            # Add audio strip (Blender 5.0+ uses strips, older versions use sequences)
            if hasattr(seq_editor, "strips"):
                seq_editor.strips.new_sound(
                    name="BB_Audio",
                    filepath=filepath,
                    channel=1,
                    frame_start=1,
                )
            elif hasattr(seq_editor, "sequences"):
                seq_editor.sequences.new_sound(
                    name="BB_Audio",
                    filepath=filepath,
                    channel=1,
                    frame_start=1,
                )

            # Enable audio scrubbing
            scene.use_audio_scrub = True
            scene.sync_mode = 'AUDIO_SYNC'

        except Exception as e:
            print(f"[BlenderBeat] Audio playback setup warning: {e}")


class BB_OT_ClearScene(bpy.types.Operator):
    """Remove all BlenderBeat objects from the scene"""
    bl_idname = "blenderbeat.clear_scene"
    bl_label = "Clear BlenderBeat"
    bl_description = "Remove all generated BlenderBeat objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .visual.geometry import clear_blenderbeat_objects
        clear_blenderbeat_objects()

        # Remove audio strips across Blender versions
        seq_editor = context.scene.sequence_editor
        if seq_editor:
            strip_list = getattr(seq_editor, "strips_all", None) or getattr(seq_editor, "sequences_all", None) or getattr(seq_editor, "sequences", [])
            for strip in list(strip_list):
                if strip.name.startswith("BB_Audio"):
                    if hasattr(seq_editor, "strips"):
                        seq_editor.strips.remove(strip)
                    elif hasattr(seq_editor, "sequences"):
                        seq_editor.sequences.remove(strip)

        # Reset properties
        context.scene.bb_visual.is_generated = False
        context.scene.bb_audio.is_analyzed = False

        self.report({'INFO'}, "BlenderBeat scene cleared")
        return {'FINISHED'}


class BB_OT_RenderAnimation(bpy.types.Operator):
    """Render the visualizer animation"""
    bl_idname = "blenderbeat.render_animation"
    bl_label = "Render Animation"
    bl_description = "Render the full loop animation"
    bl_options = {'REGISTER'}

    def execute(self, context):
        visual = context.scene.bb_visual
        render_props = context.scene.bb_render

        if not visual.is_generated:
            self.report({'ERROR'},
                "No visual generated. Generate a visual first.")
            return {'CANCELLED'}

        # Apply render settings
        from .visual.lighting import setup_render_settings
        setup_render_settings(
            resolution_x=render_props.resolution_x,
            resolution_y=render_props.resolution_y,
            fps=render_props.fps,
            renderer=render_props.renderer,
            output_path=render_props.output_path,
        )

        # Start render
        bpy.ops.render.render('INVOKE_DEFAULT', animation=True)

        self.report({'INFO'}, "Rendering started...")
        return {'FINISHED'}


class BB_OT_InstallDependencies(bpy.types.Operator):
    """Install optional dependencies (scipy)"""
    bl_idname = "blenderbeat.install_deps"
    bl_label = "Install Dependencies"
    bl_description = "Install scipy for enhanced audio analysis"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .utils.dependencies import ensure_scipy
        success, msg = ensure_scipy()
        if success:
            self.report({'INFO'}, msg)
        else:
            self.report({'WARNING'}, msg)
        return {'FINISHED'}


# Module-level analysis cache
_analysis_cache: dict = {}


# All operator classes to register
OPERATOR_CLASSES = [
    BB_OT_ImportAudio,
    BB_OT_AnalyzeAudio,
    BB_OT_GenerateVisual,
    BB_OT_ClearScene,
    BB_OT_RenderAnimation,
    BB_OT_InstallDependencies,
]


def register_operators():
    """Register all operators."""
    for cls in OPERATOR_CLASSES:
        bpy.utils.register_class(cls)


def unregister_operators():
    """Unregister all operators."""
    for cls in reversed(OPERATOR_CLASSES):
        bpy.utils.unregister_class(cls)
