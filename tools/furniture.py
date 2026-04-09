"""
tools/furniture.py
Furniture and fixture placement tools for interior designers.
Draws symbolic 2D plan-view representations of common furniture.
All dimensions in mm. Symbols follow standard ID plan conventions.
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_active_doc, point


def _rect(space, x, y, w, h, angle_deg=0.0, layer="A-FURN"):
    """Helper: draw a rotated rectangle from bottom-left corner."""
    angle = math.radians(angle_deg)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    corners = [(0, 0), (w, 0), (w, h), (0, h), (0, 0)]
    flat = []
    for cx, cy in corners:
        rx = x + cx * cos_a - cy * sin_a
        ry = y + cx * sin_a + cy * cos_a
        flat += [rx, ry, 0]

    pts = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, flat)
    obj = space.AddLightWeightPolyline(pts)
    obj.Closed = True
    obj.Layer = layer
    return obj


def _circle(space, cx, cy, r, layer="A-FURN"):
    obj = space.AddCircle(
        win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [cx, cy, 0.0]),
        float(r)
    )
    obj.Layer = layer
    return obj


def _line(space, x1, y1, x2, y2, layer="A-FURN"):
    obj = space.AddLine(point(x1, y1), point(x2, y2))
    obj.Layer = layer
    return obj


def register_furniture_tools(mcp):

    # -----------------------------------------------------------------------
    # SEATING
    # -----------------------------------------------------------------------

    @mcp.tool()
    def place_sofa(
        x: float, y: float,
        width: float = 2200.0, depth: float = 900.0,
        rotation_deg: float = 0.0,
        style: str = "3-seater",
        layer: str = "A-FURN"
    ) -> dict:
        """
        Place a sofa symbol. style: '2-seater', '3-seater', 'l-shape', 'corner'.
        x,y: insertion point (bottom-left of bounding box).
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        # Outer body
        body = _rect(space, x, y, width, depth, rotation_deg, layer)
        handles.append(body.Handle)

        # Seat divisions
        if style in ("2-seater", "3-seater"):
            seats = 2 if style == "2-seater" else 3
            seat_w = width / seats
            angle = math.radians(rotation_deg)
            for i in range(1, seats):
                sx = x + i * seat_w * math.cos(angle)
                sy = y + i * seat_w * math.sin(angle)
                ex = sx - depth * math.sin(angle)
                ey = sy + depth * math.cos(angle)
                div = _line(space, sx, sy, ex, ey, layer)
                handles.append(div.Handle)

        # Back cushion line
        cushion_depth = depth * 0.35
        angle = math.radians(rotation_deg)
        bx1 = x - cushion_depth * math.sin(angle) + (depth - cushion_depth) * (-math.sin(angle))
        by1 = y + cushion_depth * math.cos(angle) + (depth - cushion_depth) * math.cos(angle)
        bx2 = bx1 + width * math.cos(angle)
        by2 = by1 + width * math.sin(angle)
        back = _line(space, bx1 - (depth - cushion_depth) * (-math.sin(angle)),
                     by1 - (depth - cushion_depth) * math.cos(angle),
                     bx2 - (depth - cushion_depth) * (-math.sin(angle)),
                     by2 - (depth - cushion_depth) * math.cos(angle), layer)
        handles.append(back.Handle)

        return {
            "handles": handles,
            "width": width, "depth": depth,
            "message": f"{style.title()} sofa {width}×{depth}mm placed at ({x},{y})"
        }

    @mcp.tool()
    def place_chair(
        x: float, y: float,
        width: float = 600.0, depth: float = 600.0,
        rotation_deg: float = 0.0,
        style: str = "dining",
        layer: str = "A-FURN"
    ) -> dict:
        """
        Place a chair symbol. style: 'dining', 'lounge', 'office', 'bar'.
        x,y: center of the chair.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        # Body
        body = _rect(space, x - width / 2, y - depth / 2, width, depth, rotation_deg, layer)
        handles.append(body.Handle)

        # Back rest
        back_depth = depth * 0.2
        angle = math.radians(rotation_deg)
        bx = x - width / 2
        by = y + depth / 2 - back_depth
        back = _rect(space, bx, by, width, back_depth, rotation_deg, layer)
        handles.append(back.Handle)

        if style == "office":
            circ = _circle(space, x, y, width * 0.3, layer)
            handles.append(circ.Handle)

        return {
            "handles": handles,
            "width": width, "depth": depth,
            "message": f"{style.title()} chair {width}×{depth}mm at ({x},{y})"
        }

    @mcp.tool()
    def place_armchair(
        x: float, y: float,
        width: float = 800.0, depth: float = 800.0,
        rotation_deg: float = 0.0,
        layer: str = "A-FURN"
    ) -> dict:
        """Place an armchair symbol with side arms and back rest."""
        doc = get_active_doc()
        space = doc.ModelSpace
        arm_w = width * 0.15
        handles = []

        # Seat
        seat = _rect(space, x, y, width, depth * 0.65, rotation_deg, layer)
        handles.append(seat.Handle)
        # Back
        back = _rect(space, x, y + depth * 0.65, width, depth * 0.35, rotation_deg, layer)
        handles.append(back.Handle)
        # Left arm
        la = _rect(space, x - arm_w, y, arm_w, depth, rotation_deg, layer)
        handles.append(la.Handle)
        # Right arm
        ra = _rect(space, x + width, y, arm_w, depth, rotation_deg, layer)
        handles.append(ra.Handle)

        return {
            "handles": handles,
            "message": f"Armchair {width}×{depth}mm at ({x},{y})"
        }

    # -----------------------------------------------------------------------
    # TABLES
    # -----------------------------------------------------------------------

    @mcp.tool()
    def place_dining_table(
        x: float, y: float,
        width: float = 1800.0, depth: float = 900.0,
        rotation_deg: float = 0.0,
        num_chairs: int = 6,
        chair_width: float = 450.0, chair_depth: float = 450.0,
        layer: str = "A-FURN"
    ) -> dict:
        """
        Place a dining table with chairs arranged around it.
        x,y: table center. num_chairs distributed evenly around the perimeter.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        # Table
        table = _rect(space, x - width / 2, y - depth / 2, width, depth, rotation_deg, layer)
        handles.append(table.Handle)

        # Chairs arranged around table
        gap = 50.0
        chairs_long = max(1, round(num_chairs * width / (2 * (width + depth))))
        chairs_short = max(1, (num_chairs - 2 * chairs_long) // 2)

        angle = math.radians(rotation_deg)

        # Top and bottom rows
        for side in [-1, 1]:
            cy_base = y + side * (depth / 2 + gap + chair_depth / 2)
            count = chairs_long
            spacing = width / count
            for i in range(count):
                cx = x - width / 2 + spacing * (i + 0.5)
                chair_rot = rotation_deg + (0 if side == -1 else 180)
                c = _rect(space, cx - chair_width / 2, cy_base - chair_depth / 2,
                          chair_width, chair_depth, chair_rot, layer)
                handles.append(c.Handle)

        # Left and right columns
        for side in [-1, 1]:
            cx_base = x + side * (width / 2 + gap + chair_depth / 2)
            count = chairs_short
            if count > 0:
                spacing = depth / count
                for i in range(count):
                    cy = y - depth / 2 + spacing * (i + 0.5)
                    chair_rot = rotation_deg + (270 if side == -1 else 90)
                    c = _rect(space, cx_base - chair_depth / 2, cy - chair_width / 2,
                              chair_depth, chair_width, chair_rot, layer)
                    handles.append(c.Handle)

        return {
            "handles": handles,
            "table_width": width, "table_depth": depth,
            "num_chairs": num_chairs,
            "message": f"Dining table {width}×{depth}mm with {num_chairs} chairs at ({x},{y})"
        }

    @mcp.tool()
    def place_coffee_table(
        x: float, y: float,
        width: float = 1200.0, depth: float = 600.0,
        rotation_deg: float = 0.0,
        shape: str = "rectangle",
        layer: str = "A-FURN"
    ) -> dict:
        """
        Place a coffee table. shape: 'rectangle', 'oval', 'round', 'square'.
        x,y: center of the table.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        if shape in ("round", "square"):
            diameter = min(width, depth)
            if shape == "round":
                c = _circle(space, x, y, diameter / 2, layer)
                handles.append(c.Handle)
            else:
                r = _rect(space, x - diameter / 2, y - diameter / 2,
                          diameter, diameter, rotation_deg, layer)
                handles.append(r.Handle)
        elif shape == "oval":
            major = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8, [width / 2, 0.0, 0.0]
            )
            ctr = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8, [x, y, 0.0]
            )
            e = space.AddEllipse(ctr, major, depth / width)
            e.Layer = layer
            handles.append(e.Handle)
        else:
            r = _rect(space, x - width / 2, y - depth / 2,
                      width, depth, rotation_deg, layer)
            handles.append(r.Handle)

        return {
            "handles": handles,
            "message": f"{shape.title()} coffee table {width}×{depth}mm at ({x},{y})"
        }

    @mcp.tool()
    def place_desk(
        x: float, y: float,
        width: float = 1600.0, depth: float = 800.0,
        rotation_deg: float = 0.0,
        with_return: bool = False,
        return_width: float = 1000.0,
        layer: str = "A-FURN"
    ) -> dict:
        """
        Place a desk (and optional L-shaped return).
        x,y: bottom-left corner. with_return: adds an L-shaped return.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        desk = _rect(space, x, y, width, depth, rotation_deg, layer)
        handles.append(desk.Handle)

        if with_return:
            angle = math.radians(rotation_deg)
            rx = x + width * math.cos(angle)
            ry = y + width * math.sin(angle)
            ret = _rect(space, rx, ry - depth, return_width, depth, rotation_deg + 90, layer)
            handles.append(ret.Handle)

        return {
            "handles": handles,
            "message": f"Desk {width}×{depth}mm at ({x},{y})" +
                       (" with return" if with_return else "")
        }

    # -----------------------------------------------------------------------
    # BEDS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def place_bed(
        x: float, y: float,
        size: str = "queen",
        rotation_deg: float = 0.0,
        with_pillows: bool = True,
        layer: str = "A-FURN"
    ) -> dict:
        """
        Place a bed symbol. size: 'single' (900×2000), 'double' (1350×2000),
        'queen' (1530×2030), 'king' (1830×2030), 'super-king' (1800×2000).
        x,y: headboard corner (bottom-left when rotation=0).
        """
        sizes = {
            "single":    (900, 2000),
            "double":    (1350, 2000),
            "queen":     (1530, 2030),
            "king":      (1830, 2030),
            "super-king": (1800, 2000),
        }
        width, depth = sizes.get(size.lower(), (1530, 2030))
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        # Mattress
        mattress = _rect(space, x, y, width, depth, rotation_deg, layer)
        handles.append(mattress.Handle)

        # Headboard
        angle = math.radians(rotation_deg)
        hb = _rect(space, x, y + depth - depth * 0.08, width, depth * 0.08, rotation_deg, layer)
        handles.append(hb.Handle)

        # Pillows
        if with_pillows:
            pillow_w = width * 0.35
            pillow_h = depth * 0.12
            gap = width * 0.05
            num_pillows = 1 if width < 1200 else 2
            total = num_pillows * pillow_w + (num_pillows - 1) * gap
            start_x = x + (width - total) / 2
            py = y + depth - depth * 0.08 - pillow_h - gap
            for i in range(num_pillows):
                px = start_x + i * (pillow_w + gap)
                p = _rect(space, px, py, pillow_w, pillow_h, rotation_deg, layer)
                handles.append(p.Handle)

        return {
            "handles": handles,
            "size": size, "width": width, "depth": depth,
            "message": f"{size.title()} bed ({width}×{depth}mm) at ({x},{y})"
        }

    # -----------------------------------------------------------------------
    # KITCHEN & BATHROOM FIXTURES
    # -----------------------------------------------------------------------

    @mcp.tool()
    def place_kitchen_unit(
        x: float, y: float,
        width: float = 600.0,
        depth: float = 600.0,
        unit_type: str = "base",
        rotation_deg: float = 0.0,
        layer: str = "A-FURN-FIXD"
    ) -> dict:
        """
        Place a kitchen unit. unit_type: 'base', 'wall', 'tall', 'sink', 'hob', 'corner'.
        width/depth are the plan dimensions.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        body = _rect(space, x, y, width, depth, rotation_deg, layer)
        handles.append(body.Handle)

        if unit_type == "sink":
            margin = width * 0.1
            basin = _rect(space, x + margin, y + margin,
                          width - 2 * margin, depth - 2 * margin, rotation_deg, layer)
            handles.append(basin.Handle)
            tap_x = x + width / 2
            tap_y = y + depth - depth * 0.2
            t = _circle(space, tap_x, tap_y, depth * 0.05, layer)
            handles.append(t.Handle)

        elif unit_type == "hob":
            burner_r = min(width, depth) * 0.12
            positions = [(0.3, 0.3), (0.7, 0.3), (0.3, 0.7), (0.7, 0.7)]
            for bx_frac, by_frac in positions:
                bx = x + width * bx_frac
                by = y + depth * by_frac
                b = _circle(space, bx, by, burner_r, layer)
                handles.append(b.Handle)

        elif unit_type == "corner":
            # L-shaped worktop corner
            corner_pts = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8,
                [x, y, 0, x + width, y, 0, x + width, y + depth / 2, 0,
                 x + width / 2, y + depth / 2, 0, x + width / 2, y + depth, 0,
                 x, y + depth, 0, x, y, 0]
            )
            corner_shape = space.AddLightWeightPolyline(corner_pts)
            corner_shape.Closed = True
            corner_shape.Layer = layer
            handles.append(corner_shape.Handle)
            body.Delete()
            handles.pop(0)

        return {
            "handles": handles,
            "unit_type": unit_type,
            "message": f"Kitchen {unit_type} unit {width}×{depth}mm at ({x},{y})"
        }

    @mcp.tool()
    def place_toilet(
        x: float, y: float,
        rotation_deg: float = 0.0,
        layer: str = "A-FIXT"
    ) -> dict:
        """Place a toilet symbol (standard 750×480mm pan + cistern)."""
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []
        pan_w, pan_d = 750, 480
        cistern_d = 170

        # Pan (oval)
        ctr = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x + pan_w / 2, y + pan_d / 2, 0.0]
        )
        major = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [pan_w / 2 * 0.9, 0.0, 0.0]
        )
        pan = space.AddEllipse(ctr, major, (pan_d * 0.9) / pan_w)
        pan.Layer = layer
        handles.append(pan.Handle)

        # Cistern
        cistern = _rect(space, x, y + pan_d, pan_w, cistern_d, rotation_deg, layer)
        handles.append(cistern.Handle)

        return {
            "handles": handles,
            "message": f"Toilet placed at ({x},{y}), rotation={rotation_deg}°"
        }

    @mcp.tool()
    def place_bath(
        x: float, y: float,
        width: float = 1700.0, depth: float = 750.0,
        rotation_deg: float = 0.0,
        layer: str = "A-FIXT"
    ) -> dict:
        """Place a bathtub symbol with inner oval basin. Standard: 1700×750mm."""
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        outer = _rect(space, x, y, width, depth, rotation_deg, layer)
        handles.append(outer.Handle)

        margin_x = width * 0.06
        margin_y = depth * 0.08
        ctr = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x + width / 2, y + depth / 2, 0.0]
        )
        inner_w = (width - 2 * margin_x) / 2
        inner_d = (depth - 2 * margin_y) / 2
        major = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [inner_w, 0.0, 0.0]
        )
        basin = space.AddEllipse(ctr, major, inner_d / inner_w)
        basin.Layer = layer
        handles.append(basin.Handle)

        # Tap
        t = _circle(space, x + width * 0.85, y + depth / 2, depth * 0.06, layer)
        handles.append(t.Handle)

        return {
            "handles": handles,
            "message": f"Bath {width}×{depth}mm at ({x},{y})"
        }

    @mcp.tool()
    def place_sink(
        x: float, y: float,
        width: float = 600.0, depth: float = 500.0,
        rotation_deg: float = 0.0,
        num_bowls: int = 1,
        layer: str = "A-FIXT"
    ) -> dict:
        """
        Place a sink/basin symbol. num_bowls: 1 or 2 (for double sinks).
        x,y: bottom-left of the overall sink unit.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        outer = _rect(space, x, y, width, depth, rotation_deg, layer)
        handles.append(outer.Handle)

        bowl_w = (width - (num_bowls + 1) * width * 0.08) / num_bowls
        bowl_d = depth * 0.75
        for i in range(num_bowls):
            bx = x + width * 0.08 + i * (bowl_w + width * 0.08)
            by = y + depth * 0.12
            bowl = _rect(space, bx, by, bowl_w, bowl_d, rotation_deg, layer)
            handles.append(bowl.Handle)
            # Drain
            drain = _circle(space, bx + bowl_w / 2, by + bowl_d / 2, bowl_w * 0.08, layer)
            handles.append(drain.Handle)

        # Tap
        t = _circle(space, x + width / 2, y + depth * 0.9, depth * 0.05, layer)
        handles.append(t.Handle)

        return {
            "handles": handles,
            "num_bowls": num_bowls,
            "message": f"{num_bowls}-bowl sink {width}×{depth}mm at ({x},{y})"
        }

    @mcp.tool()
    def place_shower(
        x: float, y: float,
        width: float = 900.0, depth: float = 900.0,
        rotation_deg: float = 0.0,
        door_side: str = "front",
        layer: str = "A-FIXT"
    ) -> dict:
        """
        Place a shower enclosure symbol with tray and door indication.
        door_side: 'front', 'left', 'right'.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        outer = _rect(space, x, y, width, depth, rotation_deg, layer)
        handles.append(outer.Handle)

        # Shower head
        head = _circle(space, x + width / 2, y + depth / 2, min(width, depth) * 0.15, layer)
        handles.append(head.Handle)
        cross_size = min(width, depth) * 0.12
        cx, cy = x + width / 2, y + depth / 2
        h1 = _line(space, cx - cross_size, cy, cx + cross_size, cy, layer)
        h2 = _line(space, cx, cy - cross_size, cx, cy + cross_size, layer)
        handles += [h1.Handle, h2.Handle]

        return {
            "handles": handles,
            "message": f"Shower {width}×{depth}mm at ({x},{y})"
        }

    # -----------------------------------------------------------------------
    # STORAGE & CASEGOODS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def place_wardrobe(
        x: float, y: float,
        width: float = 1800.0, depth: float = 600.0,
        rotation_deg: float = 0.0,
        door_type: str = "hinged",
        layer: str = "A-FURN-FIXD"
    ) -> dict:
        """
        Place a wardrobe. door_type: 'hinged', 'sliding', 'walk-in'.
        x,y: bottom-left corner.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        body = _rect(space, x, y, width, depth, rotation_deg, layer)
        handles.append(body.Handle)

        if door_type == "sliding":
            mid_x = x + width / 2
            mid = _line(space, mid_x, y, mid_x, y + depth, layer)
            handles.append(mid.Handle)
        elif door_type == "hinged":
            num_doors = round(width / 600)
            door_w = width / num_doors
            angle = math.radians(rotation_deg)
            for i in range(num_doors):
                dx_start = x + i * door_w * math.cos(angle)
                dy_start = y + i * door_w * math.sin(angle)
                # Swing arc
                arc_start = math.radians(rotation_deg + 90)
                arc_end = math.radians(rotation_deg + 90) + math.radians(90)
                arc = space.AddArc(
                    point(dx_start, dy_start),
                    float(door_w),
                    arc_start, arc_end
                )
                arc.Layer = layer
                arc.Linetype = "DASHED"
                handles.append(arc.Handle)

        return {
            "handles": handles,
            "message": f"Wardrobe {width}×{depth}mm ({door_type}) at ({x},{y})"
        }

    @mcp.tool()
    def place_bookshelf(
        x: float, y: float,
        width: float = 900.0, depth: float = 300.0,
        num_shelves: int = 4,
        rotation_deg: float = 0.0,
        layer: str = "A-FURN-FIXD"
    ) -> dict:
        """Place a bookshelf/shelving unit with shelf lines."""
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        body = _rect(space, x, y, width, depth, rotation_deg, layer)
        handles.append(body.Handle)

        for i in range(1, num_shelves):
            shelf_y = y + depth * i / num_shelves
            ln = _line(space, x, shelf_y, x + width, shelf_y, layer)
            handles.append(ln.Handle)

        return {
            "handles": handles,
            "message": f"Bookshelf {width}×{depth}mm ({num_shelves} shelves) at ({x},{y})"
        }

    # -----------------------------------------------------------------------
    # LIGHTING (PLAN VIEW)
    # -----------------------------------------------------------------------

    @mcp.tool()
    def place_light_downlight(
        x: float, y: float,
        radius: float = 75.0,
        layer: str = "E-LITE"
    ) -> dict:
        """Place a downlight/recessed light symbol (circle with cross)."""
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        c = _circle(space, x, y, radius, layer)
        handles.append(c.Handle)
        h1 = _line(space, x - radius, y, x + radius, y, layer)
        h2 = _line(space, x, y - radius, x, y + radius, layer)
        handles += [h1.Handle, h2.Handle]

        return {"handles": handles, "message": f"Downlight at ({x},{y})"}

    @mcp.tool()
    def place_light_pendant(
        x: float, y: float,
        radius: float = 150.0,
        layer: str = "E-LITE"
    ) -> dict:
        """Place a pendant light symbol (circle with dot)."""
        doc = get_active_doc()
        space = doc.ModelSpace
        outer = _circle(space, x, y, radius, layer)
        inner = _circle(space, x, y, radius * 0.15, layer)
        return {
            "handles": [outer.Handle, inner.Handle],
            "message": f"Pendant light at ({x},{y})"
        }

    @mcp.tool()
    def place_power_outlet(
        x: float, y: float,
        rotation_deg: float = 0.0,
        layer: str = "E-POWR"
    ) -> dict:
        """Place a power outlet symbol (rectangle with lines)."""
        doc = get_active_doc()
        space = doc.ModelSpace
        size = 100.0
        body = _rect(space, x - size / 2, y - size / 4, size, size / 2, rotation_deg, layer)
        ln = _line(space, x - size * 0.3, y, x + size * 0.3, y, layer)
        return {
            "handles": [body.Handle, ln.Handle],
            "message": f"Power outlet at ({x},{y})"
        }
