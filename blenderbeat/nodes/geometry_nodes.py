"""
BlenderBeat — Geometry Nodes tree builders.

Programmatically constructs Geometry Node trees for
procedural visualizers. Phase 1: Audio Sphere — an icosphere
with radial bars instanced on each vertex, driven by audio.
"""

import bpy
import math
from typing import Tuple, Optional


def _clear_node_tree(node_tree: bpy.types.NodeTree):
    """Remove all nodes from a node tree."""
    for node in list(node_tree.nodes):
        node_tree.nodes.remove(node)


def _link(node_tree, from_socket, to_socket):
    """Create a node link."""
    node_tree.links.new(from_socket, to_socket)


def create_audio_sphere_nodes(
    obj: bpy.types.Object,
    bar_count: int = 64,
    subdivisions: int = 3,
    material: Optional[bpy.types.Material] = None,
) -> bpy.types.NodeTree:
    """
    Create the Audio Sphere Geometry Nodes setup.

    Architecture:
        Ico Sphere (subdivided)
        → Instance cube bars on each vertex
        → Scale bars along vertex normal by audio data
        → Individual variation via noise

    The key audio-driven inputs:
        - bb_scale: Controls bar extension (bass)
        - bb_rotation_z: Controls global rotation (treble)
        - bb_displacement: Controls vertex displacement

    Args:
        obj: The object to apply the GN modifier to.
        bar_count: Approximate number of radial bars.
        subdivisions: Icosphere subdivision level (controls density).

    Returns:
        The created NodeTree.
    """
    # Create or get the node group
    tree_name = "BB_AudioSphere"
    if tree_name in bpy.data.node_groups:
        node_tree = bpy.data.node_groups[tree_name]
        _clear_node_tree(node_tree)
    else:
        node_tree = bpy.data.node_groups.new(tree_name, 'GeometryNodeTree')

    nodes = node_tree.nodes
    links = node_tree.links

    # --- Create Interface (Inputs/Outputs) ---
    # Clear existing interface items
    for item in list(node_tree.interface.items_tree):
        if item.item_type in {'SOCKET'}:
            node_tree.interface.remove(item)

    # Output socket
    node_tree.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry',
    )

    # Input socket: Geometry
    node_tree.interface.new_socket(
        name="Geometry",
        in_out='INPUT',
        socket_type='NodeSocketGeometry',
    )

    # Input: Scale (driven by bass)
    scale_input = node_tree.interface.new_socket(
        name="Audio Scale",
        in_out='INPUT',
        socket_type='NodeSocketFloat',
    )
    scale_input.default_value = 0.5
    scale_input.min_value = 0.0
    scale_input.max_value = 2.0

    # Input: Rotation (driven by treble)
    rotation_input = node_tree.interface.new_socket(
        name="Audio Rotation",
        in_out='INPUT',
        socket_type='NodeSocketFloat',
    )
    rotation_input.default_value = 0.0
    rotation_input.min_value = 0.0
    rotation_input.max_value = 1.0

    # Input: Bar Base Scale
    bar_scale_input = node_tree.interface.new_socket(
        name="Bar Base Scale",
        in_out='INPUT',
        socket_type='NodeSocketFloat',
    )
    bar_scale_input.default_value = 0.03
    bar_scale_input.min_value = 0.001
    bar_scale_input.max_value = 0.5

    # Input: Bar Length
    bar_length_input = node_tree.interface.new_socket(
        name="Bar Max Length",
        in_out='INPUT',
        socket_type='NodeSocketFloat',
    )
    bar_length_input.default_value = 2.0
    bar_length_input.min_value = 0.1
    bar_length_input.max_value = 10.0

    # Input: Sphere Radius
    radius_input = node_tree.interface.new_socket(
        name="Sphere Radius",
        in_out='INPUT',
        socket_type='NodeSocketFloat',
    )
    radius_input.default_value = 2.0
    radius_input.min_value = 0.5
    radius_input.max_value = 20.0

    # Input: Variation
    variation_input = node_tree.interface.new_socket(
        name="Variation",
        in_out='INPUT',
        socket_type='NodeSocketFloat',
    )
    variation_input.default_value = 0.3
    variation_input.min_value = 0.0
    variation_input.max_value = 1.0

    # Input: Beat Glow (Polyfjord stochastic trigger)
    glow_input = node_tree.interface.new_socket(
        name="Beat Glow",
        in_out='INPUT',
        socket_type='NodeSocketFloat',
    )
    glow_input.default_value = 0.0
    glow_input.min_value = 0.0
    glow_input.max_value = 2.0

    # --- Create Nodes ---

    # Group Input
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1400, 0)

    # Group Output
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1200, 0)

    # 1. Ico Sphere mesh
    ico = nodes.new('GeometryNodeMeshIcoSphere')
    ico.location = (-1000, 200)
    ico.inputs['Radius'].default_value = 1.0
    ico.inputs['Subdivisions'].default_value = subdivisions

    # 2. Scale the sphere by the radius input
    transform_sphere = nodes.new('GeometryNodeTransform')
    transform_sphere.location = (-800, 200)
    _link(node_tree, ico.outputs['Mesh'], transform_sphere.inputs['Geometry'])

    # Combine XYZ for uniform scale from radius
    combine_radius = nodes.new('ShaderNodeCombineXYZ')
    combine_radius.location = (-1000, 0)
    _link(node_tree, input_node.outputs['Sphere Radius'], combine_radius.inputs['X'])
    _link(node_tree, input_node.outputs['Sphere Radius'], combine_radius.inputs['Y'])
    _link(node_tree, input_node.outputs['Sphere Radius'], combine_radius.inputs['Z'])
    _link(node_tree, combine_radius.outputs['Vector'], transform_sphere.inputs['Scale'])

    # 3. Mesh to Points — get vertex positions for instancing
    mesh_to_points = nodes.new('GeometryNodeMeshToPoints')
    mesh_to_points.location = (-600, 200)
    _link(node_tree, transform_sphere.outputs['Geometry'],
          mesh_to_points.inputs['Mesh'])

    # 4. Create the bar instance (thin cube)
    bar_cube = nodes.new('GeometryNodeMeshCube')
    bar_cube.location = (-600, -200)
    bar_cube.inputs['Size'].default_value = (1.0, 1.0, 1.0)

    # 5. Noise Texture for per-point variation
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-400, -100)
    noise.inputs['Scale'].default_value = 2.0

    # Position for noise input
    position_node = nodes.new('GeometryNodeInputPosition')
    position_node.location = (-600, -100)
    _link(node_tree, position_node.outputs['Position'], noise.inputs['Vector'])

    # Internal driver Value node for Audio Scale
    scale_val_node = nodes.new('ShaderNodeValue')
    scale_val_node.location = (-400, 100)
    scale_val_node.name = "BB_InternalAudioScale"
    scale_val_node.label = "Audio Scale (Driven)"

    # 6. Math: Audio Scale × Bar Max Length + variation
    # audio_scale * bar_length * (1 + noise * variation)

    # Multiply audio scale by bar max length
    scale_multiply = nodes.new('ShaderNodeMath')
    scale_multiply.location = (-200, 100)
    scale_multiply.operation = 'MULTIPLY'
    _link(node_tree, scale_val_node.outputs[0],
          scale_multiply.inputs[0])
    _link(node_tree, input_node.outputs['Bar Max Length'],
          scale_multiply.inputs[1])

    # Multiply noise by variation amount
    noise_var = nodes.new('ShaderNodeMath')
    noise_var.location = (-200, -100)
    noise_var.operation = 'MULTIPLY'
    _link(node_tree, noise.outputs['Fac'], noise_var.inputs[0])
    _link(node_tree, input_node.outputs['Variation'], noise_var.inputs[1])

    # Add 1 to get multiplier (1 + noise*variation)
    noise_add = nodes.new('ShaderNodeMath')
    noise_add.location = (0, -100)
    noise_add.operation = 'ADD'
    noise_add.inputs[0].default_value = 1.0
    _link(node_tree, noise_var.outputs['Value'], noise_add.inputs[1])

    # Final scale = audio_scale * bar_length * (1 + noise*variation)
    final_scale = nodes.new('ShaderNodeMath')
    final_scale.location = (200, 0)
    final_scale.operation = 'MULTIPLY'
    _link(node_tree, scale_multiply.outputs['Value'], final_scale.inputs[0])
    _link(node_tree, noise_add.outputs['Value'], final_scale.inputs[1])

    # Clamp minimum so bars are always visible
    scale_max = nodes.new('ShaderNodeMath')
    scale_max.location = (400, 0)
    scale_max.operation = 'MAXIMUM'
    scale_max.inputs[1].default_value = 0.1
    _link(node_tree, final_scale.outputs['Value'], scale_max.inputs[0])

    # --- Polyfjord Stochastic Random Glowing Bars Engine ---
    # 7a. Random float per point (seed 42, min 0, max 1) with Index connected to ID
    index_node = nodes.new('GeometryNodeInputIndex')
    index_node.location = (0, 350)

    random_val = nodes.new('FunctionNodeRandomValue')
    random_val.location = (200, 350)
    random_val.data_type = 'FLOAT'
    random_val.inputs['Min'].default_value = 0.0
    random_val.inputs['Max'].default_value = 1.0
    _link(node_tree, index_node.outputs['Index'], random_val.inputs['ID'])

    # Internal driver Value node for Beat Glow
    glow_val_node = nodes.new('ShaderNodeValue')
    glow_val_node.location = (-200, 500)
    glow_val_node.name = "BB_InternalBeatGlow"
    glow_val_node.label = "Beat Glow (Driven)"

    # 7b. Dynamic activation threshold: threshold drops as Beat Glow rises
    # threshold = 0.95 - (Beat Glow * 0.45)
    thresh_scale = nodes.new('ShaderNodeMath')
    thresh_scale.location = (0, 500)
    thresh_scale.operation = 'MULTIPLY'
    thresh_scale.inputs[1].default_value = 0.45
    _link(node_tree, glow_val_node.outputs[0], thresh_scale.inputs[0])

    sub_thresh = nodes.new('ShaderNodeMath')
    sub_thresh.location = (200, 500)
    sub_thresh.operation = 'SUBTRACT'
    sub_thresh.inputs[0].default_value = 0.95
    _link(node_tree, thresh_scale.outputs['Value'], sub_thresh.inputs[1])

    # 7c. Compare: RandomVal > Threshold -> Glow Active (1.0 or 0.0)
    compare_glow = nodes.new('FunctionNodeCompare')
    compare_glow.location = (400, 400)
    compare_glow.data_type = 'FLOAT'
    compare_glow.operation = 'GREATER_THAN'
    _link(node_tree, random_val.outputs['Value'], compare_glow.inputs['A'])
    _link(node_tree, sub_thresh.outputs['Value'], compare_glow.inputs['B'])

    # Multiply glow mask by Beat Glow to get continuous intensity
    glow_intensity = nodes.new('ShaderNodeMath')
    glow_intensity.location = (600, 400)
    glow_intensity.operation = 'MULTIPLY'
    _link(node_tree, compare_glow.outputs['Result'], glow_intensity.inputs[0])
    _link(node_tree, glow_val_node.outputs[0], glow_intensity.inputs[1])

    # 7d. Store 'bb_glow' attribute on points before instancing
    store_attr = nodes.new('GeometryNodeStoreNamedAttribute')
    store_attr.location = (600, 200)
    store_attr.data_type = 'FLOAT'
    store_attr.domain = 'POINT'
    store_attr.inputs['Name'].default_value = "bb_glow"
    _link(node_tree, mesh_to_points.outputs['Points'], store_attr.inputs['Geometry'])
    _link(node_tree, glow_intensity.outputs['Value'], store_attr.inputs['Value'])

    # 7e. Scale boost for active glowing bars: Z scale * (1.0 + glow * 0.8)
    glow_scale_add = nodes.new('ShaderNodeMath')
    glow_scale_add.location = (600, -100)
    glow_scale_add.operation = 'MULTIPLY_ADD'
    glow_scale_add.inputs[1].default_value = 0.8
    _link(node_tree, glow_intensity.outputs['Value'], glow_scale_add.inputs[0])
    _link(node_tree, scale_max.outputs['Value'], glow_scale_add.inputs[2])

    # 7f. Build scale vector: bar_base for XY, computed length for Z
    combine_bar_scale = nodes.new('ShaderNodeCombineXYZ')
    combine_bar_scale.location = (750, 0)
    _link(node_tree, input_node.outputs['Bar Base Scale'],
          combine_bar_scale.inputs['X'])
    _link(node_tree, input_node.outputs['Bar Base Scale'],
          combine_bar_scale.inputs['Y'])
    _link(node_tree, glow_scale_add.outputs['Value'],
          combine_bar_scale.inputs['Z'])

    # 8. Instance on Points
    instance_on_points = nodes.new('GeometryNodeInstanceOnPoints')
    instance_on_points.location = (950, 200)
    _link(node_tree, store_attr.outputs['Geometry'],
          instance_on_points.inputs['Points'])
    _link(node_tree, bar_cube.outputs['Mesh'],
          instance_on_points.inputs['Instance'])
    _link(node_tree, combine_bar_scale.outputs['Vector'],
          instance_on_points.inputs['Scale'])

    # 9. Align instances to face outward from sphere center
    # Use Align Euler to Vector with the normal
    normal_node = nodes.new('GeometryNodeInputNormal')
    normal_node.location = (400, 300)

    align_euler = nodes.new('FunctionNodeAlignEulerToVector')
    align_euler.location = (600, 300)
    align_euler.axis = 'Z'  # Align bar's Z axis to the normal
    _link(node_tree, normal_node.outputs['Normal'],
          align_euler.inputs['Vector'])
    _link(node_tree, align_euler.outputs['Rotation'],
          instance_on_points.inputs['Rotation'])

    # Internal driver Value node for Audio Rotation
    rot_val_node = nodes.new('ShaderNodeValue')
    rot_val_node.location = (400, -200)
    rot_val_node.name = "BB_InternalAudioRotation"
    rot_val_node.label = "Audio Rotation (Driven)"

    # 10. Global rotation from audio
    # Convert Audio Rotation [0,1] → radians [0, 2π]
    rotation_to_rad = nodes.new('ShaderNodeMath')
    rotation_to_rad.location = (600, -200)
    rotation_to_rad.operation = 'MULTIPLY'
    _link(node_tree, rot_val_node.outputs[0],
          rotation_to_rad.inputs[0])
    rotation_to_rad.inputs[1].default_value = 2.0 * math.pi

    # Transform: rotate the whole thing
    global_rotate = nodes.new('GeometryNodeTransform')
    global_rotate.location = (1000, 200)
    _link(node_tree, instance_on_points.outputs['Instances'],
          global_rotate.inputs['Geometry'])

    # Build rotation vector (rotate around Z)
    combine_rotation = nodes.new('ShaderNodeCombineXYZ')
    combine_rotation.location = (800, -200)
    combine_rotation.inputs['X'].default_value = 0.0
    combine_rotation.inputs['Y'].default_value = 0.0
    _link(node_tree, rotation_to_rad.outputs['Value'],
          combine_rotation.inputs['Z'])
    _link(node_tree, combine_rotation.outputs['Vector'],
          global_rotate.inputs['Rotation'])

    # 11. Realize Instances to propagate per-point attributes into shader
    realize_instances = nodes.new('GeometryNodeRealizeInstances')
    realize_instances.location = (1150, 200)
    _link(node_tree, global_rotate.outputs['Geometry'],
          realize_instances.inputs['Geometry'])

    # 12. Assign Material if provided
    final_geo_socket = realize_instances.outputs['Geometry']
    if material:
        set_mat = nodes.new('GeometryNodeSetMaterial')
        set_mat.location = (1300, 200)
        set_mat.inputs['Material'].default_value = material
        _link(node_tree, realize_instances.outputs['Geometry'], set_mat.inputs['Geometry'])
        final_geo_socket = set_mat.outputs['Geometry']
        output_node.location = (1500, 0)

    # 13. Connect to output
    _link(node_tree, final_geo_socket, output_node.inputs['Geometry'])

    # --- Apply modifier to object ---
    _apply_gn_modifier(obj, node_tree)

    print(f"[BlenderBeat] Audio Sphere GN tree created: "
          f"{len(nodes)} nodes, subdivisions={subdivisions}")

    return node_tree


