"""
BlenderBeat — Infinite Light Grid: Master Frame Geometry Generator.

Creates a single high-detail procedural square frame unit consisting of:
1. 4 structural strut beams along each edge (dark gunmetal housing)
2. 4 corner joint spheres (chrome mechanical nodes)
3. 4 primary LED edge bars (emissive neon strips recessed into struts)
4. 4 secondary dashed LED accent segments on strut faces
5. 4 thin connecting rods between corners (chrome detail)

This is the HERO COMPONENT — it must look premium on its own
before any instancing or tunnel assembly.
"""

import bpy
import math
from typing import Optional


def _add_box(
    verts: list,
    faces: list,
    face_mats: list,
    center: tuple,
    size: tuple,
    mat_idx: int,
    pipe_ids: list = None,
    pipe_id: float = -1.0,
):
    """Add an axis-aligned box to the mesh data."""
    cx, cy, cz = center
    sx, sy, sz = size[0] * 0.5, size[1] * 0.5, size[2] * 0.5

    v = len(verts)
    verts.extend([
        (cx - sx, cy - sy, cz - sz),  # 0: back-bottom-left
        (cx + sx, cy - sy, cz - sz),  # 1: back-bottom-right
        (cx + sx, cy + sy, cz - sz),  # 2: back-top-right
        (cx - sx, cy + sy, cz - sz),  # 3: back-top-left
        (cx - sx, cy - sy, cz + sz),  # 4: front-bottom-left
        (cx + sx, cy - sy, cz + sz),  # 5: front-bottom-right
        (cx + sx, cy + sy, cz + sz),  # 6: front-top-right
        (cx - sx, cy + sy, cz + sz),  # 7: front-top-left
    ])
    # 6 faces of the box
    box_faces = [
        (v+0, v+1, v+2, v+3),  # back
        (v+4, v+7, v+6, v+5),  # front
        (v+0, v+4, v+5, v+1),  # bottom
        (v+2, v+6, v+7, v+3),  # top
        (v+0, v+3, v+7, v+4),  # left
        (v+1, v+5, v+6, v+2),  # right
    ]
    faces.extend(box_faces)
    face_mats.extend([mat_idx] * 6)
    if pipe_ids is not None:
        pipe_ids.extend([pipe_id] * 6)


def _add_rotated_box(
    verts: list,
    faces: list,
    face_mats: list,
    start: tuple,
    end: tuple,
    width: float,
    height: float,
    mat_idx: int,
    pipe_ids: list = None,
    pipe_id: float = -1.0,
):
    """
    Add a box oriented along the vector from start to end.
    Width is perpendicular in XY plane, height is along Z.
    """
    sx, sy, sz = start
    ex, ey, ez = end

    # Direction vector
    dx, dy = ex - sx, ey - sy
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-6:
        return

    # Normalized perpendicular (in XY plane)
    nx, ny = -dy / length, dx / length

    w2 = width * 0.5
    h2 = height * 0.5

    v = len(verts)
    # 8 vertices: 4 at start cross-section, 4 at end cross-section
    verts.extend([
        (sx + nx * w2, sy + ny * w2, sz - h2),
        (sx - nx * w2, sy - ny * w2, sz - h2),
        (sx - nx * w2, sy - ny * w2, sz + h2),
        (sx + nx * w2, sy + ny * w2, sz + h2),
        (ex + nx * w2, ey + ny * w2, ez - h2),
        (ex - nx * w2, ey - ny * w2, ez - h2),
        (ex - nx * w2, ey - ny * w2, ez + h2),
        (ex + nx * w2, ey + ny * w2, ez + h2),
    ])

    box_faces = [
        (v+0, v+1, v+2, v+3),  # start cap
        (v+4, v+7, v+6, v+5),  # end cap
        (v+0, v+4, v+5, v+1),  # bottom
        (v+2, v+6, v+7, v+3),  # top
        (v+0, v+3, v+7, v+4),  # side A
        (v+1, v+5, v+6, v+2),  # side B
    ]
    faces.extend(box_faces)
    face_mats.extend([mat_idx] * 6)
    if pipe_ids is not None:
        pipe_ids.extend([pipe_id] * 6)


