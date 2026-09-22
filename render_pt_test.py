import bpy
import sys

# Test render Pulse Tunnel camera view
from blenderbeat.presets.pulse_tunnel.tunnel_materials import create_pulse_tunnel_materials
from blenderbeat.presets.pulse_tunnel.tunnel_ring import create_master_ring_mesh
from blenderbeat.presets.pulse_tunnel.tunnel_nodes import create_pulse_tunnel_geometry_nodes
from blenderbeat.presets.pulse_tunnel.tunnel_camera import setup_pulse_tunnel_camera
from blenderbeat.presets.pulse_tunnel.tunnel_lighting import setup_pulse_tunnel_lighting
from blenderbeat.visual.geometry import create_visualizer_object

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

col = bpy.data.collections.new("BB_PulseTunnel_Test")
bpy.context.scene.collection.children.link(col)

mats = create_pulse_tunnel_materials(
    palette_name='CYBER_CYAN_MAGENTA',
    glow_intensity=35.0,
    resting_glow=0.0,
)

ring_obj = create_master_ring_mesh(
    name="BB_PT_MasterRing",
    outer_radius=8.0,
    segments_per_zone=32,
    mat_hull=mats["hull"],
    mat_led=mats["led_primary"],
    mat_glow=mats["led_accent"],
)
col.objects.link(ring_obj)

viz_obj = create_visualizer_object("BB_Visualizer")
col.objects.link(viz_obj)
viz_obj.data.materials.clear()
for mat in ring_obj.data.materials:
    viz_obj.data.materials.append(mat)

node_tree = create_pulse_tunnel_geometry_nodes(
    viz_obj=viz_obj,
    ring_obj=ring_obj,
    ring_count=80,
    spacing=1.8,
)

cam = setup_pulse_tunnel_camera(
    tunnel_depth=80 * 1.8,
    camera_z_start=1.5,
    total_frames=300,
    lens_mm=20.0,
    collection=col,
)

setup_pulse_tunnel_lighting(
    collection=col,
    tunnel_depth=80 * 1.8,
    haze_density=0.0,
    bloom_threshold=0.65,
    bloom_size=0.95,
)

# Connect drivers or set test values
viz_obj["bb_scale"] = 0.85
viz_obj["bb_rotation_z"] = 0.5
viz_obj["bb_emission_strength"] = 0.8

# Manual shader value test
led_mat = mats["led_primary"]
for n in led_mat.node_tree.nodes:
    if n.name == "BB_PT_KickVal":
        n.outputs[0].default_value = 0.85
    elif n.name == "BB_PT_EnergyVal":
        n.outputs[0].default_value = 0.8

# Render frame 1 to scratch
bpy.context.scene.camera = cam
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.filepath = r"C:\Users\itsha\.gemini\antigravity-ide\brain\65e4e8a5-8fd6-447a-be01-eeb0baec2d14\scratch\pulse_tunnel_verify_render.png"

bpy.ops.render.render(write_still=True)
print("RENDER FINISHED SUCCESSFULLY!")
