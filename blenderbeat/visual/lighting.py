"""
BlenderBeat — Lighting system.

Creates dramatic, cinematic lighting setups with
audio-reactive intensity. Designed for both Eevee and Cycles.
"""

import bpy
import math
from typing import Optional, Tuple

from ..animation.baking import get_prop_name


def create_lighting_setup(
    key_color: Tuple[float, float, float] = (0.6, 0.8, 1.0),
    fill_color: Tuple[float, float, float] = (0.2, 0.1, 0.4),
    rim_color: Tuple[float, float, float] = (1.0, 0.3, 0.1),
    key_intensity: float = 500.0,
    fill_intensity: float = 100.0,
    rim_intensity: float = 300.0,
) -> dict:
    """
    Create a cinematic 3-point lighting setup.

    - Key light: Main illumination, audio-reactive
    - Fill light: Soft fill from opposite side
    - Rim light: Back-light for edge definition

    Returns dict of {name: light_object}.
    """
    lights = {}

    # Remove existing BB lights
    for obj in list(bpy.data.objects):
        if obj.name.startswith("BB_Light_"):
            bpy.data.objects.remove(obj, do_unlink=True)

    # Key Light — main, positioned high and to the side
    key = _create_light(
        name="BB_Light_Key",
        light_type='AREA',
        color=key_color,
        energy=key_intensity,
        location=(5, -3, 6),
        rotation=(math.radians(45), 0, math.radians(30)),
        size=3.0,
    )
    lights["key"] = key

    # Fill Light — softer, opposite side
    fill = _create_light(
        name="BB_Light_Fill",
        light_type='AREA',
        color=fill_color,
        energy=fill_intensity,
        location=(-4, 2, 3),
        rotation=(math.radians(60), 0, math.radians(-45)),
        size=5.0,
    )
    lights["fill"] = fill

    # Rim Light — behind the subject
    rim = _create_light(
        name="BB_Light_Rim",
        light_type='POINT',
        color=rim_color,
        energy=rim_intensity,
        location=(0, 5, 4),
        rotation=(0, 0, 0),
        size=1.0,
    )
    lights["rim"] = rim

    print(f"[BlenderBeat] Lighting: 3-point setup created")
    return lights


def _create_light(
    name: str,
    light_type: str,
    color: Tuple[float, float, float],
    energy: float,
    location: Tuple[float, float, float],
    rotation: Tuple[float, float, float],
    size: float = 1.0,
) -> bpy.types.Object:
    """Create a single light."""
    # Remove existing
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    # Create light data
    light_data = bpy.data.lights.new(name=name, type=light_type)
    light_data.color = color
    light_data.energy = energy

    if light_type == 'AREA':
        light_data.size = size

    if light_type in ('POINT', 'SPOT'):
        light_data.shadow_soft_size = size

    # Enable contact shadows for Eevee
    try:
        light_data.use_contact_shadow = True
    except AttributeError:
        pass

    # Create object
    light_obj = bpy.data.objects.new(name, light_data)
    light_obj.location = location
    light_obj.rotation_euler = rotation
    bpy.context.collection.objects.link(light_obj)

    return light_obj


def setup_light_drivers(
    source_obj: bpy.types.Object,
    lights: dict,
    base_key_intensity: float = 500.0,
    max_key_intensity: float = 2000.0,
):
    """
    Set up audio-reactive drivers on lights.

    Key light intensity is driven by bb_light_intensity.
    """
    key_light = lights.get("key")
    if key_light is None:
        return

    prop_name = get_prop_name("light_intensity")
    if prop_name not in source_obj:
        return

    try:
        # Remove existing driver
        try:
            key_light.data.driver_remove("energy")
        except Exception:
            pass

        driver_fc = key_light.data.driver_add("energy")
        driver = driver_fc.driver
        driver.type = 'SCRIPTED'
        # Remap [0,1] → [base, max] intensity
        driver.expression = (
            f'{base_key_intensity} + var * {max_key_intensity - base_key_intensity}'
        )

        var = driver.variables.new()
        var.name = "var"
        var.type = 'SINGLE_PROP'
        var.targets[0].id = source_obj
        var.targets[0].data_path = f'["{prop_name}"]'

        print(f"[BlenderBeat] Light driver: {prop_name} → key intensity")

    except Exception as e:
        print(f"[BlenderBeat] Light driver failed: {e}")


def configure_eevee_rendering():
    """Configure Eevee render settings for optimal visualizer output."""
    scene = bpy.context.scene
    eevee = scene.eevee

    # Enable bloom for glow effect
    try:
        eevee.use_bloom = True
        eevee.bloom_threshold = 0.5
        eevee.bloom_intensity = 0.3
        eevee.bloom_radius = 6.0
    except AttributeError:
        # Blender 4.x may handle bloom differently (compositor)
        pass

    # Screen space reflections / Raytracing (Blender 4.x & 5.x EEVEE-Next)
    try:
        eevee.use_ssr = True
        eevee.use_ssr_refraction = True
    except AttributeError:
        pass

    try:
        eevee.use_raytracing = True
        eevee.ray_tracing_method = 'SCREEN'
        if hasattr(eevee, "ray_tracing_options"):
            rto = eevee.ray_tracing_options
            rto.screen_trace_quality = 0.5
            rto.screen_trace_thickness = 0.25
            rto.trace_max_roughness = 0.75
            rto.use_denoise = True
    except (AttributeError, TypeError):
        pass

    # Ambient occlusion
    try:
        eevee.use_gtao = True
    except AttributeError:
        pass

    # Shadows
    try:
        eevee.shadow_cube_size = '1024'
        eevee.shadow_cascade_size = '2048'
    except (AttributeError, TypeError):
        pass

    # Volumetrics
    try:
        eevee.use_volumetric_lights = True
        eevee.volumetric_tile_size = '4'
    except (AttributeError, TypeError):
        pass

    # Samples
    try:
        eevee.taa_render_samples = 64
        eevee.taa_samples = 16
    except AttributeError:
        pass

    # Ensure background is pitch-black for high contrast sci-fi corridor
    try:
        world = scene.world
        if world and world.use_nodes:
            bg = world.node_tree.nodes.get("Background")
            if bg:
                bg.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
                bg.inputs["Strength"].default_value = 0.0
    except Exception:
        pass


