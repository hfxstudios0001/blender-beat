"""
BlenderBeat — Pulse Tunnel: Radial Spoke Ring Disk Generator (Exact Video Match).

Creates a single master disk mesh viewed HEAD-ON with authentic video proportions:
  - Open central hole (vanishing point beacon)
  - Zone 1: Inner thin tick ring (32 segments, width ~20%)
  - Zone 2: Mid star-pattern radial bars (32 segments, modulated lengths)
  - Zone 3: Hero continuous bright cyan glow ring + fringe ticks
  - Zone 4: Outer sleek radial spoke bars (32 segments)
  - Zone 5: Perimeter diamond / chevron accents (16 segments)
  - Dark chrome structural backing plate
  - Material slots:
      [0] = dark chrome hull (structural bands / backing plate)
      [1] = LED radial bar (audio-reactive cyan / magenta / white spokes)
      [2] = glow ring (bright continuous cyan halo)
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix


def create_master_ring_mesh(
    name: str = "BB_PT_MasterRing",
    outer_radius: float = 8.0,
    segments_per_zone: int = 32,
    mat_hull=None,
    mat_led=None,
    mat_glow=None,
) -> bpy.types.Object:
    """
    Build the master radial-spoke disk mesh matching the reference video.
    """
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bm = bmesh.new()

    scale = outer_radius / 8.0
    disk_half_depth = 0.08
    seg_angle = 2.0 * math.pi / segments_per_zone  # 32 divisions = 11.25 deg

    # 1. Dark structural mounting bezels (sleek thin rims, NOT solid occluding plates)
    # Leaving open gaps between zones so you see completely through to deep tunnel rings
    backing_rings = [
        (3.45, 3.52),  # Bezel behind inner halo edge
        (3.72, 3.80),  # Bezel behind outer halo edge
        (7.60, 8.00),  # Outer tunnel frame ring
    ]
    for r_in, r_out in backing_rings:
        _create_annular_ring(
            bm, r_in * scale, r_out * scale,
            subdivisions=segments_per_zone * 2,
            half_depth=disk_half_depth * 0.4,
            z_offset=-disk_half_depth * 0.5,
            mat_index=0,  # Hull
        )

    # 2. Zone 1: Inner thin tick ring (32 segments, short ticks)
    # r = 1.1 to 1.7, thin bars covering ~22% of arc
    bar_half_arc_inner = (seg_angle * 0.22) / 2.0
    for i in range(segments_per_zone):
        ang = i * seg_angle
        _create_radial_bar(
            bm, ang, bar_half_arc_inner,
            1.15 * scale, 1.65 * scale,
            disk_half_depth, 0.0,
            mat_index=1,
        )

    # 3. Zone 2: Mid star-burst radial spokes (32 segments)
    # Alternating long and short spokes creating the 8-pointed star shape seen in video
    bar_half_arc_mid = (seg_angle * 0.20) / 2.0
    for i in range(segments_per_zone):
        ang = i * seg_angle
        # 8-fold harmonic: every 4th spoke is a long hero bar, intermediates are stepped
        # i % 4 == 0 -> peak length, i % 4 == 2 -> mid length, odd -> short
        mod4 = i % 4
        if mod4 == 0:
            r_outer_spoke = 3.35  # Long spoke reaches close to halo ring
        elif mod4 == 2:
            r_outer_spoke = 2.85  # Medium spoke
        else:
            r_outer_spoke = 2.50  # Short spoke

        _create_radial_bar(
            bm, ang, bar_half_arc_mid,
            2.05 * scale, r_outer_spoke * scale,
            disk_half_depth, 0.0,
            mat_index=1,
        )

    # 4. Zone 3: Hero segmented glow ring (Halo)
    # Split into 32 independent arched rectangular segments so every single piece reacts independently
    halo_block_half_arc = (seg_angle * 0.88) / 2.0  # 88% arc coverage with crisp cut gaps
    for i in range(segments_per_zone):
        ang = i * seg_angle
        _create_radial_bar(
            bm, ang, halo_block_half_arc,
            3.52 * scale, 3.72 * scale,
            disk_half_depth * 1.1, 0.01,
            mat_index=1,
        )

    # Fringe ticks on outer edge of the halo (32 short blocks)
    fringe_half_arc = (seg_angle * 0.25) / 2.0
    for i in range(segments_per_zone):
        ang = i * seg_angle + (seg_angle * 0.5)  # Offset
        _create_radial_bar(
            bm, ang, fringe_half_arc,
            3.72 * scale, 3.95 * scale,
            disk_half_depth, 0.0,
            mat_index=1,
        )

    # 5. Zone 4: Outer sleek radial spoke bars (32 segments)
    bar_half_arc_outer = (seg_angle * 0.16) / 2.0
    for i in range(segments_per_zone):
        ang = i * seg_angle
        # Outer bars alternate lengths
        r_outer_end = 5.2 if (i % 2 == 0) else 4.7
        _create_radial_bar(
            bm, ang, bar_half_arc_outer,
            4.15 * scale, r_outer_end * scale,
            disk_half_depth, 0.0,
            mat_index=1,
        )

    # 6. Zone 5: Perimeter Diamond / Chevron Accents (16 segments)
    diamond_count = 16
    diamond_seg_angle = 2.0 * math.pi / diamond_count
    for i in range(diamond_count):
        ang = i * diamond_seg_angle + (diamond_seg_angle * 0.5)
        _create_diamond_marker(
            bm, ang,
            r_center=5.8 * scale,
            radial_span=0.45 * scale,
            arc_width=0.045,
            half_depth=disk_half_depth,
            mat_index=1,
        )

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    # Materials
    if mat_hull:
        mesh.materials.append(mat_hull)
    else:
        mesh.materials.append(bpy.data.materials.new("BB_Mat_PT_Hull_Placeholder"))

    if mat_led:
        mesh.materials.append(mat_led)
    else:
        mesh.materials.append(bpy.data.materials.new("BB_Mat_PT_LED_Placeholder"))

    if mat_glow:
        mesh.materials.append(mat_glow)
    else:
        mesh.materials.append(bpy.data.materials.new("BB_Mat_PT_Glow_Placeholder"))

    try:
        mesh.shade_smooth()
    except AttributeError:
        for poly in mesh.polygons:
            poly.use_smooth = True

    obj.hide_viewport = True
    obj.hide_render = True

    print(f"[BlenderBeat] Master radial disk '{name}' created matching reference video!")
    return obj


def _create_annular_ring(
    bm, r_inner: float, r_outer: float, subdivisions: int,
    half_depth: float, z_offset: float, mat_index: int = 0,
):
    """Create a continuous solid annular ring."""
    seg_angle = 2.0 * math.pi / subdivisions

    for i in range(subdivisions):
        a0 = i * seg_angle
        a1 = (i + 1) * seg_angle

        # Front face
        v0 = bm.verts.new((r_outer * math.cos(a0), r_outer * math.sin(a0), half_depth + z_offset))
        v1 = bm.verts.new((r_outer * math.cos(a1), r_outer * math.sin(a1), half_depth + z_offset))
        v2 = bm.verts.new((r_inner * math.cos(a1), r_inner * math.sin(a1), half_depth + z_offset))
        v3 = bm.verts.new((r_inner * math.cos(a0), r_inner * math.sin(a0), half_depth + z_offset))
        f = bm.faces.new([v0, v1, v2, v3])
        f.material_index = mat_index

        # Back face
        v4 = bm.verts.new((r_outer * math.cos(a1), r_outer * math.sin(a1), -half_depth + z_offset))
        v5 = bm.verts.new((r_outer * math.cos(a0), r_outer * math.sin(a0), -half_depth + z_offset))
        v6 = bm.verts.new((r_inner * math.cos(a0), r_inner * math.sin(a0), -half_depth + z_offset))
        v7 = bm.verts.new((r_inner * math.cos(a1), r_inner * math.sin(a1), -half_depth + z_offset))
        fb = bm.faces.new([v4, v5, v6, v7])
        fb.material_index = mat_index


def _create_radial_bar(
    bm, center_angle: float, half_arc: float,
    r_inner: float, r_outer: float,
    half_depth: float, z_offset: float,
    mat_index: int = 1,
):
    """Create a sleek radial rectangular bar spoke."""
    a0 = center_angle - half_arc
    a1 = center_angle + half_arc

    v0 = bm.verts.new((r_inner * math.cos(a0), r_inner * math.sin(a0), half_depth + z_offset))
    v1 = bm.verts.new((r_outer * math.cos(a0), r_outer * math.sin(a0), half_depth + z_offset))
    v2 = bm.verts.new((r_outer * math.cos(a1), r_outer * math.sin(a1), half_depth + z_offset))
    v3 = bm.verts.new((r_inner * math.cos(a1), r_inner * math.sin(a1), half_depth + z_offset))
    f_front = bm.faces.new([v0, v1, v2, v3])
    f_front.material_index = mat_index

    v4 = bm.verts.new((r_inner * math.cos(a1), r_inner * math.sin(a1), -half_depth + z_offset))
    v5 = bm.verts.new((r_outer * math.cos(a1), r_outer * math.sin(a1), -half_depth + z_offset))
    v6 = bm.verts.new((r_outer * math.cos(a0), r_outer * math.sin(a0), -half_depth + z_offset))
    v7 = bm.verts.new((r_inner * math.cos(a0), r_inner * math.sin(a0), -half_depth + z_offset))
    f_back = bm.faces.new([v4, v5, v6, v7])
    f_back.material_index = mat_index


def _create_diamond_marker(
    bm, center_angle: float, r_center: float, radial_span: float,
    arc_width: float, half_depth: float, mat_index: int = 1,
):
    """Create a sharp diamond / chevron LED accent."""
    r_in = r_center - radial_span * 0.5
    r_out = r_center + radial_span * 0.5

    # 4 vertices: inner tip, outer tip, left corner, right corner
    v_in = bm.verts.new((r_in * math.cos(center_angle), r_in * math.sin(center_angle), half_depth))
    v_out = bm.verts.new((r_out * math.cos(center_angle), r_out * math.sin(center_angle), half_depth))
    v_left = bm.verts.new((r_center * math.cos(center_angle - arc_width), r_center * math.sin(center_angle - arc_width), half_depth))
    v_right = bm.verts.new((r_center * math.cos(center_angle + arc_width), r_center * math.sin(center_angle + arc_width), half_depth))

    f = bm.faces.new([v_in, v_left, v_out, v_right])
    f.material_index = mat_index

