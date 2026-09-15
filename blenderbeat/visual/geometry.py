"""
BlenderBeat — Geometry creation helpers.

Utility functions for creating and managing geometry objects
that the visualizer system uses.
"""

import bpy
from typing import Optional


def create_visualizer_object(
    name: str = "BB_Visualizer",
) -> bpy.types.Object:
    """
    Create the main visualizer object.

    This is an empty mesh that will receive the Geometry Nodes modifier.
    The actual geometry is generated entirely by Geometry Nodes.
    """
    # Return existing if already present
    existing = bpy.data.objects.get(name)
    if existing:
        return existing

    # Create empty mesh
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    # Link to scene
    bpy.context.collection.objects.link(obj)

    # Set as active object
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    return obj


def clear_blenderbeat_objects():
    """Remove all BlenderBeat-generated objects from the scene."""
    to_remove = []

    for obj in bpy.data.objects:
        if obj.name.startswith("BB_") or obj.name == "Cube":
            to_remove.append(obj)

    for obj in to_remove:
        bpy.data.objects.remove(obj, do_unlink=True)

    # Clean up orphan data
    for mesh in bpy.data.meshes:
        if mesh.name.startswith("BB_") and mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    for mat in bpy.data.materials:
        if mat.name.startswith("BB_") and mat.users == 0:
            bpy.data.materials.remove(mat)

    for ng in bpy.data.node_groups:
        if ng.name.startswith("BB_") and ng.users == 0:
            bpy.data.node_groups.remove(ng)

    for cam in bpy.data.cameras:
        if cam.name.startswith("BB_") and cam.users == 0:
            bpy.data.cameras.remove(cam)

    for light in bpy.data.lights:
        if light.name.startswith("BB_") and light.users == 0:
            bpy.data.lights.remove(light)

    for action in bpy.data.actions:
        if action.name.startswith("BB_") and action.users == 0:
            bpy.data.actions.remove(action)

    print("[BlenderBeat] Cleared all BB objects")


def set_object_material(obj: bpy.types.Object, material: bpy.types.Material):
    """Assign a material to an object, replacing existing BB materials."""
    # Remove existing BB materials
    for i in range(len(obj.data.materials) - 1, -1, -1):
        if obj.data.materials[i] and obj.data.materials[i].name.startswith("BB_"):
            obj.data.materials.pop(index=i)

    # Add the new material
    if material.name not in [m.name for m in obj.data.materials if m]:
        obj.data.materials.append(material)