def _add_icosphere(
    verts: list,
    faces: list,
    face_mats: list,
    center: tuple,
    radius: float,
    subdivisions: int,
    mat_idx: int,
    pipe_ids: list = None,
    pipe_id: float = -1.0,
):
    """Add an icosphere to the mesh data."""
    cx, cy, cz = center

    # Golden ratio for icosphere construction
    phi = (1.0 + math.sqrt(5.0)) / 2.0

    # 12 base vertices of icosahedron
    ico_verts = [
        (-1,  phi, 0), ( 1,  phi, 0), (-1, -phi, 0), ( 1, -phi, 0),
        ( 0, -1,  phi), ( 0,  1,  phi), ( 0, -1, -phi), ( 0,  1, -phi),
        ( phi, 0, -1), ( phi, 0,  1), (-phi, 0, -1), (-phi, 0,  1),
    ]

    ico_faces = [
        (0,11,5), (0,5,1), (0,1,7), (0,7,10), (0,10,11),
        (1,5,9), (5,11,4), (11,10,2), (10,7,6), (7,1,8),
        (3,9,4), (3,4,2), (3,2,6), (3,6,8), (3,8,9),
        (4,9,5), (2,4,11), (6,2,10), (8,6,7), (9,8,1),
    ]

    # Subdivide
    cache = {}
    current_verts = list(ico_verts)
    current_faces = list(ico_faces)

    def midpoint(v1_idx, v2_idx):
        key = (min(v1_idx, v2_idx), max(v1_idx, v2_idx))
        if key in cache:
            return cache[key]
        p1 = current_verts[v1_idx]
        p2 = current_verts[v2_idx]
        mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2)
        # Normalize to unit sphere
        l = math.sqrt(mid[0]**2 + mid[1]**2 + mid[2]**2)
        if l > 0:
            mid = (mid[0]/l, mid[1]/l, mid[2]/l)
        idx = len(current_verts)
        current_verts.append(mid)
        cache[key] = idx
        return idx

    for _ in range(subdivisions):
        new_faces = []
        cache = {}
        for tri in current_faces:
            a, b, c = tri
            ab = midpoint(a, b)
            bc = midpoint(b, c)
            ca = midpoint(c, a)
            new_faces.extend([
                (a, ab, ca),
                (b, bc, ab),
                (c, ca, bc),
                (ab, bc, ca),
            ])
        current_faces = new_faces

    # Normalize all verts to radius and offset to center
    v_base = len(verts)
    for vx, vy, vz in current_verts:
        l = math.sqrt(vx*vx + vy*vy + vz*vz)
        if l > 0:
            vx, vy, vz = vx/l*radius, vy/l*radius, vz/l*radius
        verts.append((cx + vx, cy + vy, cz + vz))

    for tri in current_faces:
        faces.append((v_base + tri[0], v_base + tri[1], v_base + tri[2]))
        face_mats.append(mat_idx)
    if pipe_ids is not None:
        pipe_ids.extend([pipe_id] * len(current_faces))