def create_quantum_field_nodes(
    obj: bpy.types.Object,
    density: float = 0.5,
    material: Optional[bpy.types.Material] = None,
) -> bpy.types.NodeTree:
    """
    Create the Eduard OV-inspired Organic Particle Wave Field Geometry Nodes setup.

    Architecture:
        High-Density Grid (e.g. 150x150 to 250x250 points)
        → Concentric harmonic ripple waves driven by Bass & Kick
        → Multi-octave 4D Noise displacement driven by Mids
        → Instanced micro-particles with audio-reactive size & luminous glow
        → Set Material with luminous point shader
    """
    tree_name = "BB_QuantumField"
    if tree_name in bpy.data.node_groups:
        node_tree = bpy.data.node_groups[tree_name]
        _clear_node_tree(node_tree)
    else:
        node_tree = bpy.data.node_groups.new(tree_name, 'GeometryNodeTree')

    nodes = node_tree.nodes
    links = node_tree.links

    # Clear existing interface
    for item in list(node_tree.interface.items_tree):
        if item.item_type in {'SOCKET'}:
            node_tree.interface.remove(item)

    # Output socket
    node_tree.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry',
    )

    # Inputs: Audio Bass (Ripples)
    sock_bass = node_tree.interface.new_socket(
        name="Audio Bass Wave",
        in_out='INPUT',
        socket_type='NodeSocketFloat',
    )
    sock_bass.default_value = 0.5
    sock_bass.min_value = 0.0
    sock_bass.max_value = 4.0

    # Inputs: Audio Treble (Sparkle / Noise)
    sock_treble = node_tree.interface.new_socket(
        name="Audio Treble Sparkle",
        in_out='INPUT',
        socket_type='NodeSocketFloat',
    )
    sock_treble.default_value = 0.3
    sock_treble.min_value = 0.0
    sock_treble.max_value = 2.0

    # Inputs: Audio Rotation
    sock_rot = node_tree.interface.new_socket(
        name="Audio Rotation",
        in_out='INPUT',
        socket_type='NodeSocketFloat',
    )
    sock_rot.default_value = 0.0

    # Inputs: Particle Size
    sock_size = node_tree.interface.new_socket(
        name="Particle Size",
        in_out='INPUT',
        socket_type='NodeSocketFloat',
    )
    sock_size.default_value = 0.04
    sock_size.min_value = 0.005
    sock_size.max_value = 0.2

    # Group Input / Output
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1200, 0)
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1800, 0)

    # 1. High-Density Base Grid
    grid = nodes.new('GeometryNodeMeshGrid')
    grid.location = (-1000, 300)
    grid.inputs['Size X'].default_value = 16.0
    grid.inputs['Size Y'].default_value = 16.0
    # Map density: 0.5 -> 140x140 (~20,000 points), 1.0 -> 220x220 (~48,000 points)
    res = int(100 + density * 120)
    grid.inputs['Vertices X'].default_value = res
    grid.inputs['Vertices Y'].default_value = res

    # 2. Position Vector
    pos_node = nodes.new('GeometryNodeInputPosition')
    pos_node.location = (-1000, -100)

    # 3. Distance from Center for concentric ripples (Length of XY)
    dist_node = nodes.new('ShaderNodeVectorMath')
    dist_node.location = (-800, -100)
    dist_node.operation = 'LENGTH'
    _link(node_tree, pos_node.outputs['Position'], dist_node.inputs['Vector'])

    # 4. Harmonic Concentric Sine Wave: sin(dist * freq - phase)
    # Multiply distance by spatial frequency
    wave_freq = nodes.new('ShaderNodeMath')
    wave_freq.location = (-600, -100)
    wave_freq.operation = 'MULTIPLY'
    wave_freq.inputs[1].default_value = 2.4
    _link(node_tree, dist_node.outputs['Value'], wave_freq.inputs[0])

    # Sine function
    wave_sine = nodes.new('ShaderNodeMath')
    wave_sine.location = (-400, -100)
    wave_sine.operation = 'SINE'
    _link(node_tree, wave_freq.outputs['Value'], wave_sine.inputs[0])

    # Multiply wave by Audio Bass Wave input
    wave_amp = nodes.new('ShaderNodeMath')
    wave_amp.location = (-200, -100)
    wave_amp.operation = 'MULTIPLY'
    _link(node_tree, wave_sine.outputs['Value'], wave_amp.inputs[0])
    _link(node_tree, input_node.outputs['Audio Bass Wave'], wave_amp.inputs[1])

    # 5. Organic Noise Field (Eduard OV organic turbulence)
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-400, -300)
    noise.inputs['Scale'].default_value = 0.5
    noise.inputs['Detail'].default_value = 4.0
    noise.inputs['Roughness'].default_value = 0.6
    _link(node_tree, pos_node.outputs['Position'], noise.inputs['Vector'])

    # Scale noise by Audio Treble Sparkle
    noise_amp = nodes.new('ShaderNodeMath')
    noise_amp.location = (-200, -300)
    noise_amp.operation = 'MULTIPLY'
    _link(node_tree, noise.outputs['Fac'], noise_amp.inputs[0])
    _link(node_tree, input_node.outputs['Audio Treble Sparkle'], noise_amp.inputs[1])

    # Combine wave + noise displacement for Z
    total_z = nodes.new('ShaderNodeMath')
    total_z.location = (0, -150)
    total_z.operation = 'ADD'
    _link(node_tree, wave_amp.outputs['Value'], total_z.inputs[0])
    _link(node_tree, noise_amp.outputs['Value'], total_z.inputs[1])

    # 6. Build Offset Vector (0, 0, total_z)
    combine_offset = nodes.new('ShaderNodeCombineXYZ')
    combine_offset.location = (200, -150)
    combine_offset.inputs['X'].default_value = 0.0
    combine_offset.inputs['Y'].default_value = 0.0
    _link(node_tree, total_z.outputs['Value'], combine_offset.inputs['Z'])

    # 7. Displace Grid Surface with Set Position
    set_pos = nodes.new('GeometryNodeSetPosition')
    set_pos.location = (400, 300)
    _link(node_tree, grid.outputs['Mesh'], set_pos.inputs['Geometry'])
    _link(node_tree, combine_offset.outputs['Vector'], set_pos.inputs['Offset'])

    # 8. Mesh to Points
    mesh_to_points = nodes.new('GeometryNodeMeshToPoints')
    mesh_to_points.location = (650, 300)
    _link(node_tree, set_pos.outputs['Geometry'], mesh_to_points.inputs['Mesh'])

    # 9. Instance Micro-Spheres (Luminous Quantum Particles)
    ico_particle = nodes.new('GeometryNodeMeshIcoSphere')
    ico_particle.location = (650, 0)
    ico_particle.inputs['Radius'].default_value = 1.0
    ico_particle.inputs['Subdivisions'].default_value = 2

    # Scale calculation: Particle Size * (1.0 + total_z * 0.4)
    size_mult = nodes.new('ShaderNodeMath')
    size_mult.location = (650, -200)
    size_mult.operation = 'MULTIPLY'
    size_mult.inputs[1].default_value = 0.4
    _link(node_tree, total_z.outputs['Value'], size_mult.inputs[0])

    size_add = nodes.new('ShaderNodeMath')
    size_add.location = (850, -200)
    size_add.operation = 'ADD'
    size_add.inputs[0].default_value = 1.0
    _link(node_tree, size_mult.outputs['Value'], size_add.inputs[1])

    final_particle_scale = nodes.new('ShaderNodeMath')
    final_particle_scale.location = (1050, -200)
    final_particle_scale.operation = 'MULTIPLY'
    _link(node_tree, input_node.outputs['Particle Size'], final_particle_scale.inputs[0])
    _link(node_tree, size_add.outputs['Value'], final_particle_scale.inputs[1])

    combine_p_scale = nodes.new('ShaderNodeCombineXYZ')
    combine_p_scale.location = (1250, -200)
    _link(node_tree, final_particle_scale.outputs['Value'], combine_p_scale.inputs['X'])
    _link(node_tree, final_particle_scale.outputs['Value'], combine_p_scale.inputs['Y'])
    _link(node_tree, final_particle_scale.outputs['Value'], combine_p_scale.inputs['Z'])

    # Instance on Points
    instance_points = nodes.new('GeometryNodeInstanceOnPoints')
    instance_points.location = (1200, 300)
    _link(node_tree, mesh_to_points.outputs['Points'], instance_points.inputs['Points'])
    _link(node_tree, ico_particle.outputs['Mesh'], instance_points.inputs['Instance'])
    _link(node_tree, combine_p_scale.outputs['Vector'], instance_points.inputs['Scale'])

    # 10. Assign Material
    final_geo = instance_points.outputs['Instances']
    if material:
        set_mat = nodes.new('GeometryNodeSetMaterial')
        set_mat.location = (1450, 300)
        set_mat.inputs['Material'].default_value = material
        _link(node_tree, instance_points.outputs['Instances'], set_mat.inputs['Geometry'])
        final_geo = set_mat.outputs['Geometry']

    # 11. Connect to output
    _link(node_tree, final_geo, output_node.inputs['Geometry'])

    # Apply modifier
    _apply_gn_modifier(obj, node_tree)
    print(f"[BlenderBeat] Quantum Field GN tree created: {len(nodes)} nodes, resolution={res}x{res} ({res*res} points)")
    return node_tree


