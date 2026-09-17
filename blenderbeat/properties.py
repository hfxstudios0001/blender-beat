"""
BlenderBeat — Property definitions.

Defines all Blender PropertyGroups that store addon state:
audio settings, visual settings, loop settings, render settings.
"""

import bpy
from bpy.props import (
    StringProperty,
    FloatProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
    FloatVectorProperty,
)


class BB_AudioProperties(bpy.types.PropertyGroup):
    """Audio file and analysis settings."""

    filepath: StringProperty(
        name="Audio File",
        description="Path to the audio file (WAV, MP3, FLAC, OGG)",
        subtype='FILE_PATH',
        default="",
    )

    bpm_override: FloatProperty(
        name="BPM Override",
        description="Manual BPM override (0 = auto-detect)",
        default=0.0,
        min=0.0,
        max=300.0,
        step=100,
    )

    detected_bpm: FloatProperty(
        name="Detected BPM",
        description="BPM detected by analysis",
        default=0.0,
    )

    duration: FloatProperty(
        name="Duration",
        description="Audio duration in seconds",
        default=0.0,
    )

    sample_rate: IntProperty(
        name="Sample Rate",
        description="Audio sample rate",
        default=0,
    )

    is_analyzed: BoolProperty(
        name="Is Analyzed",
        description="Whether the audio has been analyzed",
        default=False,
    )

    analysis_resolution: EnumProperty(
        name="Analysis Resolution",
        description="Analysis detail level",
        items=[
            ('LOW', "Low", "Faster analysis, less detail (hop=1024)"),
            ('MEDIUM', "Medium", "Balanced (hop=512)"),
            ('HIGH', "High", "Most detail, slower (hop=256)"),
        ],
        default='MEDIUM',
    )

    beat_count: IntProperty(
        name="Beat Count",
        description="Number of detected beats",
        default=0,
    )

    n_frames: IntProperty(
        name="Analysis Frames",
        description="Number of analysis frames",
        default=0,
    )


