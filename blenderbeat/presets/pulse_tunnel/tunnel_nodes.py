"""
BlenderBeat — Pulse Tunnel: Geometry Nodes Instancing Engine.

Instances the master radial-spoke disk along -Z to create tunnel depth.
Each ring gets a slight Z-rotation offset for visual variation.
Realizes instances so Object-space coordinates work in shaders.
"""

import bpy
import math
from typing import Optional


def create_pulse_tunnel_geometry_nodes(
    viz_obj: bpy.types.Object,
    ring_obj: bpy.types.Object,
    ring_count: int = 80,
    spacing: float = 1.8,
) -> bpy.types.NodeTree:
    """
    Build the Geometry Nodes modifier tree for the Pulse Tunnel.

    Args:
        viz_obj: The BB_Visualizer object that receives the GN modifier.
        ring_obj: The master radial disk object to instance.
        ring_count: Number of disks in the tunnel.
        spacing: Distance between disks along Z.

    Returns:
        The NodeTree for external driver connection.
    """
    tree_name = "BB_PulseTunnelGN"

    # Clean or create node tree
    if tree_name in bpy.data.node_groups:
        node_tree = bpy.data.node_groups[tree_name]
        for n in list(node_tree.nodes):
            node_tree.nodes.remove(n)
    else:
        node_tree = bpy.data.node_groups.new(tree_name, 'GeometryNodeTree')

    nodes = node_tree.nodes
    links = node_tree.links

    # Clear interface sockets
    for item in list(node_tree.interface.items_tree):
        if item.item_type in {'SOCKET'}:
            node_tree.interface.remove(item)

    # Output geometry socket
    node_tree.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry',
    )

    # ── Layout ──────────────────────────────────────────────────────
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1400, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1200, 0)

    # ── Internal Value Nodes (for drivers) ──────────────────────────
    kick_val = nodes.new('ShaderNodeValue')
    kick_val.name = "BB_PT_GN_KickVal"
    kick_val.label = "Kick Signal (Driven)"
    kick_val.location = (-1200, 300)

    bass_val = nodes.new('ShaderNodeValue')
    bass_val.name = "BB_PT_GN_BassVal"
    bass_val.label = "Bass Signal (Driven)"
    bass_val.location = (-1200, 150)

    energy_val = nodes.new('ShaderNodeValue')
    energy_val.name = "BB_PT_GN_EnergyVal"
    energy_val.label = "Energy Signal (Driven)"
    energy_val.location = (-1200, 0)

    time_val = nodes.new('ShaderNodeValue')
    time_val.name = "BB_PT_GN_TimeVal"
    time_val.label = "Time Phase (Driven)"
    time_val.location = (-1200, -150)

    # ── 1. Mesh Line: disk positions along -Z ───────────────────────
    line = nodes.new('GeometryNodeMeshLine')
    line.location = (-800, 400)
    line.inputs['Count'].default_value = ring_count
    line.inputs['Start Location'].default_value = (0.0, 0.0, 0.0)
    line.inputs['Offset'].default_value = (0.0, 0.0, -spacing)

    # ── 2. Object Info: fetch master disk geometry ──────────────────
    ring_info = nodes.new('GeometryNodeObjectInfo')
    ring_info.location = (-800, 100)
    ring_info.inputs['Object'].default_value = ring_obj
    ring_info.transform_space = 'RELATIVE'

    # ── 3. Index node for per-ring variation ─────────────────────────
    index_node = nodes.new('GeometryNodeInputIndex')
    index_node.location = (-800, -100)

    # ── 4. Per-ring Z-rotation offset ───────────────────────────────
    # Perfectly aligned down tunnel for concentric vanishing point
    rot_combine = nodes.new('ShaderNodeCombineXYZ')
    rot_combine.location = (-300, -100)
    rot_combine.inputs['X'].default_value = 0.0
    rot_combine.inputs['Y'].default_value = 0.0
    rot_combine.inputs['Z'].default_value = 0.0

    # ── 5. Uniform scale (all rings same size) ──────────────────────
    scale_combine = nodes.new('ShaderNodeCombineXYZ')
    scale_combine.location = (-300, -300)
    scale_combine.inputs['X'].default_value = 1.0
    scale_combine.inputs['Y'].default_value = 1.0
    scale_combine.inputs['Z'].default_value = 1.0

    # ── 6. Instance on Points ───────────────────────────────────────
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    instance.location = (0, 200)
    links.new(line.outputs["Mesh"], instance.inputs["Points"])
    links.new(ring_info.outputs["Geometry"], instance.inputs["Instance"])
    links.new(rot_combine.outputs["Vector"], instance.inputs["Rotation"])
    links.new(scale_combine.outputs["Vector"], instance.inputs["Scale"])

    # ── 7. Realize Instances ────────────────────────────────────────
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (300, 200)
    links.new(instance.outputs["Instances"], realize.inputs["Geometry"])

    # ── 8. Output ───────────────────────────────────────────────────
    links.new(realize.outputs["Geometry"], output_node.inputs["Geometry"])

    # ── Assign GN modifier to viz_obj ───────────────────────────────
    for mod in list(viz_obj.modifiers):
        if mod.type == 'NODES':
            viz_obj.modifiers.remove(mod)

    mod = viz_obj.modifiers.new(name="PulseTunnelGN", type='NODES')
    mod.node_group = node_tree

    tunnel_depth = ring_count * spacing
    print(f"[BlenderBeat] Pulse Tunnel GN: {ring_count} disks, "
          f"spacing={spacing}m, tunnel_depth={tunnel_depth}m")
    return node_tree
