"""
tools/interior_advanced.py
Advanced interior design tools:
  - Ceiling plans (reflected ceiling plans, coffers, bulkheads)
  - Wall elevations
  - Space planning (full room layouts from a brief)
  - Irregular / L-shaped / custom rooms
  - Lighting layout calculations
  - Skirting, cornice, dado rails
  - Floor tile layout with grout lines
  - Staircase symbols
  - Kitchen layout workflows
  - Bathroom layout workflows
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_active_doc, point


def _rect(space, x, y, w, h, layer, lw=18):
    pts = win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8,
        [x, y, 0, x + w, y, 0, x + w, y + h, 0, x, y + h, 0, x, y, 0]
    )
    obj = space.AddLightWeightPolyline(pts)
    obj.Closed = True
    obj.Layer = layer
    obj.Lineweight = lw
    return obj


def _line(space, x1, y1, x2, y2, layer, lw=18):
    obj = space.AddLine(point(x1, y1), point(x2, y2))
    obj.Layer = layer
    obj.Lineweight = lw
    return obj


def _circle(space, cx, cy, r, layer):
    obj = space.AddCircle(
        win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [cx, cy, 0.0]),
        float(r)
    )
    obj.Layer = layer
    return obj


def _text(space, x, y, text, height, layer, align=4):
    pt = win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y), 0.0]
    )
    txt = space.AddText(str(text), pt, float(height))
    txt.Layer = layer
    if align:
        txt.Alignment = align
        txt.TextAlignmentPoint = pt
    return txt


def register_interior_advanced_tools(mcp):

    # -----------------------------------------------------------------------
    # IRREGULAR / L-SHAPED ROOMS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def draw_l_shaped_room(
        x: float, y: float,
        total_width: float, total_depth: float,
        notch_width: float, notch_depth: float,
        wall_thickness: float = 150.0,
        name: str = "",
        layer: str = "A-WALL"
    ) -> dict:
        """
        Draw an L-shaped room. The notch is cut from the top-right corner.
        x,y: bottom-left of overall bounding box.
        total_width/depth: overall dimensions.
        notch_width/depth: size of the rectangular notch cut from the top-right.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        t = wall_thickness

        # L-shape outline (internal)
        inner_pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x, y, 0,
             x + total_width, y, 0,
             x + total_width, y + total_depth - notch_depth, 0,
             x + total_width - notch_width, y + total_depth - notch_depth, 0,
             x + total_width - notch_width, y + total_depth, 0,
             x, y + total_depth, 0,
             x, y, 0]
        )
        inner = space.AddLightWeightPolyline(inner_pts)
        inner.Closed = True
        inner.Layer = layer
        inner.Lineweight = 35

        # Outer wall outline
        outer_pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x - t, y - t, 0,
             x + total_width + t, y - t, 0,
             x + total_width + t, y + total_depth - notch_depth, 0,
             x + total_width - notch_width, y + total_depth - notch_depth, 0,
             x + total_width - notch_width, y + total_depth + t, 0,
             x - t, y + total_depth + t, 0,
             x - t, y - t, 0]
        )
        outer = space.AddLightWeightPolyline(outer_pts)
        outer.Closed = True
        outer.Layer = layer
        outer.Lineweight = 35

        # Hatch wall region
        try:
            hatch = space.AddHatch(0, "SOLID", True)
            outer_loop = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [outer]
            )
            hatch.AppendOuterLoop(outer_loop)
            inner_loop = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [inner]
            )
            hatch.AppendInnerLoop(inner_loop)
            hatch.Evaluate()
            hatch.Layer = "A-WALL-PATT"
        except Exception:
            pass

        area_m2 = ((total_width * total_depth) - (notch_width * notch_depth)) / 1e6
        handles = [outer.Handle, inner.Handle]

        if name:
            cx = x + (total_width - notch_width / 2) / 2
            cy = y + total_depth / 2
            t_obj = _text(space, cx, cy, name, total_depth * 0.04, "A-ANNO-ROOM")
            handles.append(t_obj.Handle)

        doc.Regen(1)
        return {
            "handles": handles,
            "total_width": total_width, "total_depth": total_depth,
            "area_m2": round(area_m2, 2),
            "message": f"L-shaped room '{name}' {total_width}×{total_depth}mm, area={area_m2:.2f}m²"
        }

    @mcp.tool()
    def draw_custom_room(
        points_flat: list[float],
        wall_thickness: float = 150.0,
        name: str = "",
        layer: str = "A-WALL"
    ) -> dict:
        """
        Draw a room from a custom polygon. points_flat is a flat list of XY pairs
        defining the internal room boundary (clockwise or counter-clockwise).
        Minimum 3 points. Wall thickness is extruded outward.
        """
        doc = get_active_doc()
        space = doc.ModelSpace

        if len(points_flat) < 6 or len(points_flat) % 2 != 0:
            raise ValueError("points_flat must be an even list of at least 6 values (3 XY pairs)")

        # Close polygon
        flat = list(points_flat)
        if flat[:2] != flat[-2:]:
            flat += flat[:2]

        inner = space.AddLightWeightPolyline(
            win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, flat)
        )
        inner.Closed = True
        inner.Layer = layer
        inner.Lineweight = 35

        # Calculate area using shoelace formula
        coords = list(zip(flat[::2], flat[1::2]))
        n = len(coords)
        area_mm2 = abs(sum(
            coords[i][0] * coords[(i + 1) % n][1] - coords[(i + 1) % n][0] * coords[i][1]
            for i in range(n)
        )) / 2
        area_m2 = area_mm2 / 1e6

        cx = sum(c[0] for c in coords) / n
        cy = sum(c[1] for c in coords) / n

        handles = [inner.Handle]
        if name:
            t = _text(space, cx, cy, name, area_mm2 ** 0.5 * 0.05, "A-ANNO-ROOM")
            handles.append(t.Handle)

        doc.Regen(1)
        return {
            "handles": handles,
            "area_m2": round(area_m2, 2),
            "centroid": [round(cx, 1), round(cy, 1)],
            "message": f"Custom room '{name}' drawn, area={area_m2:.2f}m²"
        }

    # -----------------------------------------------------------------------
    # CEILING PLANS (RCP — Reflected Ceiling Plan)
    # -----------------------------------------------------------------------

    @mcp.tool()
    def draw_rcp_room(
        x: float, y: float,
        width: float, depth: float,
        ceiling_height: float = 2700.0,
        layer: str = "A-CLNG"
    ) -> dict:
        """
        Draw a reflected ceiling plan (RCP) boundary for a room.
        Includes the ceiling perimeter and a note of the ceiling height.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        ceiling = _rect(space, x, y, width, depth, layer, 25)
        handles.append(ceiling.Handle)

        ht = _text(space, x + width / 2, y + depth / 2,
                   f"CH = {ceiling_height:.0f}", min(width, depth) * 0.04, layer)
        handles.append(ht.Handle)

        return {
            "handles": handles,
            "message": f"RCP boundary {width}×{depth}mm, ceiling height={ceiling_height}mm"
        }

    @mcp.tool()
    def draw_coffer(
        x: float, y: float,
        width: float, depth: float,
        border: float = 300.0,
        layer: str = "A-CLNG"
    ) -> dict:
        """
        Draw a coffered ceiling element (outer rectangle + inner rectangle).
        x,y: bottom-left. border: width of the coffer frame.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        outer = _rect(space, x, y, width, depth, layer, 25)
        inner = _rect(space, x + border, y + border,
                      width - 2 * border, depth - 2 * border, layer, 18)
        handles += [outer.Handle, inner.Handle]

        return {
            "handles": handles,
            "message": f"Coffer {width}×{depth}mm with {border}mm border"
        }

    @mcp.tool()
    def draw_bulkhead(
        x1: float, y1: float,
        x2: float, y2: float,
        depth: float = 400.0,
        layer: str = "A-CLNG"
    ) -> dict:
        """
        Draw a ceiling bulkhead (dropped section) as a rectangle.
        The bulkhead runs along the wall from (x1,y1) to (x2,y2) and drops inward by depth.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        nx = -dy / length * depth
        ny = dx / length * depth

        pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x1, y1, 0,
             x2, y2, 0,
             x2 + nx, y2 + ny, 0,
             x1 + nx, y1 + ny, 0,
             x1, y1, 0]
        )
        bulkhead = space.AddLightWeightPolyline(pts)
        bulkhead.Closed = True
        bulkhead.Layer = layer
        bulkhead.Lineweight = 25

        try:
            hatch = space.AddHatch(0, "ANSI31", True)
            outer = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [bulkhead]
            )
            hatch.AppendOuterLoop(outer)
            hatch.PatternScale = 0.5
            hatch.Evaluate()
            hatch.Layer = layer
            handles.append(hatch.Handle)
        except Exception:
            pass
        handles.append(bulkhead.Handle)

        return {
            "handles": handles,
            "message": f"Bulkhead {length:.0f}mm long × {depth}mm deep"
        }

    @mcp.tool()
    def calculate_downlight_layout(
        room_width: float, room_depth: float,
        ceiling_height: float = 2700.0,
        light_type: str = "downlight",
        spacing_multiplier: float = 1.0
    ) -> dict:
        """
        Calculate recommended downlight positions for a room using
        the standard rule: spacing = ceiling_height × 0.9–1.0,
        with first light at half the spacing from the wall.

        Returns a list of (x,y) positions relative to room bottom-left.
        spacing_multiplier: adjust tighter (0.8) or looser (1.2) spacing.
        """
        spacing = ceiling_height * 0.9 * spacing_multiplier

        cols = max(1, round(room_width / spacing))
        rows = max(1, round(room_depth / spacing))

        col_spacing = room_width / cols
        row_spacing = room_depth / rows

        positions = []
        for row in range(rows):
            for col in range(cols):
                px = col_spacing * (col + 0.5)
                py = row_spacing * (row + 0.5)
                positions.append([round(px, 1), round(py, 1)])

        return {
            "positions": positions,
            "count": len(positions),
            "cols": cols,
            "rows": rows,
            "col_spacing_mm": round(col_spacing, 1),
            "row_spacing_mm": round(row_spacing, 1),
            "recommended_spacing_mm": round(spacing, 1),
            "note": f"Based on ceiling height {ceiling_height}mm. Positions relative to room bottom-left."
        }

    @mcp.tool()
    def draw_downlight_layout(
        x: float, y: float,
        room_width: float, room_depth: float,
        ceiling_height: float = 2700.0,
        downlight_radius: float = 75.0,
        spacing_multiplier: float = 1.0,
        layer: str = "E-LITE"
    ) -> dict:
        """
        Calculate and draw all downlights for a room automatically.
        x,y: room bottom-left corner in model space.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        spacing = ceiling_height * 0.9 * spacing_multiplier
        cols = max(1, round(room_width / spacing))
        rows = max(1, round(room_depth / spacing))
        col_spacing = room_width / cols
        row_spacing = room_depth / rows

        for row in range(rows):
            for col in range(cols):
                cx = x + col_spacing * (col + 0.5)
                cy = y + row_spacing * (row + 0.5)

                c = _circle(space, cx, cy, downlight_radius, layer)
                h1 = _line(space, cx - downlight_radius, cy, cx + downlight_radius, cy, layer)
                h2 = _line(space, cx, cy - downlight_radius, cx, cy + downlight_radius, layer)
                handles += [c.Handle, h1.Handle, h2.Handle]

        return {
            "handles": handles,
            "count": cols * rows,
            "message": f"{cols * rows} downlights placed ({cols}×{rows} grid)"
        }

    # -----------------------------------------------------------------------
    # WALL ELEVATIONS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def draw_wall_elevation(
        x: float, y: float,
        wall_width: float,
        floor_to_ceiling: float = 2700.0,
        floor_to_top_of_baseboard: float = 100.0,
        floor_to_dado: float = 0.0,
        floor_to_cornice: float = 0.0,
        room_name: str = "",
        wall_label: str = "",
        layer: str = "A-ANNO"
    ) -> dict:
        """
        Draw a schematic wall elevation with optional dado rail and cornice lines.
        x,y: bottom-left of elevation. wall_width, floor_to_ceiling in mm.
        floor_to_dado: height of dado rail (0 = omit).
        floor_to_cornice: height of cornice (0 = use ceiling - 100).
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        # Main elevation outline
        outline = _rect(space, x, y, wall_width, floor_to_ceiling, layer, 35)
        handles.append(outline.Handle)

        # Floor line (baseboard top)
        if floor_to_baseboard := floor_to_top_of_baseboard:
            fl = _line(space, x, y + floor_to_baseboard, x + wall_width, y + floor_to_baseboard, layer)
            handles.append(fl.Handle)

        # Dado rail
        if floor_to_dado > 0:
            dado = _line(space, x, y + floor_to_dado, x + wall_width, y + floor_to_dado, layer)
            dado.Lineweight = 25
            handles.append(dado.Handle)

        # Cornice line
        cornice_h = floor_to_cornice if floor_to_cornice > 0 else floor_to_ceiling - 100
        cornice = _line(space, x, y + cornice_h, x + wall_width, y + cornice_h, layer)
        cornice.Lineweight = 25
        handles.append(cornice.Handle)

        # Labels
        if wall_label:
            lbl = _text(space, x + wall_width / 2, y - floor_to_ceiling * 0.08,
                        wall_label, floor_to_ceiling * 0.04, layer)
            handles.append(lbl.Handle)

        # Dimension: ceiling height
        dim = space.AddDimAligned(
            [x - wall_width * 0.12, y, 0.0],
            [x - wall_width * 0.12, y + floor_to_ceiling, 0.0],
            [x - wall_width * 0.18, y + floor_to_ceiling / 2, 0.0]
        )
        dim.Layer = "A-DIMS"
        handles.append(dim.Handle)

        # Dimension: wall width
        dim2 = space.AddDimAligned(
            [x, y - floor_to_ceiling * 0.08, 0.0],
            [x + wall_width, y - floor_to_ceiling * 0.08, 0.0],
            [x + wall_width / 2, y - floor_to_ceiling * 0.14, 0.0]
        )
        dim2.Layer = "A-DIMS"
        handles.append(dim2.Handle)

        return {
            "handles": handles,
            "wall_width": wall_width,
            "floor_to_ceiling": floor_to_ceiling,
            "message": f"Wall elevation '{wall_label}' drawn {wall_width}×{floor_to_ceiling}mm"
        }

    @mcp.tool()
    def add_window_to_elevation(
        elevation_x: float, elevation_y: float,
        window_x: float,
        sill_height: float = 900.0,
        window_width: float = 1200.0,
        window_height: float = 1100.0,
        layer: str = "A-GLAZ"
    ) -> dict:
        """
        Add a window opening to a wall elevation drawing.
        elevation_x,y: bottom-left of the parent elevation.
        window_x: distance from left edge of elevation to window centerline.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        wx = elevation_x + window_x - window_width / 2
        wy = elevation_y + sill_height

        # Window frame
        frame = _rect(space, wx, wy, window_width, window_height, layer, 25)
        handles.append(frame.Handle)

        # Glazing bar (cross)
        mid_h = _line(space, wx, wy + window_height / 2,
                      wx + window_width, wy + window_height / 2, layer)
        mid_v = _line(space, wx + window_width / 2, wy,
                      wx + window_width / 2, wy + window_height, layer)
        handles += [mid_h.Handle, mid_v.Handle]

        # Sill line
        sill = _line(space, wx - window_width * 0.1, wy,
                     wx + window_width * 1.1, wy, layer)
        sill.Lineweight = 35
        handles.append(sill.Handle)

        # Dimension
        dim = space.AddDimAligned(
            [wx, elevation_y, 0.0],
            [wx, wy, 0.0],
            [wx - window_width * 0.3, elevation_y + sill_height / 2, 0.0]
        )
        dim.Layer = "A-DIMS"
        handles.append(dim.Handle)

        return {
            "handles": handles,
            "message": f"Window {window_width}×{window_height}mm at sill height {sill_height}mm added to elevation"
        }

    # -----------------------------------------------------------------------
    # FLOOR TILE LAYOUT
    # -----------------------------------------------------------------------

    @mcp.tool()
    def draw_tile_layout(
        x: float, y: float,
        room_width: float, room_depth: float,
        tile_width: float = 600.0,
        tile_depth: float = 600.0,
        grout_width: float = 3.0,
        pattern: str = "grid",
        start_x: float = 0.0,
        start_y: float = 0.0,
        layer: str = "A-FLOR-PATT"
    ) -> dict:
        """
        Draw a floor tile layout within a room boundary.
        pattern: 'grid', 'offset' (brick bond), 'diagonal' (45°).
        start_x/y: offset the tile grid origin within the room.
        grout_width: grout line width in mm.
        Returns total tile count and cut tile info.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []
        total_tiles = 0
        cut_tiles = 0

        pitch_x = tile_width + grout_width
        pitch_y = tile_depth + grout_width

        if pattern == "diagonal":
            doc.SendCommand(f"_SNAP\nR\n{x},{y}\n45\n")

        cols = math.ceil(room_width / pitch_x) + 1
        rows = math.ceil(room_depth / pitch_y) + 1

        for row in range(rows):
            for col in range(cols):
                if pattern == "offset" and row % 2 == 1:
                    tx = x + start_x + col * pitch_x + pitch_x / 2
                else:
                    tx = x + start_x + col * pitch_x

                ty = y + start_y + row * pitch_y

                # Clip to room boundary
                if tx >= x + room_width or ty >= y + room_depth:
                    continue
                if tx < x:
                    tx = x
                    cut_tiles += 1
                if ty < y:
                    ty = y
                    cut_tiles += 1
                actual_w = min(tile_width, x + room_width - tx)
                actual_h = min(tile_depth, y + room_depth - ty)

                tile = _rect(space, tx, ty, actual_w, actual_h, layer, 9)
                handles.append(tile.Handle)
                total_tiles += 1

        doc.Regen(1)
        return {
            "handles_count": len(handles),
            "total_tiles_drawn": total_tiles,
            "estimated_cut_tiles": cut_tiles,
            "tile_size": f"{tile_width}×{tile_depth}mm",
            "pattern": pattern,
            "message": f"Tile layout drawn: {total_tiles} tiles, ~{cut_tiles} cuts"
        }

    # -----------------------------------------------------------------------
    # SKIRTING, CORNICE, DADO RAILS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def draw_skirting_boards(
        room_x: float, room_y: float,
        room_width: float, room_depth: float,
        height: float = 100.0,
        thickness: float = 18.0,
        door_openings: list[dict] = None,
        layer: str = "A-FURN-FIXD"
    ) -> dict:
        """
        Draw skirting board lines around the perimeter of a room.
        door_openings: list of dicts with 'wall' ('bottom','top','left','right'),
                       'offset' (distance from left/bottom of wall), 'width'.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []
        openings = door_openings or []

        def wall_has_opening(wall, pos):
            for op in openings:
                if op.get("wall") == wall:
                    off = op.get("offset", 0)
                    w = op.get("width", 0)
                    if off <= pos <= off + w:
                        return True
            return False

        walls = [
            ("bottom", room_x, room_y, room_x + room_width, room_y, False),
            ("top",    room_x, room_y + room_depth, room_x + room_width, room_y + room_depth, False),
            ("left",   room_x, room_y, room_x, room_y + room_depth, True),
            ("right",  room_x + room_width, room_y, room_x + room_width, room_y + room_depth, True),
        ]

        for wall_id, sx, sy, ex, ey, is_vertical in walls:
            length = math.hypot(ex - sx, ey - sy)
            segments = []
            current_start = 0.0
            step = length / 100
            in_opening = False

            for i in range(101):
                pos = i * step
                opening_here = wall_has_opening(wall_id, pos)
                if opening_here and not in_opening:
                    if pos > current_start:
                        segments.append((current_start, pos))
                    in_opening = True
                elif not opening_here and in_opening:
                    current_start = pos
                    in_opening = False
            if not in_opening:
                segments.append((current_start, length))

            for seg_start, seg_end in segments:
                t_s = seg_start / length
                t_e = seg_end / length
                lx1 = sx + (ex - sx) * t_s
                ly1 = sy + (ey - sy) * t_s
                lx2 = sx + (ex - sx) * t_e
                ly2 = sy + (ey - sy) * t_e
                ln = _line(space, lx1, ly1, lx2, ly2, layer, 18)
                handles.append(ln.Handle)

        perimeter = 2 * (room_width + room_depth) / 1000
        total_opening_w = sum(op.get("width", 0) for op in openings) / 1000
        net_m = perimeter - total_opening_w

        return {
            "handles": handles,
            "perimeter_m": round(perimeter, 2),
            "net_skirting_m": round(net_m, 2),
            "message": f"Skirting boards drawn, net length ≈ {net_m:.2f}m"
        }

    # -----------------------------------------------------------------------
    # STAIRCASE
    # -----------------------------------------------------------------------

    @mcp.tool()
    def draw_staircase(
        x: float, y: float,
        width: float = 1000.0,
        total_rise: float = 3000.0,
        num_steps: int = 16,
        direction: str = "up",
        going: float = 0.0,
        layer: str = "A-WALL"
    ) -> dict:
        """
        Draw a straight staircase plan symbol.
        x,y: bottom of staircase. width: stair width. total_rise: vertical rise in mm.
        going: tread depth (auto-calculated from total horizontal run if 0).
        direction: 'up' (arrow points away from x,y) or 'down'.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        tread_depth = going if going > 0 else total_rise / num_steps * 1.8  # approx going
        total_run = tread_depth * num_steps

        # Side strings
        left = _line(space, x, y, x, y + total_run, layer, 25)
        right = _line(space, x + width, y, x + width, y + total_run, layer, 25)
        handles += [left.Handle, right.Handle]

        # Treads
        for i in range(num_steps + 1):
            ry = y + i * tread_depth
            tread = _line(space, x, ry, x + width, ry, layer, 18)
            handles.append(tread.Handle)

        # Direction arrow (centre line with arrowhead)
        arrow_x = x + width / 2
        arrow_start_y = y + tread_depth * 0.5
        arrow_end_y = y + total_run - tread_depth * 0.5
        arrow_line = _line(space, arrow_x, arrow_start_y, arrow_x, arrow_end_y, layer)
        handles.append(arrow_line.Handle)

        # Arrowhead
        ah = tread_depth * 0.4
        aw = width * 0.12
        arrow_tip_y = arrow_end_y
        arr_pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [arrow_x, arrow_tip_y, 0,
             arrow_x - aw, arrow_tip_y - ah, 0,
             arrow_x + aw, arrow_tip_y - ah, 0,
             arrow_x, arrow_tip_y, 0]
        )
        arrowhead = space.AddLightWeightPolyline(arr_pts)
        arrowhead.Closed = True
        arrowhead.Layer = layer
        handles.append(arrowhead.Handle)

        # "UP" label
        label_t = _text(space, arrow_x, y + tread_depth * 2, "UP" if direction == "up" else "DN",
                        width * 0.12, layer)
        handles.append(label_t.Handle)

        # Break line (diagonal cross-cut) at top of visible portion
        break_y = y + total_run * 0.65
        break_ln = _line(space, x, break_y, x + width, break_y + tread_depth * 0.3, layer)
        handles.append(break_ln.Handle)

        return {
            "handles": handles,
            "num_steps": num_steps,
            "tread_depth_mm": round(tread_depth, 1),
            "total_run_mm": round(total_run, 1),
            "message": f"Staircase: {num_steps} steps, {width}mm wide, {total_run:.0f}mm run"
        }

    # -----------------------------------------------------------------------
    # KITCHEN LAYOUT WORKFLOW
    # -----------------------------------------------------------------------

    @mcp.tool()
    def draw_kitchen_layout(
        x: float, y: float,
        room_width: float, room_depth: float,
        layout_type: str = "l-shape",
        unit_depth: float = 600.0,
        island_width: float = 0.0,
        island_depth: float = 900.0,
        layer: str = "A-FURN-FIXD"
    ) -> dict:
        """
        Draw a complete kitchen layout with units arranged around the room.
        layout_type: 'single-wall', 'galley', 'l-shape', 'u-shape', 'island'.
        island_width: if > 0 and layout supports it, adds a kitchen island.
        Draws unit outlines; individual units (sink, hob) can be added separately.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []
        ud = unit_depth

        def add_counter(sx, sy, w, d):
            r = _rect(space, sx, sy, w, d, layer, 18)
            handles.append(r.Handle)

        if layout_type == "single-wall":
            add_counter(x, y, room_width, ud)

        elif layout_type == "galley":
            add_counter(x, y, room_width, ud)
            add_counter(x, y + room_depth - ud, room_width, ud)

        elif layout_type == "l-shape":
            add_counter(x, y, room_width, ud)
            add_counter(x, y, ud, room_depth)

        elif layout_type == "u-shape":
            add_counter(x, y, room_width, ud)
            add_counter(x, y, ud, room_depth)
            add_counter(x + room_width - ud, y, ud, room_depth)

        elif layout_type == "island":
            add_counter(x, y, room_width, ud)
            add_counter(x, y, ud, room_depth)
            add_counter(x + room_width - ud, y, ud, room_depth)
            if island_width > 0:
                isl_x = x + (room_width - island_width) / 2
                isl_y = y + ud + (room_depth - ud - island_depth) / 2
                island = _rect(space, isl_x, isl_y, island_width, island_depth, layer, 25)
                handles.append(island.Handle)

        return {
            "handles": handles,
            "layout_type": layout_type,
            "message": f"Kitchen layout '{layout_type}' drawn in {room_width}×{room_depth}mm room"
        }

    # -----------------------------------------------------------------------
    # BATHROOM LAYOUT WORKFLOW
    # -----------------------------------------------------------------------

    @mcp.tool()
    def draw_bathroom_layout(
        x: float, y: float,
        room_width: float, room_depth: float,
        layout_type: str = "standard",
        has_bath: bool = True,
        has_shower: bool = False,
        has_double_sink: bool = False,
        layer: str = "A-FIXT"
    ) -> dict:
        """
        Draw a complete bathroom layout.
        layout_type: 'standard', 'ensuite', 'wet-room'.
        Automatically positions toilet, basin, bath/shower based on room size.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        # Standard toilet dimensions
        toilet_w, toilet_d = 750, 650
        basin_w, basin_d = 600, 450
        bath_w, bath_d = 1700, 750
        shower_w, shower_d = 900, 900

        if layout_type == "ensuite":
            # Compact: toilet + shower only, no bath
            has_bath = False
            has_shower = True

        # Toilet (always bottom-right corner)
        t_x = x + room_width - toilet_w - 50
        t_y = y + 50
        # Draw toilet inline
        ctr = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [t_x + toilet_w / 2, t_y + toilet_d * 0.45, 0.0]
        )
        major = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [toilet_w / 2 * 0.9, 0.0, 0.0]
        )
        pan = space.AddEllipse(ctr, major, (toilet_d * 0.85 * 0.9) / toilet_w)
        pan.Layer = layer
        cistern = _rect(space, t_x, t_y + toilet_d * 0.72, toilet_w, toilet_d * 0.25, layer)
        handles += [pan.Handle, cistern.Handle]

        # Basin (bottom-left)
        b_x = x + 50
        b_y = y + 50
        basin_outer = _rect(space, b_x, b_y, basin_w, basin_d, layer)
        basin_inner = _rect(space, b_x + basin_w * 0.1, b_y + basin_d * 0.12,
                            basin_w * 0.8, basin_d * 0.7, layer)
        drain = _circle(space, b_x + basin_w / 2, b_y + basin_d / 2, basin_w * 0.08, layer)
        handles += [basin_outer.Handle, basin_inner.Handle, drain.Handle]

        # Bath (along longest available wall)
        if has_bath:
            if room_width >= room_depth:
                b_x2 = x + 50
                b_y2 = y + room_depth - bath_d - 50
                bath_w_placed, bath_d_placed = bath_w, bath_d
            else:
                b_x2 = x + room_width - bath_d - 50
                b_y2 = y + 50
                bath_w_placed, bath_d_placed = bath_d, bath_w
            bath_outer = _rect(space, b_x2, b_y2, bath_w_placed, bath_d_placed, layer)
            bath_ctr = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8,
                [b_x2 + bath_w_placed / 2, b_y2 + bath_d_placed / 2, 0.0]
            )
            bath_major = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8,
                [bath_w_placed * 0.42, 0.0, 0.0]
            )
            bath_basin = space.AddEllipse(bath_ctr, bath_major, bath_d_placed * 0.4 / bath_w_placed)
            bath_basin.Layer = layer
            handles += [bath_outer.Handle, bath_basin.Handle]

        # Shower
        if has_shower:
            s_x = x + room_width - shower_w - 50
            s_y = y + room_depth - shower_d - 50
            shower_outer = _rect(space, s_x, s_y, shower_w, shower_d, layer)
            shower_head = _circle(space, s_x + shower_w / 2, s_y + shower_d / 2,
                                  min(shower_w, shower_d) * 0.15, layer)
            cross_size = min(shower_w, shower_d) * 0.12
            sc_x, sc_y = s_x + shower_w / 2, s_y + shower_d / 2
            sh1 = _line(space, sc_x - cross_size, sc_y, sc_x + cross_size, sc_y, layer)
            sh2 = _line(space, sc_x, sc_y - cross_size, sc_x, sc_y + cross_size, layer)
            handles += [shower_outer.Handle, shower_head.Handle, sh1.Handle, sh2.Handle]

        doc.Regen(1)
        return {
            "handles": handles,
            "layout_type": layout_type,
            "has_bath": has_bath,
            "has_shower": has_shower,
            "message": f"Bathroom layout '{layout_type}' drawn in {room_width}×{room_depth}mm room"
        }

    # -----------------------------------------------------------------------
    # SPACE PLANNING ANALYSIS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def analyse_circulation_space(
        room_width: float, room_depth: float,
        furniture_handles: list[str] = None
    ) -> dict:
        """
        Analyse circulation space in a room.
        Calculates total room area, estimated furniture footprint (from bounding boxes),
        and remaining floor area. Returns a circulation adequacy assessment.
        Minimum recommended circulation: 600mm corridors, 900mm main routes.
        """
        doc = get_active_doc()
        total_area_m2 = (room_width * room_depth) / 1e6
        furniture_area_m2 = 0.0

        if furniture_handles:
            for h in furniture_handles:
                try:
                    obj = doc.HandleToObject(h)
                    mn, mx = obj.GetBoundingBox()
                    w = mx[0] - mn[0]
                    d = mx[1] - mn[1]
                    furniture_area_m2 += (w * d) / 1e6
                except Exception:
                    pass

        clear_area_m2 = total_area_m2 - furniture_area_m2
        circulation_ratio = clear_area_m2 / total_area_m2

        if circulation_ratio >= 0.5:
            assessment = "Good — plenty of circulation space"
        elif circulation_ratio >= 0.35:
            assessment = "Adequate — meets minimum standards"
        elif circulation_ratio >= 0.25:
            assessment = "Tight — review furniture placement"
        else:
            assessment = "Overcrowded — reduce furniture or increase room size"

        return {
            "total_area_m2": round(total_area_m2, 2),
            "furniture_footprint_m2": round(furniture_area_m2, 2),
            "clear_floor_area_m2": round(clear_area_m2, 2),
            "circulation_ratio_pct": round(circulation_ratio * 100, 1),
            "assessment": assessment,
            "note": "Furniture footprint estimated from bounding boxes (may include overlap)"
        }

    @mcp.tool()
    def generate_room_data_tag(
        x: float, y: float,
        room_name: str,
        room_number: str,
        area_m2: float,
        floor_finish: str = "",
        ceiling_height: float = 0.0,
        text_height: float = 150.0,
        layer: str = "A-ANNO-ROOM"
    ) -> dict:
        """
        Generate a comprehensive room data tag with name, number, area,
        floor finish, and ceiling height — suitable for design development drawings.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        lines = [
            (f"{room_number}  {room_name.upper()}", text_height * 1.2),
            (f"{area_m2:.2f} m²", text_height),
        ]
        if floor_finish:
            lines.append((f"FF: {floor_finish}", text_height * 0.85))
        if ceiling_height > 0:
            lines.append((f"CH: {ceiling_height:.0f}mm", text_height * 0.85))

        for i, (line, ht) in enumerate(lines):
            t = _text(space, x, y - i * text_height * 1.6, line, ht, layer)
            handles.append(t.Handle)

        # Underline below room name
        line_width = len(lines[0][0]) * text_height * 0.6
        ul = _line(space, x - line_width * 0.1, y - text_height * 1.5,
                   x + line_width * 1.1, y - text_height * 1.5, layer)
        handles.append(ul.Handle)

        return {
            "handles": handles,
            "message": f"Room data tag for '{room_name}' placed at ({x},{y})"
        }