class BB_VisualProperties(bpy.types.PropertyGroup):
    """Visual generation settings."""

    preset: EnumProperty(
        name="Preset",
        description="Visual preset to use",
        items=[
            ('NEON_SIGNAL_CITY', "Neon Signal City", "Futuristic cyberpunk skyscraper corridor with vertical LED light columns, wet reflective ground, and kick depth wave propagation"),
            ('COSMIC_BLOSSOM', "Cosmic Blossom", "Multilayered alien cosmic flower organism with energy wave propagation and reflective temple environment"),
            ('INFINITE_BLACK_HOLE_TUNNEL', "Infinite Black Hole Tunnel", "Gigantic mechanical corridor with amber LED pulse rings leading to a black hole"),
            ('INFINITE_LIGHT_GRID', "Infinite Light Grid", "Deep square-framed LED tunnel with mechanical joints and audio-reactive light propagation"),
            ('QUANTUM_FIELD', "Quantum Field", "High-density organic particle waves (Eduard OV style)"),
            ('AUDIO_SPHERE', "Audio Sphere", "Radial bars on an icosphere"),
        ],
        default='NEON_SIGNAL_CITY',
    )

    complexity: FloatProperty(
        name="Complexity",
        description="Visual complexity (affects polygon count and detail)",
        default=0.5,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )

    density: FloatProperty(
        name="Density",
        description="Object/instance density",
        default=0.5,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )

    seed: IntProperty(
        name="Random Seed",
        description="Seed for deterministic randomization",
        default=42,
        min=0,
        max=999999,
    )

    sphere_radius: FloatProperty(
        name="Sphere Radius",
        description="Base sphere radius",
        default=2.0,
        min=0.5,
        max=20.0,
    )

    bar_max_length: FloatProperty(
        name="Bar Length",
        description="Maximum bar extension length",
        default=2.0,
        min=0.1,
        max=10.0,
    )

    tunnel_ring_count: IntProperty(
        name="Tunnel Rings",
        description="Number of concentric corridor rings",
        default=45,
        min=15,
        max=120,
    )

    tunnel_radius: FloatProperty(
        name="Corridor Radius",
        description="Radius of the mechanical tunnel corridor",
        default=3.5,
        min=1.5,
        max=10.0,
    )

    tunnel_color_mode: EnumProperty(
        name="Aura Sync Mode",
        description="Aura Sync lighting color effect",
        items=[
            ('SPECTRUM', "Rainbow Spectrum", "Flowing rainbow chromatic wave along rings"),
            ('RED', "Cyberpunk Red", "Intense aggressive crimson red"),
            ('CYAN', "Electric Cyan", "Vibrant futuristic Tron/cyber cyan"),
            ('VIOLET', "Laser Violet", "Deep neon synthwave purple/violet"),
            ('AMBER', "Amber Gold", "Warm industrial gold/amber LED"),
            ('WHITE', "Arctic White", "Clean hyper-bright diamond white"),
            ('CUSTOM', "Custom Color", "User selected color"),
        ],
        default='SPECTRUM',
    )

    tunnel_custom_color: FloatVectorProperty(
        name="Custom Neon Color",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(0.0, 0.8, 1.0),
    )

    tunnel_glow_min: FloatProperty(
        name="Resting Opacity",
        description="Minimum dimness/opacity of rings when quiet (0 = completely dark)",
        default=0.02,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )

    tunnel_glow_max: FloatProperty(
        name="Peak Glow",
        description="Peak emission brightness on beat hits",
        default=35.0,
        min=2.0,
        max=100.0,
    )

    tunnel_enable_debris: BoolProperty(
        name="Enable Floating Debris",
        description="Toggle suspended space rocks inside corridor (off for clean view)",
        default=False,
    )

    # ── Cosmic Blossom Parameters ─────────────────────────────────────
    blossom_outer_petals: IntProperty(
        name="Outer Petals",
        description="Number of petals on the outermost hero layer",
        default=14,
        min=6,
        max=24,
    )

    blossom_open_factor: FloatProperty(
        name="Bloom Openness",
        description="Resting flare/open factor of the flower petals",
        default=0.45,
        min=0.1,
        max=1.0,
        subtype='FACTOR',
    )

    blossom_core_energy: FloatProperty(
        name="Core Energy",
        description="Emission intensity of central energy core",
        default=40.0,
        min=5.0,
        max=150.0,
    )

    blossom_shard_count: IntProperty(
        name="Floating Shards",
        description="Number of orbiting crystalline diamond shards",
        default=45,
        min=0,
        max=200,
    )

    blossom_color_palette: EnumProperty(
        name="Blossom Palette",
        description="Aesthetic theme for the cosmic blossom organism",
        items=[
            ('CELESTIAL_GOLD', "Celestial Gold & Crystal", "Warm gold chassis, translucent crystal, white-hot core"),
            ('CYBER_CYAN', "Cyberpunk Cyan & Diamond", "Electric cyan reflections, deep obsidian metal"),
            ('AMETHYST_VOID', "Amethyst & Obsidian", "Deep royal purple, hot magenta veins, dark void metal"),
            ('SOLAR_CRIMSON', "Solar Flare Crimson", "Intense fiery red-orange, gold trim, solar white core"),
            ('ARCTIC_DIAMOND', "Arctic Diamond & Chrome", "Pure icy blue-white, mirror chrome, diamond facets"),
        ],
        default='CELESTIAL_GOLD',
    )

    blossom_water_reflections: BoolProperty(
        name="Mirror Platform",
        description="Enable reflective temple water/obsidian platform below blossom",
        default=True,
    )

    # ── Infinite Light Grid Parameters ──────────────────────────────────
    grid_frame_count: IntProperty(
        name="Grid Frames",
        description="Number of square frames in the tunnel corridor",
        default=35,
        min=10,
        max=80,
    )

    grid_frame_size: FloatProperty(
        name="Frame Size",
        description="Side length of each square frame in meters",
        default=3.0,
        min=1.0,
        max=8.0,
    )

    grid_twist_amount: FloatProperty(
        name="Twist Per Frame",
        description="Z-rotation increment per frame (creates spiral perspective)",
        default=0.05,
        min=0.0,
        max=0.3,
        subtype='FACTOR',
    )

    variation: FloatProperty(
        name="Variation",
        description="Per-instance random variation amount",
        default=0.3,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )

    is_generated: BoolProperty(
        name="Is Generated",
        description="Whether a visual has been generated",
        default=False,
    )