def setup_realtime_glow_compositor():
    """
    Configure real-time Fog Glow bloom in the Blender 5.2 Compositor.
    Creates a CompositorNodeTree assigned to scene.compositing_node_group
    and enables viewport compositor in 'ALWAYS' mode for rendered views.
    """
    scene = bpy.context.scene

    # Blender 5.2 Compositor Node Tree
    c_tree = bpy.data.node_groups.get("BB_CompositorNodes")
    if not c_tree:
        c_tree = bpy.data.node_groups.new(name="BB_CompositorNodes", type="CompositorNodeTree")

    scene.compositing_node_group = c_tree
    c_tree.nodes.clear()

    rl = c_tree.nodes.new("CompositorNodeRLayers")
    rl.location = (-300, 200)

    glare = c_tree.nodes.new("CompositorNodeGlare")
    glare.name = "Glare"
    glare.location = (0, 200)
    try:
        glare.inputs["Type"].default_value = "Fog Glow"
    except Exception:
        try:
            glare.glare_type = "FOG_GLOW"
        except Exception:
            pass

    try:
        glare.inputs["Quality"].default_value = "High"
    except Exception:
        pass

    if "Threshold" in glare.inputs:
        glare.inputs["Threshold"].default_value = 0.65
    if "Saturation" in glare.inputs:
        glare.inputs["Saturation"].default_value = 1.2
    if "Strength" in glare.inputs:
        glare.inputs["Strength"].default_value = 0.7
    if "Size" in glare.inputs:
        glare.inputs["Size"].default_value = 0.95
    if "Tint" in glare.inputs:
        glare.inputs["Tint"].default_value = (1.0, 1.0, 1.0, 1.0)  # Neutral tint for multi-color Aura Sync

    out_node = c_tree.nodes.new("NodeGroupOutput")
    out_node.location = (300, 200)

    # Ensure output socket exists
    has_img_socket = any(s.name == "Image" and s.in_out == "OUTPUT" for s in c_tree.interface.items_tree)
    if not has_img_socket:
        c_tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")

    c_tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
    c_tree.links.new(glare.outputs["Image"], out_node.inputs["Image"])

    # Enable real-time compositing in 3D viewports
    try:
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.shading.type = 'RENDERED'
                            space.shading.use_compositor = 'ALWAYS'
    except Exception:
        pass

    print("[BlenderBeat] Compositor Fog Glow pipeline configured successfully.")


def configure_cycles_rendering():
    """Configure Cycles render settings for quality output."""
    scene = bpy.context.scene

    scene.render.engine = 'CYCLES'

    cycles = scene.cycles
    cycles.samples = 128
    cycles.use_denoising = True
    cycles.use_adaptive_sampling = True

    # Try to use GPU
    try:
        cycles.device = 'GPU'
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA'  # or 'OPTIX', 'HIP', 'METAL'
        for device in prefs.devices:
            device.use = True
    except Exception:
        cycles.device = 'CPU'


def setup_render_settings(
    resolution_x: int = 1920,
    resolution_y: int = 1080,
    fps: int = 30,
    renderer: str = 'BLENDER_EEVEE',
    output_path: str = "//render/",
):
    """
    Configure render output settings.

    Args:
        resolution_x: Output width.
        resolution_y: Output height.
        fps: Frames per second.
        renderer: 'BLENDER_EEVEE' or 'CYCLES'.
        output_path: Output directory (// = relative to blend file).
    """
    scene = bpy.context.scene
    render = scene.render

    render.resolution_x = resolution_x
    render.resolution_y = resolution_y
    render.fps = fps
    render.image_settings.file_format = 'PNG'
    render.filepath = output_path

    # Set renderer
    try:
        render.engine = renderer
    except Exception:
        # Fallback for older Blender
        if 'EEVEE' in renderer:
            render.engine = 'BLENDER_EEVEE'
        else:
            render.engine = 'CYCLES'

    # Apply renderer-specific settings
    if 'EEVEE' in render.engine:
        configure_eevee_rendering()
    elif render.engine == 'CYCLES':
        configure_cycles_rendering()

    # Color management
    try:
        scene.view_settings.view_transform = 'AgX'
    except TypeError:
        try:
            scene.view_settings.view_transform = 'Filmic'
        except TypeError:
            pass

    scene.view_settings.look = 'None'

    print(f"[BlenderBeat] Render: {resolution_x}×{resolution_y} @ {fps}fps, "
          f"engine={render.engine}")
