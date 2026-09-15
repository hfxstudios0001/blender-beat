"""
BlenderBeat — Music-Reactive 3D Visualizer for Blender

Turn any song into an insane procedural 3D music visualizer.

Music → Audio Analysis → Visual Intelligence → Procedural 3D Scene
→ Music-Reactive Animation → Seamless Loop → Render

Author: BlenderBeat Team
Version: 0.1.0 (Phase 1 — Technical Proof)
"""

bl_info = {
    "name": "BlenderBeat",
    "author": "BlenderBeat",
    "version": (0, 1, 0),
    "blender": (5, 2, 0),
    "location": "View3D > Sidebar > BlenderBeat",
    "description": "Music-reactive 3D visualizer — turn any song into cinematic procedural visuals",
    "category": "Animation",
    "doc_url": "",
    "tracker_url": "",
}


def register():
    """Register the BlenderBeat add-on."""
    print("[BlenderBeat] Registering add-on v0.1.0...")

    from .properties import register_properties
    from .operators import register_operators
    from .panels import register_panels
    import blenderbeat.presets

    register_properties()
    register_operators()
    register_panels()

    print("[BlenderBeat] Add-on registered successfully!")
    print("[BlenderBeat] Find the panel in: View3D > Sidebar (N) > BlenderBeat")


def unregister():
    """Unregister the BlenderBeat add-on."""
    print("[BlenderBeat] Unregistering add-on...")

    from .panels import unregister_panels
    from .operators import unregister_operators
    from .properties import unregister_properties

    unregister_panels()
    unregister_operators()
    unregister_properties()

    print("[BlenderBeat] Add-on unregistered.")


if __name__ == "__main__":
    register()