def create_master_frame_mesh(
    name: str = "BB_MasterFrame",
    frame_size: float = 3.0,
    depth: float = 0.35,
    mat_led: Optional[bpy.types.Material] = None,
) -> bpy.types.Object:
    """
    Generate the master square frame corridor section consisting of:
    1. Rectangular structural strut beams along each edge (MAT_DARK_METAL, slot 0)
    2. Chrome mechanical joint spheres at each corner (MAT_CHROME, slot 1)
    3. Glowing LED neon bars recessed into each edge (MAT_GRID_LED, slot 2)
    4. Short dashed LED accent strips on strut faces (MAT_GRID_LED, slot 2)
    5. Thin chrome connecting rods diagonally between corner joint details (slot 1)

    Args:
        name: Object name
        frame_size: Side length of the square frame
        depth: Z-thickness of the frame section
        mat_led: Pre-created LED emission material (or None to create default)

    Returns:
        bpy.types.Object: The master frame mesh object with 3 material slots
    """
    # Remove old object
    old_obj = bpy.data.objects.get(name)
    if old_obj:
        bpy.data.objects.remove(old_obj, do_unlink=True)

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    # Materials (reuse from existing library)
    from ...visual.materials_library import (
        create_dark_metal_material,
        create_chrome_material,
    )
    mat_dark = create_dark_metal_material()
    mat_chrome = create_chrome_material()
    if mat_led is None:
        from .grid_materials import create_grid_led_material
        mat_led = create_grid_led_material()

    obj.data.materials.append(mat_dark)    # Slot 0: Dark gunmetal structural
    obj.data.materials.append(mat_chrome)  # Slot 1: Chrome joints & rods
    obj.data.materials.append(mat_led)     # Slot 2: LED emission

    verts = []
    faces = []
    face_mats = []
    pipe_ids = []

    half = frame_size * 0.5

    # Corner positions (square in XY plane, centered at origin)
    corners = [
        (-half, -half, 0.0),  # bottom-left
        ( half, -half, 0.0),  # bottom-right
        ( half,  half, 0.0),  # top-right
        (-half,  half, 0.0),  # top-left
    ]

    # Edge pairs (for struts and LED bars)
    edges = [
        (0, 1),  # bottom edge
        (1, 2),  # right edge
        (2, 3),  # top edge
        (3, 0),  # left edge
    ]

    # ═══════════════════════════════════════════════════════════════════
    # 1. STRUCTURAL STRUT BEAMS (Dark Metal housing around LED channels)
    # ═══════════════════════════════════════════════════════════════════
    strut_width = 0.16     # Width perpendicular to edge direction
    strut_height = depth   # Full depth of frame section

    # Inset corners slightly so struts don't overlap with joint spheres
    corner_inset = 0.22

    for i, (c0_idx, c1_idx) in enumerate(edges):
        c0 = corners[c0_idx]
        c1 = corners[c1_idx]

        # Direction from c0 to c1
        dx = c1[0] - c0[0]
        dy = c1[1] - c0[1]
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1e-6:
            continue
        ux, uy = dx / length, dy / length

        # Inset start and end points
        start = (c0[0] + ux * corner_inset, c0[1] + uy * corner_inset, 0.0)
        end = (c1[0] - ux * corner_inset, c1[1] - uy * corner_inset, 0.0)

        _add_rotated_box(
            verts, faces, face_mats,
            start, end,
            width=strut_width,
            height=strut_height,
            mat_idx=0,
            pipe_ids=pipe_ids,
            pipe_id=-1.0,
        )

    # ═══════════════════════════════════════════════════════════════════
    # 2. CORNER JOINT SPHERES (Chrome mechanical nodes)
    # ═══════════════════════════════════════════════════════════════════
    joint_radius = 0.14

    for cx, cy, cz in corners:
        _add_icosphere(
            verts, faces, face_mats,
            center=(cx, cy, cz),
            radius=joint_radius,
            subdivisions=2,  # 2 subdivisions = 80 faces, smooth but efficient
            mat_idx=1,
            pipe_ids=pipe_ids,
            pipe_id=-1.0,
        )

    # ═══════════════════════════════════════════════════════════════════
    # 3. PRIMARY LED EDGE BARS (Emissive neon strips recessed into struts)
    #    Each of the 4 edges has a distinct pipe_id: 0.0, 1.0, 2.0, 3.0
    # ═══════════════════════════════════════════════════════════════════
    led_width = 0.08    # Clean luminous neon tube
    led_height = 0.08   # Square cross-section neon bar

    for i, (c0_idx, c1_idx) in enumerate(edges):
        c0 = corners[c0_idx]
        c1 = corners[c1_idx]

        dx = c1[0] - c0[0]
        dy = c1[1] - c0[1]
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1e-6:
            continue
        ux, uy = dx / length, dy / length

        # Inward direction pointing towards tunnel axis (0, 0)
        mid_x = (c0[0] + c1[0]) * 0.5
        mid_y = (c0[1] + c1[1]) * 0.5
        dist = math.sqrt(mid_x * mid_x + mid_y * mid_y)
        in_x = -mid_x / dist if dist > 1e-6 else 0.0
        in_y = -mid_y / dist if dist > 1e-6 else 0.0

        # Position neon bar on the inner surface facing into the tunnel
        inner_offset = (strut_width * 0.5) + (led_width * 0.5) - 0.02
        led_inset = corner_inset + 0.02
        start = (
            c0[0] + ux * led_inset + in_x * inner_offset,
            c0[1] + uy * led_inset + in_y * inner_offset,
            0.0,
        )
        end = (
            c1[0] - ux * led_inset + in_x * inner_offset,
            c1[1] - uy * led_inset + in_y * inner_offset,
            0.0,
        )

        _add_rotated_box(
            verts, faces, face_mats,
            start, end,
            width=led_width,
            height=led_height,
            mat_idx=2,
            pipe_ids=pipe_ids,
            pipe_id=float(i),  # Pipe ID: 0.0, 1.0, 2.0, 3.0
        )

    # ═══════════════════════════════════════════════════════════════════
    # 4. SECONDARY DASHED LED ACCENT STRIPS (short segments on outer strut face)
    # ═══════════════════════════════════════════════════════════════════
    num_dashes = 3  # Dashes per edge
    dash_gap_ratio = 0.35  # Fraction of segment that is gap

    for i, (c0_idx, c1_idx) in enumerate(edges):
        c0 = corners[c0_idx]
        c1 = corners[c1_idx]

        dx = c1[0] - c0[0]
        dy = c1[1] - c0[1]
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1e-6:
            continue
        ux, uy = dx / length, dy / length

        # Perpendicular outward direction (away from center)
        mid_x = (c0[0] + c1[0]) * 0.5
        mid_y = (c0[1] + c1[1]) * 0.5
        out_len = math.sqrt(mid_x * mid_x + mid_y * mid_y)
        if out_len < 1e-6:
            continue
        out_x = mid_x / out_len
        out_y = mid_y / out_len

        # Offset the dashes outward from the strut surface
        offset_dist = strut_width * 0.5 + 0.005  # Just outside the strut

        usable_length = length - 2.0 * corner_inset - 0.1
        dash_total = usable_length / num_dashes
        dash_len = dash_total * (1.0 - dash_gap_ratio)

        for d in range(num_dashes):
            t_start = corner_inset + 0.05 + d * dash_total + dash_total * dash_gap_ratio * 0.5
            t_end = t_start + dash_len

            ds = (
                c0[0] + ux * t_start + out_x * offset_dist,
                c0[1] + uy * t_start + out_y * offset_dist,
                depth * 0.25,  # Offset upward slightly for visual separation
            )
            de = (
                c0[0] + ux * t_end + out_x * offset_dist,
                c0[1] + uy * t_end + out_y * offset_dist,
                depth * 0.25,
            )

            _add_rotated_box(
                verts, faces, face_mats,
                ds, de,
                width=0.025,  # Very thin accent
                height=0.018,
                mat_idx=2,
                pipe_ids=pipe_ids,
                pipe_id=float(i),  # Tied to the same edge pipe index
            )

    # ═══════════════════════════════════════════════════════════════════
    # 5. THIN CHROME CONNECTING RODS (detail between adjacent corners)
    # ═══════════════════════════════════════════════════════════════════
    rod_width = 0.025
    rod_height = 0.025

    for i, (c0_idx, c1_idx) in enumerate(edges):
        c0 = corners[c0_idx]
        c1 = corners[c1_idx]

        dx = c1[0] - c0[0]
        dy = c1[1] - c0[1]
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1e-6:
            continue
        ux, uy = dx / length, dy / length

        # Small rod offset outward from the strut center
        mid_x = (c0[0] + c1[0]) * 0.5
        mid_y = (c0[1] + c1[1]) * 0.5
        out_len = math.sqrt(mid_x * mid_x + mid_y * mid_y)
        if out_len < 1e-6:
            continue
        out_x = mid_x / out_len
        out_y = mid_y / out_len

        rod_offset = strut_width * 0.5 + 0.01
        rod_z = -depth * 0.3  # Below center for visual layering

        start = (
            c0[0] + ux * (corner_inset * 0.5) + out_x * rod_offset,
            c0[1] + uy * (corner_inset * 0.5) + out_y * rod_offset,
            rod_z,
        )
        end = (
            c1[0] - ux * (corner_inset * 0.5) + out_x * rod_offset,
            c1[1] - uy * (corner_inset * 0.5) + out_y * rod_offset,
            rod_z,
        )

        _add_rotated_box(
            verts, faces, face_mats,
            start, end,
            width=rod_width,
            height=rod_height,
            mat_idx=1,
            pipe_ids=pipe_ids,
            pipe_id=-1.0,
        )

    # ═══════════════════════════════════════════════════════════════════
    # Build the mesh
    # ═══════════════════════════════════════════════════════════════════
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    for poly, mat_idx in zip(mesh.polygons, face_mats):
        poly.material_index = mat_idx

    # Store pipe ID attribute (0..3 for the 4 inner LED pipes, -1 for all other faces)
    pipe_attr = mesh.attributes.new(name="bb_pipe_id", type='FLOAT', domain='FACE')
    pipe_attr.data.foreach_set('value', pipe_ids)

    # Auto-smooth for clean specular highlights
    mesh.shade_smooth()

    print(f"[BlenderBeat] Master Frame generated: {len(verts)} verts, "
          f"{len(faces)} faces, 3 materials, frame_size={frame_size}m")
    return obj