def _apply_gn_modifier(
    obj: bpy.types.Object,
    node_tree: bpy.types.NodeTree,
):
    """Apply a Geometry Nodes modifier to an object."""
    mod_name = "BlenderBeat_GN"
    mod = obj.modifiers.get(mod_name)
    if mod is None:
        mod = obj.modifiers.new(name=mod_name, type='NODES')
    mod.node_group = node_tree


def setup_gn_drivers(
    obj: bpy.types.Object,
    node_tree: bpy.types.NodeTree,
):
    """
    Set up drivers connecting the object's custom properties
    to the Geometry Nodes modifier inputs.
    """
    mod = obj.modifiers.get("BlenderBeat_GN")
    if mod is None:
        print("[BlenderBeat] Error: GN modifier not found")
        return

    gn_inputs = _get_gn_input_identifiers(node_tree)

    # Audio Sphere mappings:
    # 1. Drive internal Value nodes in node_tree (rock-solid dynamic evaluation in Blender 5)
    for node_name, prop_name, expr in [
        ("BB_InternalAudioScale", "bb_scale", "var"),
        ("BB_InternalAudioRotation", "bb_rotation_z", "var"),
        ("BB_InternalBeatGlow", "bb_camera_zoom", "var * 1.5"),
    ]:
        node = node_tree.nodes.get(node_name)
        if node and prop_name in obj:
            try:
                df = node.outputs[0].driver_add("default_value")
                d = df.driver
                d.type = 'SCRIPTED'
                d.expression = expr
                var = d.variables.new()
                var.name = "var"
                var.type = 'SINGLE_PROP'
                var.targets[0].id = obj
                var.targets[0].data_path = f'["{prop_name}"]'
                print(f"[BlenderBeat] Internal GN Node Driver: {prop_name} → {node_name}")
            except Exception as e:
                print(f"[BlenderBeat] Warning: failed to set internal GN node driver for {node_name}: {e}")

    # 2. Also drive modifier sockets for backwards compatibility and UI inspection
    if "Audio Scale" in gn_inputs and "bb_scale" in obj:
        _create_modifier_driver(obj, mod, gn_inputs["Audio Scale"], "bb_scale", expression="var")
    if "Audio Rotation" in gn_inputs and "bb_rotation_z" in obj:
        _create_modifier_driver(obj, mod, gn_inputs["Audio Rotation"], "bb_rotation_z", expression="var")
    if "Beat Glow" in gn_inputs:
        driver_prop = "bb_camera_zoom" if "bb_camera_zoom" in obj else "bb_scale"
        if driver_prop in obj:
            _create_modifier_driver(obj, mod, gn_inputs["Beat Glow"], driver_prop, expression="var * 1.5")

    # Quantum Field mappings
    if "Audio Bass Wave" in gn_inputs and "bb_scale" in obj:
        _create_modifier_driver(obj, mod, gn_inputs["Audio Bass Wave"], "bb_scale", expression="var * 2.5")
    if "Audio Treble Sparkle" in gn_inputs and "bb_rotation_z" in obj:
        _create_modifier_driver(obj, mod, gn_inputs["Audio Treble Sparkle"], "bb_rotation_z", expression="var * 1.5")


