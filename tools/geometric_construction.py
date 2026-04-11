"""
tools/geometric_construction.py
Geometric Construction tools — maps to the B.Des ID curriculum subject
'Geometric Construction' (1202504) and 'Analytical Drawing' (1202512).

Covers:
  • Regular polygon construction (triangle → dodecagon, by circle/angle methods)
  • Isometric drawing grid setup (30° axes)
  • Orthographic projection view layout (plan / front / side)
  • Section-cut markers and hatching
  • Scale-drawing helpers (enlarge / reduce, custom scale bar)
  • Surface development (prism / pyramid unfolding)
  • Perspective grid setup (1-point and 2-point)
  • Golden ratio / Fibonacci spiral overlay
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_active_doc, get_model_space, point


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _var(coords):
    """Convert a flat list of floats to a COM VARIANT array."""
    return win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(c) for c in coords]
    )


def _polyline(space, pts_flat, closed=False):
    """Draw a lightweight 2D polyline from a flat list [x0,y0, x1,y1, ...]."""
    pl = space.AddLightWeightPolyline(_var(pts_flat))
    if closed:
        pl.Closed = True
    return pl


def _hatch_region(space, boundary_handle, pattern="ANSI31", scale=1.0, angle=0.0):
    """Create a hatch inside a closed polyline boundary."""
    doc = get_active_doc()
    outer = doc.HandleToObject(boundary_handle)
    hatch = space.AddHatch(0, pattern, True)
    hatch.PatternScale = scale
    hatch.PatternAngle = math.radians(angle)
    outer_loop = _var([outer])
    hatch.AppendOuterLoop(outer_loop)
    hatch.Evaluate()
    return hatch


# ---------------------------------------------------------------------------
# Register all tools
# ---------------------------------------------------------------------------

def register_geometric_construction_tools(mcp):

    # ------------------------------------------------------------------
    # POLYGONS
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_regular_polygon(
        cx: float, cy: float,
        sides: int,
        radius: float,
        method: str = "circumscribed",
        rotation_deg: float = 0.0,
        layer: str = "A-GEOM"
    ) -> dict:
        """
        Draw a regular polygon (3–12 sides) centred at (cx, cy).

        method: 'circumscribed' — radius is vertex distance (corner touches circle),
                'inscribed'     — radius is mid-edge distance (edge touches circle).
        rotation_deg: rotate the polygon CCW by this many degrees.
        Covers curriculum: Unit 4 — Construction of platonic shapes.
        """
        if sides < 3 or sides > 12:
            raise ValueError("sides must be between 3 and 12")

        space = get_model_space()

        r = radius if method == "circumscribed" else radius / math.cos(math.pi / sides)
        rot = math.radians(rotation_deg)
        pts = []
        for i in range(sides):
            angle = rot + 2 * math.pi * i / sides
            pts.extend([cx + r * math.cos(angle), cy + r * math.sin(angle)])
        pts.extend(pts[:2])  # close
        pl = _polyline(space, pts, closed=True)
        pl.Layer = layer

        # Circumscribed helper circle (construction line)
        circle = space.AddCircle(point(cx, cy), radius)
        circle.Layer = layer
        circle.Linetype = "CENTER"

        return {
            "sides": sides,
            "center": [cx, cy],
            "radius": radius,
            "method": method,
            "rotation_deg": rotation_deg,
            "polygon_handle": pl.Handle,
            "circle_handle": circle.Handle,
            "message": f"Regular {sides}-gon drawn at ({cx},{cy}), radius={radius}"
        }

    @mcp.tool()
    def draw_polygon_by_edge(
        x1: float, y1: float,
        x2: float, y2: float,
        sides: int,
        layer: str = "A-GEOM"
    ) -> dict:
        """
        Construct a regular polygon where one edge is defined by two points.
        Equivalent to the 'Edge' option in AutoCAD POLYGON command.
        Covers curriculum: Unit 4 — Platonic shapes by angle method.
        """
        if sides < 3:
            raise ValueError("sides must be >= 3")

        space = get_model_space()

        edge_len = math.hypot(x2 - x1, y2 - y1)
        edge_angle = math.atan2(y2 - y1, x2 - x1)
        r = edge_len / (2 * math.sin(math.pi / sides))

        cx = x1 + r * math.cos(edge_angle + math.pi / sides)
        cy = y1 + r * math.sin(edge_angle + math.pi / sides)

        rot = edge_angle - math.pi / sides
        pts = []
        for i in range(sides):
            a = rot + 2 * math.pi * i / sides
            pts.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
        pts.extend(pts[:2])
        pl = _polyline(space, pts, closed=True)
        pl.Layer = layer

        return {
            "sides": sides,
            "center": [cx, cy],
            "edge_length": round(edge_len, 3),
            "handle": pl.Handle,
            "message": f"Regular {sides}-gon by edge from ({x1},{y1}) to ({x2},{y2})"
        }

    # ------------------------------------------------------------------
    # ISOMETRIC GRID
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_isometric_grid(
        origin_x: float, origin_y: float,
        width: float, height: float,
        grid_spacing: float = 100.0,
        layer: str = "A-GRID"
    ) -> dict:
        """
        Draw an isometric grid (30°/90°/150° axes) as construction lines.
        Useful for setting up isometric projection drawings.
        Covers curriculum: Unit 6 — Isometric view of objects.
        """
        space = get_model_space()
        handles = []

        cols = int(width / grid_spacing) + 2
        rows = int(height / grid_spacing) + 2

        # Vertical lines
        for i in range(cols + 1):
            x = origin_x + i * grid_spacing
            ln = space.AddLine(point(x, origin_y), point(x, origin_y + height))
            ln.Layer = layer
            ln.Linetype = "DASHED"
            handles.append(ln.Handle)

        # 30° left lines
        angle30 = math.radians(30)
        dx = grid_spacing
        dy = grid_spacing * math.tan(angle30)
        for i in range(-rows, cols + rows):
            sx = origin_x + i * dx
            sy = origin_y
            ex = sx + cols * dx
            ey = sy + cols * dy
            ln = space.AddLine(point(sx, sy), point(ex, ey))
            ln.Layer = layer
            ln.Linetype = "DASHED"
            handles.append(ln.Handle)

        # 150° right lines (mirror of 30°)
        for i in range(-rows, cols + rows):
            sx = origin_x + (cols + rows) * dx - i * dx
            sy = origin_y
            ex = sx - cols * dx
            ey = sy + cols * dy
            ln = space.AddLine(point(sx, sy), point(ex, ey))
            ln.Layer = layer
            ln.Linetype = "DASHED"
            handles.append(ln.Handle)

        # Three primary axes
        for angle_deg in [90, 30, 150]:
            a = math.radians(angle_deg)
            ax = space.AddLine(
                point(origin_x, origin_y),
                point(origin_x + width * math.cos(a), origin_y + width * math.sin(a))
            )
            ax.Layer = layer
            handles.append(ax.Handle)

        return {
            "origin": [origin_x, origin_y],
            "grid_spacing": grid_spacing,
            "lines_drawn": len(handles),
            "message": f"Isometric grid drawn at ({origin_x},{origin_y}), {grid_spacing}mm spacing"
        }

    # ------------------------------------------------------------------
    # ORTHOGRAPHIC PROJECTION LAYOUT
    # ------------------------------------------------------------------

    @mcp.tool()
    def setup_orthographic_layout(
        origin_x: float, origin_y: float,
        view_width: float, view_height: float,
        gap: float = 50.0,
        include_side_view: bool = True,
        layer: str = "A-GEOM"
    ) -> dict:
        """
        Draw the standard three-view orthographic projection frame:
        top-left = Plan (top view), bottom-left = Front Elevation,
        bottom-right = Side Elevation (optional).
        Reference lines connect the views for projection.
        Covers curriculum: Unit 5 — Orthographic projection techniques.
        """
        space = get_model_space()

        W, H, G = view_width, view_height, gap
        ox, oy = origin_x, origin_y

        # Plan box (top-left)
        plan_pts = [ox, oy+G+H, ox+W, oy+G+H, ox+W, oy+G+H+H, ox, oy+G+H+H, ox, oy+G+H]
        plan = _polyline(space, plan_pts, closed=True)
        plan.Layer = layer

        # Front elevation box (bottom-left)
        front_pts = [ox, oy, ox+W, oy, ox+W, oy+H, ox, oy+H, ox, oy]
        front = _polyline(space, front_pts, closed=True)
        front.Layer = layer

        handles = {"plan": plan.Handle, "front_elevation": front.Handle}

        # Side elevation box (bottom-right)
        if include_side_view:
            side_pts = [ox+W+G, oy, ox+W+G+H, oy, ox+W+G+H, oy+H, ox+W+G, oy+H, ox+W+G, oy]
            side = _polyline(space, side_pts, closed=True)
            side.Layer = layer
            handles["side_elevation"] = side.Handle

        # Projection reference lines (dashed)
        ref_lines = [
            (ox+W/2, oy+G+H, ox+W/2, oy+H),        # vertical plan→front
            (ox+W, oy+H/2, ox+W+G, oy+H/2),          # horizontal front→side
        ]
        for (x1, y1, x2, y2) in ref_lines:
            ln = space.AddLine(point(x1, y1), point(x2, y2))
            ln.Layer = layer
            ln.Linetype = "DASHDOT"

        # Labels
        labels = [("PLAN", ox+W/2, oy+G+H+H+10),
                  ("FRONT ELEVATION", ox+W/2, oy+H+5),
                  ("SIDE ELEVATION", ox+W+G+H/2, oy+H+5)]
        for txt, tx, ty in labels:
            t = space.AddText(txt, point(tx, ty), 10)
            t.Layer = layer
            t.Alignment = 4  # middle center

        return {
            "origin": [origin_x, origin_y],
            "view_size": [view_width, view_height],
            "handles": handles,
            "message": "Orthographic 3-view layout created"
        }

    # ------------------------------------------------------------------
    # SECTION CUTS
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_section_cut_line(
        x1: float, y1: float,
        x2: float, y2: float,
        label: str = "A",
        tick_length: float = 300.0,
        layer: str = "A-ANNO-SECT"
    ) -> dict:
        """
        Draw a section cutting-plane line with end ticks and labels.
        Tick arrows indicate the viewing direction.
        Covers curriculum: Unit 4 (Analytical Drawing) — longitudinal & cross sections.
        """
        space = get_model_space()

        angle = math.atan2(y2 - y1, x2 - x1)
        perp = angle + math.pi / 2

        # Main cut line
        ln = space.AddLine(point(x1, y1), point(x2, y2))
        ln.Layer = layer
        ln.Linetype = "PHANTOM"

        # End ticks pointing in the viewing direction (perpendicular)
        handles = [ln.Handle]
        for px, py in [(x1, y1), (x2, y2)]:
            tx = px + tick_length * math.cos(perp)
            ty = py + tick_length * math.sin(perp)
            tick = space.AddLine(point(px, py), point(tx, ty))
            tick.Layer = layer
            handles.append(tick.Handle)

        # Labels at ends
        text_offset = tick_length * 1.3
        for px, py in [(x1, y1), (x2, y2)]:
            tx = px + text_offset * math.cos(perp)
            ty = py + text_offset * math.sin(perp)
            t = space.AddText(label, point(tx, ty), 250)
            t.Layer = layer
            handles.append(t.Handle)

        return {
            "start": [x1, y1],
            "end": [x2, y2],
            "label": label,
            "handles": handles,
            "message": f"Section cut line '{label}' drawn"
        }

    @mcp.tool()
    def hatch_section_cut(
        boundary_handle: str,
        material: str = "concrete",
        layer: str = "A-ANNO-SECT"
    ) -> dict:
        """
        Apply a standard architectural section hatch to a closed boundary.
        material options: 'concrete', 'brick', 'stone', 'insulation',
                          'wood', 'steel', 'earth', 'gravel'
        Covers curriculum: sections in plan & elevation.
        """
        doc = get_active_doc()
        space = get_model_space()

        material_hatches = {
            "concrete": ("AR-CONC", 1.0, 0),
            "brick":    ("AR-BRELM", 1.0, 0),
            "stone":    ("AR-RSHKE", 1.0, 0),
            "insulation": ("ESCHER", 0.5, 45),
            "wood":     ("AR-RROOF", 0.5, 0),
            "steel":    ("ANSI31", 1.0, 0),
            "earth":    ("EARTH", 1.0, 0),
            "gravel":   ("GRAVEL", 1.0, 0),
        }

        pattern, scale, angle = material_hatches.get(
            material.lower(), ("ANSI31", 1.0, 0)
        )

        outer = doc.HandleToObject(boundary_handle)
        hatch = space.AddHatch(0, pattern, True)
        hatch.PatternScale = scale
        hatch.PatternAngle = math.radians(angle)
        hatch.Layer = layer
        outer_loop = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [outer]
        )
        hatch.AppendOuterLoop(outer_loop)
        hatch.Evaluate()

        return {
            "material": material,
            "pattern": pattern,
            "hatch_handle": hatch.Handle,
            "message": f"Section hatch '{pattern}' applied for material '{material}'"
        }

    # ------------------------------------------------------------------
    # SCALE / PROPORTION
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_scale_comparison(
        origin_x: float, origin_y: float,
        object_length: float,
        scales: list = None,
        orientation: str = "horizontal",
        layer: str = "A-ANNO-DIMS"
    ) -> dict:
        """
        Draw the same object at multiple scales side-by-side for comparison.
        Useful for scale study assignments.
        scales: list of scale denominators, e.g. [1, 2, 5, 10, 20, 50]
        Covers curriculum: Unit 1 (Analytical Drawing) — enlargement & reduction of scale.
        """
        space = get_model_space()
        if scales is None:
            scales = [1, 2, 5, 10, 20, 50]

        gap = object_length * 0.3
        handles = []
        x, y = origin_x, origin_y

        for s in scales:
            scaled_len = object_length / s
            if orientation == "horizontal":
                pts = [x, y, x + scaled_len, y, x + scaled_len, y + scaled_len * 0.5, x, y + scaled_len * 0.5]
                pts.append(x); pts.append(y)
                x_next = x + scaled_len + gap
                lx, ly = x + scaled_len / 2, y - 30
            else:
                pts = [x, y, x + scaled_len * 0.5, y, x + scaled_len * 0.5, y + scaled_len, x, y + scaled_len]
                pts.append(x); pts.append(y)
                x_next = x
                lx, ly = x + scaled_len * 0.25, y - 30
                y += scaled_len + gap

            pl = _polyline(space, pts, closed=True)
            pl.Layer = layer
            handles.append(pl.Handle)

            label = f"1:{s}"
            t = space.AddText(label, point(lx, ly), max(scaled_len * 0.15, 8))
            t.Layer = layer
            t.Alignment = 4
            handles.append(t.Handle)

            if orientation == "horizontal":
                x = x_next

        return {
            "origin": [origin_x, origin_y],
            "object_length": object_length,
            "scales": scales,
            "objects_drawn": len(scales),
            "message": f"Scale comparison drawn at {scales}"
        }

    @mcp.tool()
    def draw_golden_ratio_rectangle(
        origin_x: float, origin_y: float,
        width: float,
        subdivisions: int = 5,
        show_spiral: bool = True,
        layer: str = "A-GEOM"
    ) -> dict:
        """
        Draw a golden ratio rectangle with internal subdivision squares
        and optionally a Fibonacci/golden spiral overlay.
        Covers curriculum: Fundamentals of Design I, Unit 6 — Scale and Proportion (Golden Ratio).
        """
        space = get_model_space()

        phi = (1 + math.sqrt(5)) / 2
        height = width / phi
        handles = []

        # Outer rectangle
        outer = _polyline(space,
            [origin_x, origin_y, origin_x+width, origin_y,
             origin_x+width, origin_y+height, origin_x, origin_y+height,
             origin_x, origin_y],
            closed=True)
        outer.Layer = layer
        handles.append(outer.Handle)

        # Internal golden subdivisions
        x, y, w, h = origin_x, origin_y, width, height
        for i in range(subdivisions):
            sq = min(w, h)
            direction = i % 4
            if direction == 0:   # square on left
                sq_pts = [x, y, x+sq, y, x+sq, y+h, x, y+h, x, y]
                arc_cx, arc_cy = x + sq, y
                arc_start, arc_end = 90, 180
                x += sq; w -= sq
            elif direction == 1: # square on top
                sq_pts = [x, y+h-sq, x+w, y+h-sq, x+w, y+h, x, y+h, x, y+h-sq]
                arc_cx, arc_cy = x, y + h - sq
                arc_start, arc_end = 0, 90
                h -= sq
            elif direction == 2: # square on right
                sq_pts = [x+w-sq, y, x+w, y, x+w, y+h, x+w-sq, y+h, x+w-sq, y]
                arc_cx, arc_cy = x + w - sq, y + h
                arc_start, arc_end = 270, 360
                w -= sq
            else:                # square on bottom
                sq_pts = [x, y, x+w, y, x+w, y+sq, x, y+sq, x, y]
                arc_cx, arc_cy = x + w, y + sq
                arc_start, arc_end = 180, 270
                y += sq; h -= sq

            sq_pl = _polyline(space, sq_pts, closed=True)
            sq_pl.Layer = layer
            sq_pl.Linetype = "DASHDOT"
            handles.append(sq_pl.Handle)

            if show_spiral:
                arc = space.AddArc(
                    point(arc_cx, arc_cy),
                    sq,
                    math.radians(arc_start),
                    math.radians(arc_end)
                )
                arc.Layer = layer
                handles.append(arc.Handle)

        return {
            "origin": [origin_x, origin_y],
            "width": width,
            "height": round(height, 3),
            "phi": round(phi, 6),
            "subdivisions": subdivisions,
            "handles": handles,
            "message": f"Golden ratio rectangle {width}x{round(height,1)} with {subdivisions} subdivisions"
        }

    # ------------------------------------------------------------------
    # PERSPECTIVE GRID SETUPS
    # ------------------------------------------------------------------

    @mcp.tool()
    def setup_one_point_perspective(
        origin_x: float, origin_y: float,
        horizon_height: float,
        vp_x: float,
        picture_plane_width: float = 3000.0,
        depth_lines: int = 8,
        layer: str = "A-PERSP"
    ) -> dict:
        """
        Set up a 1-point perspective grid with:
          • Horizon line (eye level)
          • Vanishing point (VP) on the horizon
          • Ground line (picture plane base)
          • Radiating depth lines from VP
        Covers curriculum: Analytical Drawing Unit 5 — perspective drawing.
        """
        space = get_model_space()
        handles = []

        # Ground line
        gl = space.AddLine(
            point(origin_x, origin_y),
            point(origin_x + picture_plane_width, origin_y)
        )
        gl.Layer = layer
        handles.append(gl.Handle)

        # Horizon line
        hl = space.AddLine(
            point(origin_x, origin_y + horizon_height),
            point(origin_x + picture_plane_width, origin_y + horizon_height)
        )
        hl.Layer = layer
        handles.append(hl.Handle)

        # Vanishing point marker
        vp_abs_x = origin_x + vp_x
        vp_y = origin_y + horizon_height
        cross_size = picture_plane_width * 0.01
        for dx, dy in [(-cross_size, 0), (cross_size, 0), (0, -cross_size), (0, cross_size)]:
            m = space.AddLine(point(vp_abs_x, vp_y), point(vp_abs_x + dx, vp_y + dy))
            m.Layer = layer
            handles.append(m.Handle)

        # Radiating lines to ground
        step = picture_plane_width / (depth_lines + 1)
        for i in range(1, depth_lines + 1):
            gx = origin_x + i * step
            ln = space.AddLine(point(vp_abs_x, vp_y), point(gx, origin_y))
            ln.Layer = layer
            ln.Linetype = "DASHED"
            handles.append(ln.Handle)

        # Labels
        for txt, tx, ty in [
            ("HORIZON LINE (EYE LEVEL)", origin_x + 10, vp_y + 20),
            ("GROUND LINE", origin_x + 10, origin_y - 25),
            ("VP", vp_abs_x + 10, vp_y + 30),
        ]:
            t = space.AddText(txt, point(tx, ty), 20)
            t.Layer = layer
            handles.append(t.Handle)

        return {
            "vanishing_point": [vp_abs_x, vp_y],
            "horizon_height": horizon_height,
            "depth_lines": depth_lines,
            "handles_count": len(handles),
            "message": f"1-point perspective grid set up (VP at x={vp_x} from origin)"
        }

    @mcp.tool()
    def setup_two_point_perspective(
        origin_x: float, origin_y: float,
        horizon_height: float,
        vp_left_x: float,
        vp_right_x: float,
        picture_plane_width: float = 5000.0,
        depth_lines: int = 6,
        layer: str = "A-PERSP"
    ) -> dict:
        """
        Set up a 2-point perspective grid with two vanishing points
        on the horizon line and radiating convergence lines.
        Covers curriculum: Analytical Drawing Unit 5 — 2-point perspective.
        """
        space = get_model_space()
        handles = []

        hl_y = origin_y + horizon_height

        # Horizon line
        hl = space.AddLine(
            point(origin_x + vp_left_x, hl_y),
            point(origin_x + vp_right_x, hl_y)
        )
        hl.Layer = layer
        handles.append(hl.Handle)

        # Ground line
        gl = space.AddLine(
            point(origin_x, origin_y),
            point(origin_x + picture_plane_width, origin_y)
        )
        gl.Layer = layer
        handles.append(gl.Handle)

        vp_l = (origin_x + vp_left_x, hl_y)
        vp_r = (origin_x + vp_right_x, hl_y)

        # VP markers
        cross = picture_plane_width * 0.008
        for vp in [vp_l, vp_r]:
            for dx, dy in [(-cross, 0), (cross, 0), (0, -cross), (0, cross)]:
                m = space.AddLine(point(vp[0], vp[1]), point(vp[0]+dx, vp[1]+dy))
                m.Layer = layer
                handles.append(m.Handle)

        # Convergence lines from each VP to evenly spaced ground points
        step = picture_plane_width / (depth_lines + 1)
        for i in range(1, depth_lines + 1):
            gx = origin_x + i * step
            for vp in [vp_l, vp_r]:
                ln = space.AddLine(point(vp[0], vp[1]), point(gx, origin_y))
                ln.Layer = layer
                ln.Linetype = "DASHED"
                handles.append(ln.Handle)

        # Labels
        for txt, tx, ty in [
            ("VP (LEFT)", vp_l[0] - 80, vp_l[1] + 30),
            ("VP (RIGHT)", vp_r[0] + 10, vp_r[1] + 30),
            ("HORIZON LINE", (vp_l[0] + vp_r[0]) / 2, hl_y + 20),
        ]:
            t = space.AddText(txt, point(tx, ty), 20)
            t.Layer = layer
            handles.append(t.Handle)

        return {
            "vp_left": list(vp_l),
            "vp_right": list(vp_r),
            "horizon_height": horizon_height,
            "message": "2-point perspective grid created"
        }

    # ------------------------------------------------------------------
    # SURFACE DEVELOPMENT
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_prism_surface_development(
        origin_x: float, origin_y: float,
        sides: int,
        edge_length: float,
        height: float,
        include_top_bottom: bool = True,
        layer: str = "A-GEOM"
    ) -> dict:
        """
        Draw the surface development (net / unfolding) of a regular prism.
        The net is laid flat showing all faces connected.
        Covers curriculum: Analytical Drawing Unit 2 — surface development.
        """
        space = get_model_space()
        handles = []

        # Lateral faces: `sides` rectangles placed side by side
        x = origin_x
        for i in range(sides):
            pts = [x, origin_y, x+edge_length, origin_y,
                   x+edge_length, origin_y+height, x, origin_y+height, x, origin_y]
            face = _polyline(space, pts, closed=True)
            face.Layer = layer
            handles.append(face.Handle)
            # fold line
            fl = space.AddLine(point(x+edge_length, origin_y), point(x+edge_length, origin_y+height))
            fl.Layer = layer
            fl.Linetype = "DASHED"
            handles.append(fl.Handle)
            x += edge_length

        if include_top_bottom:
            # Bottom polygon (centred below first face)
            r = edge_length / (2 * math.sin(math.pi / sides))
            for face_y_offset, label in [(origin_y - r*2 - 20, "BOTTOM"), (origin_y + height + 20, "TOP")]:
                cx = origin_x + edge_length * sides / 2
                cy = face_y_offset + r
                pts = []
                for j in range(sides):
                    a = 2 * math.pi * j / sides - math.pi / 2
                    pts.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
                pts.extend(pts[:2])
                poly = _polyline(space, pts, closed=True)
                poly.Layer = layer
                handles.append(poly.Handle)
                t = space.AddText(label, point(cx, cy), 15)
                t.Layer = layer
                handles.append(t.Handle)

        return {
            "sides": sides,
            "edge_length": edge_length,
            "height": height,
            "total_lateral_area": round(sides * edge_length * height, 2),
            "handles_count": len(handles),
            "message": f"Surface development of {sides}-sided prism (edge={edge_length}, H={height})"
        }

    @mcp.tool()
    def draw_pyramid_surface_development(
        origin_x: float, origin_y: float,
        sides: int,
        base_edge: float,
        slant_height: float,
        include_base: bool = True,
        layer: str = "A-GEOM"
    ) -> dict:
        """
        Draw the surface development (net) of a regular pyramid:
        triangular faces fanned out around the base polygon.
        Covers curriculum: Analytical Drawing Unit 2 — surface development of pyramids.
        """
        space = get_model_space()
        handles = []

        base_r = base_edge / (2 * math.sin(math.pi / sides))
        # Place base at centre of origin
        cx = origin_x + slant_height + base_r + 20
        cy = origin_y + slant_height + base_r + 20

        # Base polygon
        if include_base:
            pts = []
            for j in range(sides):
                a = 2 * math.pi * j / sides
                pts.extend([cx + base_r * math.cos(a), cy + base_r * math.sin(a)])
            pts.extend(pts[:2])
            base = _polyline(space, pts, closed=True)
            base.Layer = layer
            handles.append(base.Handle)

        # Triangular faces fanned around the base
        face_half_angle = math.asin(base_edge / (2 * slant_height))
        total_angle = 2 * math.pi * sides * face_half_angle

        apex_r = slant_height
        start_angle = -total_angle / 2

        for i in range(sides):
            a0 = start_angle + i * 2 * face_half_angle
            a1 = a0 + 2 * face_half_angle
            fx0 = cx + apex_r * math.cos(a0)
            fy0 = cy + apex_r * math.sin(a0)
            fx1 = cx + apex_r * math.cos(a1)
            fy1 = cy + apex_r * math.sin(a1)
            pts = [cx, cy, fx0, fy0, fx1, fy1, cx, cy]
            tri = _polyline(space, pts, closed=True)
            tri.Layer = layer
            handles.append(tri.Handle)

        # Apex point mark
        apex_mark = space.AddCircle(point(cx, cy), 10)
        apex_mark.Layer = layer
        handles.append(apex_mark.Handle)

        return {
            "sides": sides,
            "base_edge": base_edge,
            "slant_height": slant_height,
            "handles_count": len(handles),
            "message": f"Pyramid net ({sides} sides, base={base_edge}, slant={slant_height})"
        }