class BB_LoopProperties(bpy.types.PropertyGroup):
    """Seamless loop settings."""

    full_song: BoolProperty(
        name="Full Song",
        description="Cover the entire duration of the audio track instead of a short bar loop",
        default=False,
    )

    loop_bars: IntProperty(
        name="Loop Bars",
        description="Number of musical bars in the loop",
        default=8,
        min=1,
        max=128,
    )

    beats_per_bar: IntProperty(
        name="Beats Per Bar",
        description="Beats per bar (time signature numerator)",
        default=4,
        min=2,
        max=8,
    )

    loop_frames: IntProperty(
        name="Loop Frames",
        description="Calculated total frames in the loop",
        default=0,
    )

    loop_duration: FloatProperty(
        name="Loop Duration",
        description="Calculated loop duration in seconds",
        default=0.0,
    )


class BB_RenderProperties(bpy.types.PropertyGroup):
    """Render output settings."""

    renderer: EnumProperty(
        name="Renderer",
        description="Render engine",
        items=[
            ('BLENDER_EEVEE', "Eevee", "Fast real-time renderer"),
            ('CYCLES', "Cycles", "Path-traced renderer (slower, higher quality)"),
        ],
        default='BLENDER_EEVEE',
    )

    resolution_x: IntProperty(
        name="Width",
        description="Render width in pixels",
        default=1920,
        min=64,
        max=7680,
    )

    resolution_y: IntProperty(
        name="Height",
        description="Render height in pixels",
        default=1080,
        min=64,
        max=4320,
    )

    fps: IntProperty(
        name="FPS",
        description="Frames per second",
        default=30,
        min=1,
        max=120,
    )

    output_path: StringProperty(
        name="Output Path",
        description="Render output directory",
        subtype='DIR_PATH',
        default="//render/",
    )


class BB_CameraProperties(bpy.types.PropertyGroup):
    """Camera settings."""

    mode: EnumProperty(
        name="Camera Mode",
        description="Camera movement mode",
        items=[
            ('ORBIT', "Orbit", "Smooth orbit around the subject"),
            ('STATIC', "Static", "Fixed camera position"),
        ],
        default='ORBIT',
    )

    orbit_speed: FloatProperty(
        name="Orbit Speed",
        description="Camera orbit speed (orbits per loop)",
        default=1.0,
        min=0.0,
        max=4.0,
    )

    distance: FloatProperty(
        name="Distance",
        description="Camera distance from center",
        default=8.0,
        min=2.0,
        max=50.0,
    )

    height: FloatProperty(
        name="Height",
        description="Camera height",
        default=3.0,
        min=-10.0,
        max=20.0,
    )

    shake_intensity: FloatProperty(
        name="Shake Intensity",
        description="Beat-reactive camera shake intensity",
        default=0.5,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )

    fov: FloatProperty(
        name="FOV",
        description="Field of view in degrees",
        default=50.0,
        min=10.0,
        max=120.0,
    )


# All property classes to register
PROPERTY_CLASSES = [
    BB_AudioProperties,
    BB_VisualProperties,
    BB_LoopProperties,
    BB_RenderProperties,
    BB_CameraProperties,
]


def register_properties():
    """Register all property groups."""
    for cls in PROPERTY_CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.bb_audio = bpy.props.PointerProperty(type=BB_AudioProperties)
    bpy.types.Scene.bb_visual = bpy.props.PointerProperty(type=BB_VisualProperties)
    bpy.types.Scene.bb_loop = bpy.props.PointerProperty(type=BB_LoopProperties)
    bpy.types.Scene.bb_render = bpy.props.PointerProperty(type=BB_RenderProperties)
    bpy.types.Scene.bb_camera = bpy.props.PointerProperty(type=BB_CameraProperties)


def unregister_properties():
    """Unregister all property groups."""
    del bpy.types.Scene.bb_camera
    del bpy.types.Scene.bb_render
    del bpy.types.Scene.bb_loop
    del bpy.types.Scene.bb_visual
    del bpy.types.Scene.bb_audio

    for cls in reversed(PROPERTY_CLASSES):
        bpy.utils.unregister_class(cls)