def _get_gn_input_identifiers(node_tree: bpy.types.NodeTree) -> dict:
    """
    Get the mapping of input socket names to their identifiers
    in the modifier interface.
    """
    result = {}
    for item in node_tree.interface.items_tree:
        if hasattr(item, 'socket_type') and item.in_out == 'INPUT':
            result[item.name] = item.identifier
    return result


def _create_modifier_driver(
    obj: bpy.types.Object,
    modifier: bpy.types.Modifier,
    input_identifier: str,
    source_prop: str,
    expression: str = "var",
):
    """
    Create a driver on a Geometry Nodes modifier input.

    In Blender 4.x:
        modifiers["ModName"]["identifier"]
    In Blender 5.x:
        modifiers["ModName"].properties.inputs["identifier"]["value"]
    """
    candidate_paths = [
        f'modifiers["{modifier.name}"].properties.inputs["{input_identifier}"]["value"]',
        f'modifiers["{modifier.name}"]["{input_identifier}"]',
    ]

    for data_path in candidate_paths:
        try:
            obj.driver_remove(data_path)
        except Exception:
            pass

    driver_fc = None
    for data_path in candidate_paths:
        try:
            driver_fc = obj.driver_add(data_path)
            if driver_fc:
                break
        except Exception:
            continue

    if not driver_fc:
        print(f"[BlenderBeat] Driver failed for {input_identifier}: could not add driver to any candidate path")
        return

    try:
        driver = driver_fc.driver
        driver.type = 'SCRIPTED'
        driver.expression = expression

        var = driver.variables.new()
        var.name = "var"
        var.type = 'SINGLE_PROP'
        var.targets[0].id = obj
        var.targets[0].data_path = f'["{source_prop}"]'

        print(f"[BlenderBeat] Driver: {source_prop} → GN:{input_identifier}")
    except Exception as e:
        print(f"[BlenderBeat] Driver failed for {input_identifier}: {e}")
