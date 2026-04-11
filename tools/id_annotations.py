"""
tools/id_annotations.py
Interior design annotation tools:
elevation markers, section cuts, north arrows, scale bars,
revision clouds, material callouts, detail bubbles, grid lines.
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_active_doc, ensure_layer, ensure_standard_linetypes, point


def _circle(space, cx, cy, r, layer):
    obj = space.AddCircle(
        win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [cx, cy, 0.0]),
        float(r)
    )
    obj.Layer = layer
    return obj


def _line(space, x1, y1, x2, y2, layer):
    obj = space.AddLine(point(x1, y1), point(x2, y2))
    obj.Layer = layer
    return obj


def _text(space, x, y, text, height, layer, align=4):
    pt = win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y), 0.0]
    )
    txt = space.AddText(str(text), pt, float(height))
    txt.Layer = layer
    if align != 0:
        txt.Alignment = align
        txt.TextAlignmentPoint = pt
    return txt


def register_id_annotation_tools(mcp):

    # -----------------------------------------------------------------------
    # ELEVATION MARKERS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def add_elevation_marker(
        x: float, y: float,
        label: str,
        directions: list[str],
        radius: float = 300.0,
        text_height: float = 150.0,
        layer: str = "A-ELEV"
    ) -> dict:
        """
        Place an elevation reference marker (circle divided into quadrants).
        label: the elevation sheet reference (e.g. 'A', 'B').
        directions: list of active quadrant directions, e.g. ['north', 'east'].
        Quadrant labels: top=north, right=east, bottom=south, left=west.
        Active quadrants are filled (solid hatch); inactive are empty.
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        space = doc.ModelSpace
        handles = []

        outer = _circle(space, x, y, radius, layer)
        handles.append(outer.Handle)

        # Cross lines dividing circle into 4 quadrants
        h1 = _line(space, x - radius, y, x + radius, y, layer)
        h2 = _line(space, x, y - radius, x, y + radius, layer)
        handles += [h1.Handle, h2.Handle]

        dir_map = {"north": 90, "east": 0, "south": 270, "west": 180}
        for direction in directions:
            angle_deg = dir_map.get(direction.lower(), 0)
            # Fill wedge with hatch
            wedge_pts = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8,
                [x, y,
                 x + radius * math.cos(math.radians(angle_deg - 45)), y + radius * math.sin(math.radians(angle_deg - 45)),
                 x + radius * math.cos(math.radians(angle_deg + 45)), y + radius * math.sin(math.radians(angle_deg + 45)),
                 x, y]
            )
            wedge = space.AddLightWeightPolyline(wedge_pts)
            wedge.Closed = True
            wedge.Layer = layer
            try:
                hatch = space.AddHatch(0, "SOLID", True)
                outer_loop = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [wedge]
                )
                hatch.AppendOuterLoop(outer_loop)
                hatch.Evaluate()
                hatch.Layer = layer
                handles.append(hatch.Handle)
            except Exception:
                pass
            handles.append(wedge.Handle)

        # Label text in center
        t = _text(space, x, y, label, text_height * 1.2, layer)
        handles.append(t.Handle)
        doc.Regen(1)

        return {
            "handles": handles,
            "message": f"Elevation marker '{label}' at ({x},{y}), directions: {directions}"
        }

    @mcp.tool()
    def add_section_marker(
        x1: float, y1: float,
        x2: float, y2: float,
        label: str,
        bubble_radius: float = 250.0,
        text_height: float = 150.0,
        layer: str = "A-SECT"
    ) -> dict:
        """
        Draw a section cut line with bubbles at each end.
        label: section reference label (e.g. 'AA', '1').
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        ensure_standard_linetypes(doc)
        space = doc.ModelSpace
        handles = []

        # Section line (chain dotted)
        cut_line = _line(space, x1, y1, x2, y2, layer)
        try:
            cut_line.Linetype = "CENTER"
        except Exception:
            pass
        cut_line.Lineweight = 25
        handles.append(cut_line.Handle)

        # Bubbles at each end
        for px, py in [(x1, y1), (x2, y2)]:
            bubble = _circle(space, px, py, bubble_radius, layer)
            handles.append(bubble.Handle)
            t = _text(space, px, py, label, text_height, layer)
            handles.append(t.Handle)

        # Direction arrows (short perpendicular ticks)
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length > 0:
            nx = -dy / length * bubble_radius * 1.2
            ny = dx / length * bubble_radius * 1.2
            for px, py, sign in [(x1, y1, 1), (x2, y2, -1)]:
                arrow = _line(space, px, py, px + nx * sign, py + ny * sign, layer)
                handles.append(arrow.Handle)

        return {
            "handles": handles,
            "message": f"Section marker '{label}' from ({x1},{y1}) to ({x2},{y2})"
        }

    # -----------------------------------------------------------------------
    # DETAIL BUBBLES
    # -----------------------------------------------------------------------

    @mcp.tool()
    def add_detail_bubble(
        x: float, y: float,
        detail_ref: str,
        sheet_ref: str = "",
        radius: float = 200.0,
        text_height: float = 100.0,
        layer: str = "A-ANNO"
    ) -> dict:
        """
        Place a detail reference bubble (circle with detail no. and sheet ref).
        detail_ref: the detail number (e.g. '3').
        sheet_ref: the sheet where the detail is drawn (e.g. 'A301').
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        space = doc.ModelSpace
        handles = []

        bubble = _circle(space, x, y, radius, layer)
        handles.append(bubble.Handle)

        # Horizontal divider if sheet ref provided
        if sheet_ref:
            div = _line(space, x - radius, y, x + radius, y, layer)
            handles.append(div.Handle)
            t1 = _text(space, x, y + radius * 0.4, detail_ref, text_height, layer)
            t2 = _text(space, x, y - radius * 0.4, sheet_ref, text_height * 0.8, layer)
            handles += [t1.Handle, t2.Handle]
        else:
            t = _text(space, x, y, detail_ref, text_height * 1.2, layer)
            handles.append(t.Handle)

        return {
            "handles": handles,
            "message": f"Detail bubble '{detail_ref}/{sheet_ref}' at ({x},{y})"
        }

    # -----------------------------------------------------------------------
    # MATERIAL CALLOUTS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def add_material_callout(
        pointer_x: float, pointer_y: float,
        text_x: float, text_y: float,
        material_name: str,
        product_code: str = "",
        supplier: str = "",
        text_height: float = 150.0,
        layer: str = "A-ANNO-MATL"
    ) -> dict:
        """
        Add a material callout with leader arrow pointing to a surface.
        pointer_x/y: where the arrow points. text_x/y: where the text label sits.
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        space = doc.ModelSpace
        handles = []

        # Leader line
        leader_pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [pointer_x, pointer_y, 0.0, text_x, text_y, 0.0]
        )
        leader = space.AddLeader(leader_pts, None, 0)  # 0 = acAnnotationNone
        leader.Layer = layer
        handles.append(leader.Handle)

        # Arrowhead dot
        dot = _circle(space, pointer_x, pointer_y, text_height * 0.2, layer)
        handles.append(dot.Handle)

        # Text lines
        lines = [l for l in [material_name, product_code, supplier] if l]
        for i, line in enumerate(lines):
            ht = text_height if i == 0 else text_height * 0.8
            t = _text(space, text_x, text_y - i * text_height * 1.5, line, ht, layer, align=1)
            handles.append(t.Handle)

        return {
            "handles": handles,
            "message": f"Material callout '{material_name}' added"
        }

    # -----------------------------------------------------------------------
    # NORTH ARROW
    # -----------------------------------------------------------------------

    @mcp.tool()
    def add_north_arrow(
        x: float, y: float,
        size: float = 500.0,
        north_rotation_deg: float = 0.0,
        layer: str = "A-ANNO"
    ) -> dict:
        """
        Draw a north arrow symbol.
        north_rotation_deg: 0 = north is up. Rotate to match drawing orientation.
        size: overall height of the symbol.
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        space = doc.ModelSpace
        handles = []
        angle = math.radians(north_rotation_deg)

        # Arrow shaft
        tip_x = x + size * math.sin(angle)
        tip_y = y + size * math.cos(angle)
        shaft = _line(space, x, y, tip_x, tip_y, layer)
        handles.append(shaft.Handle)

        # Arrowhead (filled triangle)
        perp_x = math.cos(angle) * size * 0.12
        perp_y = -math.sin(angle) * size * 0.12
        base_x = x + (size * 0.7) * math.sin(angle)
        base_y = y + (size * 0.7) * math.cos(angle)
        arrow_pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [tip_x, tip_y,
             base_x + perp_x, base_y + perp_y,
             base_x - perp_x, base_y - perp_y,
             tip_x, tip_y]
        )
        arrowhead = space.AddLightWeightPolyline(arrow_pts)
        arrowhead.Closed = True
        arrowhead.Layer = layer
        try:
            hatch = space.AddHatch(0, "SOLID", True)
            outer = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [arrowhead]
            )
            hatch.AppendOuterLoop(outer)
            hatch.Evaluate()
            hatch.Layer = layer
            handles.append(hatch.Handle)
        except Exception:
            pass
        handles.append(arrowhead.Handle)

        # 'N' label
        label_x = x + (size * 1.2) * math.sin(angle)
        label_y = y + (size * 1.2) * math.cos(angle)
        t = _text(space, label_x, label_y, "N", size * 0.3, layer)
        handles.append(t.Handle)

        doc.Regen(1)
        return {
            "handles": handles,
            "message": f"North arrow placed at ({x},{y}), rotated {north_rotation_deg}°"
        }

    # -----------------------------------------------------------------------
    # SCALE BAR
    # -----------------------------------------------------------------------

    @mcp.tool()
    def add_scale_bar(
        x: float, y: float,
        scale: int = 50,
        num_segments: int = 5,
        segment_length_mm_on_paper: float = 20.0,
        bar_height: float = 100.0,
        layer: str = "A-ANNO"
    ) -> dict:
        """
        Draw a graphic scale bar.
        scale: drawing scale denominator (e.g. 50 for 1:50).
        num_segments: number of divisions on the bar.
        segment_length_mm_on_paper: how long each segment is on the printed sheet in mm.
        Each segment represents (segment_length_mm_on_paper × scale) mm in reality.
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        space = doc.ModelSpace
        handles = []

        real_per_segment = segment_length_mm_on_paper * scale
        seg_w = real_per_segment
        total_w = seg_w * num_segments

        # Alternating filled/empty segments
        for i in range(num_segments):
            seg_x = x + i * seg_w
            pts = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8,
                [seg_x, y,
                 seg_x + seg_w, y,
                 seg_x + seg_w, y - bar_height,
                 seg_x, y - bar_height,
                 seg_x, y]
            )
            box = space.AddLightWeightPolyline(pts)
            box.Closed = True
            box.Layer = layer
            handles.append(box.Handle)

            if i % 2 == 0:
                try:
                    hatch = space.AddHatch(0, "SOLID", True)
                    outer = win32com.client.VARIANT(
                        pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [box]
                    )
                    hatch.AppendOuterLoop(outer)
                    hatch.Evaluate()
                    hatch.Layer = layer
                    handles.append(hatch.Handle)
                except Exception:
                    pass

        # Tick marks and labels
        text_h = bar_height * 0.8
        for i in range(num_segments + 1):
            tick_x = x + i * seg_w
            tick = _line(space, tick_x, y, tick_x, y + bar_height * 0.5, layer)
            handles.append(tick.Handle)
            real_val = i * real_per_segment
            label = f"{int(real_val / 1000)}m" if real_val >= 1000 else f"{int(real_val)}mm"
            t = _text(space, tick_x, y + bar_height * 0.6, label, text_h, layer, align=4)
            handles.append(t.Handle)

        # Scale label
        scale_t = _text(space, x + total_w / 2, y - bar_height * 1.8,
                        f"Scale 1:{scale}", text_h * 1.1, layer)
        handles.append(scale_t.Handle)

        return {
            "handles": handles,
            "total_width": total_w,
            "real_length_per_segment": real_per_segment,
            "message": f"Scale bar 1:{scale} placed at ({x},{y})"
        }

    # -----------------------------------------------------------------------
    # REVISION CLOUD
    # -----------------------------------------------------------------------

    @mcp.tool()
    def add_revision_cloud(
        x1: float, y1: float,
        x2: float, y2: float,
        arc_length: float = 300.0,
        revision_label: str = "",
        layer: str = "A-ANNO"
    ) -> dict:
        """
        Draw a revision cloud around a rectangular area.
        x1,y1 to x2,y2 define the bounding rectangle.
        arc_length: approximate length of each cloud arc bump.
        revision_label: optional letter/number placed near the cloud.
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        space = doc.ModelSpace
        handles = []

        perimeter_pts = [
            (x1, y1, x2, y1),  # bottom
            (x2, y1, x2, y2),  # right
            (x2, y2, x1, y2),  # top
            (x1, y2, x1, y1),  # left
        ]

        for sx, sy, ex, ey in perimeter_pts:
            seg_len = math.hypot(ex - sx, ey - sy)
            num_arcs = max(2, round(seg_len / arc_length))
            arc_r = seg_len / num_arcs / 2

            for i in range(num_arcs):
                t1 = (i + 0.5) / num_arcs
                mid_x = sx + (ex - sx) * t1
                mid_y = sy + (ey - sy) * t1
                # Direction angle
                dir_angle = math.atan2(ey - sy, ex - sx)
                perp_angle = dir_angle + math.pi / 2
                # Arc center slightly inside
                center_x = mid_x - arc_r * math.cos(perp_angle) * 0.5
                center_y = mid_y - arc_r * math.sin(perp_angle) * 0.5
                arc_start_angle = dir_angle + math.pi
                arc_end_angle = dir_angle

                try:
                    arc = space.AddArc(
                        point(center_x, center_y),
                        arc_r,
                        arc_start_angle, arc_end_angle + math.pi
                    )
                    arc.Layer = layer
                    handles.append(arc.Handle)
                except Exception:
                    pass

        if revision_label:
            t = _text(space, x2 + arc_length, y2, revision_label,
                      arc_length * 0.8, layer)
            handles.append(t.Handle)

        return {
            "handles": handles,
            "message": f"Revision cloud around ({x1},{y1})–({x2},{y2})" +
                       (f", label='{revision_label}'" if revision_label else "")
        }

    # -----------------------------------------------------------------------
    # GRID LINES
    # -----------------------------------------------------------------------

    @mcp.tool()
    def add_grid_lines(
        origin_x: float, origin_y: float,
        x_spacings: list[float],
        y_spacings: list[float],
        extension: float = 1000.0,
        bubble_radius: float = 300.0,
        text_height: float = 200.0,
        layer: str = "A-GRID"
    ) -> dict:
        """
        Draw architectural grid lines with bubbles.
        x_spacings: list of spacings between vertical grid lines (e.g. [3000, 3000, 4000]).
        y_spacings: list of spacings between horizontal grid lines.
        Vertical lines are labelled A, B, C... Horizontal lines are labelled 1, 2, 3...
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        ensure_standard_linetypes(doc)
        space = doc.ModelSpace
        handles = []

        # Calculate grid extent
        total_x = sum(x_spacings)
        total_y = sum(y_spacings)

        # Vertical grid lines (columns)
        cum_x = origin_x
        x_positions = [cum_x]
        for sp in x_spacings:
            cum_x += sp
            x_positions.append(cum_x)

        # Horizontal grid lines (rows)
        cum_y = origin_y
        y_positions = [cum_y]
        for sp in y_spacings:
            cum_y += sp
            y_positions.append(cum_y)

        for i, gx in enumerate(x_positions):
            # Grid line
            ln = _line(space, gx, origin_y - extension, gx, origin_y + total_y + extension, layer)
            try:
                ln.Linetype = "CENTER"
            except Exception:
                pass
            handles.append(ln.Handle)

            # Bubbles top and bottom
            label = chr(65 + i)  # A, B, C...
            for gy, offset in [(origin_y - extension, -1), (origin_y + total_y + extension, 1)]:
                bubble_y = gy + offset * bubble_radius
                b = _circle(space, gx, bubble_y, bubble_radius, layer)
                t = _text(space, gx, bubble_y, label, text_height, layer)
                handles += [b.Handle, t.Handle]

        for i, gy in enumerate(y_positions):
            ln = _line(space, origin_x - extension, gy, origin_x + total_x + extension, gy, layer)
            try:
                ln.Linetype = "CENTER"
            except Exception:
                pass
            handles.append(ln.Handle)

            label = str(i + 1)  # 1, 2, 3...
            for gx, offset in [(origin_x - extension, -1), (origin_x + total_x + extension, 1)]:
                bubble_x = gx + offset * bubble_radius
                b = _circle(space, bubble_x, gy, bubble_radius, layer)
                t = _text(space, bubble_x, gy, label, text_height, layer)
                handles += [b.Handle, t.Handle]

        return {
            "handles": handles,
            "columns": len(x_positions),
            "rows": len(y_positions),
            "message": f"Grid {len(x_positions)} cols × {len(y_positions)} rows at ({origin_x},{origin_y})"
        }

    # -----------------------------------------------------------------------
    # DIMENSION CHAIN
    # -----------------------------------------------------------------------

    @mcp.tool()
    def add_dimension_chain(
        points: list[float],
        offset: float = 500.0,
        axis: str = "horizontal",
        layer: str = "A-DIMS"
    ) -> dict:
        """
        Draw a chain of consecutive dimensions along a line of points.
        points: list of X coordinates (for horizontal) or Y coordinates (for vertical).
        offset: distance the dimension line is placed from the geometry.
        axis: 'horizontal' or 'vertical'.
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        space = doc.ModelSpace
        handles = []

        if len(points) < 2:
            raise ValueError("Need at least 2 points for a dimension chain")

        for i in range(len(points) - 1):
            if axis == "horizontal":
                x1, x2 = points[i], points[i + 1]
                y_ref = 0.0
                dim = space.AddDimAligned(
                    point(x1, y_ref),
                    point(x2, y_ref),
                    point(x1 + (x2 - x1) / 2, y_ref - offset)
                )
            else:
                y1, y2 = points[i], points[i + 1]
                x_ref = 0.0
                dim = space.AddDimAligned(
                    point(x_ref, y1),
                    point(x_ref, y2),
                    point(x_ref - offset, y1 + (y2 - y1) / 2)
                )
            dim.Layer = layer
            handles.append(dim.Handle)

        return {
            "handles": handles,
            "count": len(handles),
            "message": f"{axis.title()} dimension chain with {len(handles)} dims"
        }
