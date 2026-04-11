"""
tools/anthropometry.py
Anthropometry & Ergonomics tools — maps to B.Des ID curriculum:
  • Fundamentals of Design I, Unit 5 — Anthropometry (scale and proportion)
  • Vocational Skills — Interior lighting, Plumbing, Furniture making

Covers:
  • Human figure templates (standing, seated, lying, child)
  • Ergonomic clearance zones around furniture
  • ADA / universal design compliance checks and drawings
  • Standard space dimensions (door clearances, corridor widths, counter heights)
  • Kitchen work triangle analysis
  • Reach zones and activity envelopes
  • Furniture ergonomic dimensions reference table
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_model_space, point


def _var(coords):
    return win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(c) for c in coords]
    )


def _polyline(space, pts_flat, closed=False):
    pl = space.AddLightWeightPolyline(_var(pts_flat))
    if closed:
        pl.Closed = True
    return pl


def _circle(space, cx, cy, r):
    return space.AddCircle(point(cx, cy), r)


def _line(space, x1, y1, x2, y2):
    return space.AddLine(point(x1, y1), point(x2, y2))


def _text(space, txt, tx, ty, height=25, layer="A-ANNO-TEXT"):
    t = space.AddText(str(txt), point(tx, ty), height)
    t.Layer = layer
    return t


# ---------------------------------------------------------------------------
# Standard anthropometric dimensions (mm) — based on 50th percentile adult
# ---------------------------------------------------------------------------

HUMAN_DIMS = {
    "standing_height":   1750,
    "eye_level":         1620,
    "shoulder_height":   1430,
    "elbow_height":       1050,
    "knuckle_height":     745,
    "shoulder_width":     450,
    "body_depth":         300,
    "seated_height":      1200,
    "seated_eye_level":   1110,
    "seated_elbow":       680,
    "seated_knee":        500,
    "seated_seat_height": 430,
    "child_height":       1100,  # ~6-year-old
}

CLEARANCES = {
    "min_corridor":        900,
    "comfortable_corridor": 1200,
    "wheelchair_width":    760,
    "wheelchair_turning":  1500,
    "door_clear_width":    900,
    "bed_side_clearance":  600,
    "desk_chair_pullout":  900,
    "dining_chair_pullout": 760,
    "kitchen_counter_depth": 600,
    "kitchen_counter_height": 870,
    "bath_side_clearance": 760,
    "toilet_side_clearance": 460,
    "stair_width_min":     900,
}


def register_anthropometry_tools(mcp):

    # ------------------------------------------------------------------
    # HUMAN FIGURE TEMPLATES
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_human_figure(
        x: float, y: float,
        posture: str = "standing",
        scale: float = 1.0,
        facing: str = "right",
        layer: str = "A-FURN-HUMAN"
    ) -> dict:
        """
        Draw a schematic human figure (plan or elevation stick figure).

        posture: 'standing', 'seated', 'lying', 'child', 'wheelchair'
        facing: 'right' or 'left' (mirrors the figure)
        scale: 1.0 = full size (mm), 0.1 = 1:10 drawing

        Covers curriculum: Fundamentals of Design I, Unit 5 — Anthropometry.
        """
        space = get_model_space()
        handles = []
        s = scale
        mirror = -1 if facing == "left" else 1

        def _h(dx, dy):
            return x + dx * s * mirror, y + dy * s

        if posture == "standing":
            # Elevation: head circle, body, arms, legs
            head_cx, head_cy = _h(0, 1650); head_r = 100 * s
            c = _circle(space, head_cx, head_cy, head_r); c.Layer = layer; handles.append(c.Handle)
            # Torso
            lines = [
                (*_h(0, 1550), *_h(0, 950)),   # spine
                (*_h(-225, 1430), *_h(225, 1430)),  # shoulders
                (*_h(-225, 1430), *_h(-300, 1050)), # left arm
                (*_h(225, 1430), *_h(300, 1050)),   # right arm
                (*_h(-100, 950), *_h(100, 950)),    # hips
                (*_h(-100, 950), *_h(-150, 450)),   # left thigh
                (*_h(100, 950), *_h(150, 450)),     # right thigh
                (*_h(-150, 450), *_h(-160, 0)),     # left shin
                (*_h(150, 450), *_h(160, 0)),       # right shin
                (*_h(-160, 0), *_h(-50, 0)),        # left foot
                (*_h(160, 0), *_h(50, 0)),          # right foot
            ]
            for pts in lines:
                ln = _line(space, *pts); ln.Layer = layer; handles.append(ln.Handle)
            height_drawn = 1750 * s

        elif posture == "seated":
            head_cx, head_cy = _h(0, 1200); head_r = 100 * s
            c = _circle(space, head_cx, head_cy, head_r); c.Layer = layer; handles.append(c.Handle)
            lines = [
                (*_h(0, 1100), *_h(0, 680)),   # spine
                (*_h(-225, 1100), *_h(225, 1100)),  # shoulders
                (*_h(-225, 1100), *_h(-300, 680)),  # arms
                (*_h(225, 1100), *_h(300, 680)),
                (*_h(-120, 680), *_h(120, 680)),   # seat level
                (*_h(-120, 680), *_h(-120, 430)),   # thighs
                (*_h(120, 680), *_h(350, 500)),    # extended thigh
                (*_h(-120, 430), *_h(-120, 0)),     # lower legs
                (*_h(350, 500), *_h(350, 0)),
            ]
            for pts in lines:
                ln = _line(space, *pts); ln.Layer = layer; handles.append(ln.Handle)
            height_drawn = 1200 * s

        elif posture == "lying":
            head_cx, head_cy = _h(1700, 200); head_r = 100 * s
            c = _circle(space, head_cx, head_cy, head_r); c.Layer = layer; handles.append(c.Handle)
            lines = [
                (*_h(1600, 200), *_h(0, 200)),    # body horizontal
                (*_h(1430, 300), *_h(1200, 100)),  # arms
                (*_h(500, 300), *_h(250, 100)),
                (*_h(0, 250), *_h(-450, 250)),    # legs
            ]
            for pts in lines:
                ln = _line(space, *pts); ln.Layer = layer; handles.append(ln.Handle)
            height_drawn = 200 * s

        elif posture == "child":
            head_cx, head_cy = _h(0, 1050); head_r = 120 * s
            c = _circle(space, head_cx, head_cy, head_r); c.Layer = layer; handles.append(c.Handle)
            lines = [
                (*_h(0, 930), *_h(0, 600)),
                (*_h(-180, 850), *_h(180, 850)),
                (*_h(-180, 850), *_h(-220, 550)),
                (*_h(180, 850), *_h(220, 550)),
                (*_h(-80, 600), *_h(80, 600)),
                (*_h(-80, 600), *_h(-100, 300)),
                (*_h(80, 600), *_h(100, 300)),
                (*_h(-100, 300), *_h(-110, 0)),
                (*_h(100, 300), *_h(110, 0)),
            ]
            for pts in lines:
                ln = _line(space, *pts); ln.Layer = layer; handles.append(ln.Handle)
            height_drawn = 1100 * s

        elif posture == "wheelchair":
            # Wheels
            wl = _circle(space, *_h(-150, 300), 300 * s); wl.Layer = layer; handles.append(wl.Handle)
            wr = _circle(space, *_h(150, 300), 300 * s); wr.Layer = layer; handles.append(wr.Handle)
            # Seat + back
            seat_pts = [*_h(-200, 430), *_h(350, 430), *_h(350, 500), *_h(-200, 500)]
            seat_pts.extend(seat_pts[:2])
            seat = _polyline(space, seat_pts, closed=True); seat.Layer = layer; handles.append(seat.Handle)
            # Person on chair
            head_cx, head_cy = _h(50, 1200); head_r = 100 * s
            ch = _circle(space, head_cx, head_cy, head_r); ch.Layer = layer; handles.append(ch.Handle)
            lines = [
                (*_h(50, 1100), *_h(50, 500)),
                (*_h(-175, 1050), *_h(250, 1050)),
            ]
            for pts in lines:
                ln = _line(space, *pts); ln.Layer = layer; handles.append(ln.Handle)
            height_drawn = 1200 * s
        else:
            raise ValueError(f"Unknown posture: {posture}")

        return {
            "position": [x, y],
            "posture": posture,
            "facing": facing,
            "scale": scale,
            "height_drawn_mm": height_drawn / scale,
            "handle_count": len(handles),
            "message": f"{posture.capitalize()} human figure drawn at ({x},{y})"
        }

    @mcp.tool()
    def draw_human_reach_zone(
        x: float, y: float,
        standing: bool = True,
        show_plan_view: bool = True,
        layer: str = "A-FURN-HUMAN"
    ) -> dict:
        """
        Draw reach zone ellipses/arcs showing comfortable and maximum reach
        for a standing or seated person.
        Useful for kitchen, desk, and storage design.
        Covers curriculum: Unit 5 — Anthropometry with reference to scale and proportion.
        """
        space = get_model_space()
        handles = []

        if show_plan_view:
            # Plan view: concentric semi-circles showing reach zones
            comfortable_reach = 450  # mm
            max_reach = 750
            body_width = 450

            body = _circle(space, x, y, body_width / 2)
            body.Layer = layer; handles.append(body.Handle)

            comf = space.AddArc(point(x, y), comfortable_reach, math.radians(0), math.radians(180))
            comf.Layer = layer; handles.append(comf.Handle)

            maxi = space.AddArc(point(x, y), max_reach, math.radians(0), math.radians(180))
            maxi.Layer = layer; handles.append(maxi.Handle)

            for r, lbl in [(comfortable_reach, "COMFORTABLE\n450mm"), (max_reach, "MAX REACH\n750mm")]:
                t = space.AddText(lbl.replace("\n", " "), point(x, y + r + 30), 30)
                t.Layer = layer; handles.append(t.Handle)
        else:
            # Elevation view: optimal work zone (elbow to shoulder height)
            low = 745; high = 1430   # knuckle to shoulder
            for hy in [low, high]:
                ln = _line(space, x - 800, y + hy, x + 800, y + hy)
                ln.Layer = layer; ln.Linetype = "DASHED"; handles.append(ln.Handle)
            zone_pts = [x-800, y+low, x+800, y+low, x+800, y+high, x-800, y+high, x-800, y+low]
            zone = _polyline(space, zone_pts, closed=True)
            zone.Layer = layer; handles.append(zone.Handle)
            t = space.AddText("OPTIMAL WORK ZONE 745-1430mm", point(x, y + (low+high)/2), 30)
            t.Layer = layer; handles.append(t.Handle)

        return {
            "position": [x, y],
            "view": "plan" if show_plan_view else "elevation",
            "handles": len(handles),
            "message": "Human reach zone drawn"
        }

    # ------------------------------------------------------------------
    # CLEARANCE ZONES
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_clearance_zone(
        x: float, y: float,
        width: float,
        depth: float,
        clearance_type: str = "bed",
        layer: str = "A-FURN-CLEAR"
    ) -> dict:
        """
        Draw a furniture item rectangle with surrounding ergonomic clearance zones.
        clearance_type options: 'bed', 'desk', 'dining', 'toilet', 'bath',
                                'sofa', 'wardrobe', 'kitchen_counter'
        Dimensions are in mm.
        Covers curriculum: Anthropometry — clearances for activities.
        """
        space = get_model_space()
        handles = []

        clearances_map = {
            "bed":             {"front": 600, "side": 600, "back": 0},
            "desk":            {"front": 900, "side": 300, "back": 0},
            "dining":          {"front": 760, "side": 500, "back": 760},
            "toilet":          {"front": 600, "side": 460, "back": 0},
            "bath":            {"front": 760, "side": 760, "back": 0},
            "sofa":            {"front": 900, "side": 300, "back": 150},
            "wardrobe":        {"front": 900, "side": 150, "back": 0},
            "kitchen_counter": {"front": 1200, "side": 300, "back": 0},
        }

        cl = clearances_map.get(clearance_type, {"front": 600, "side": 300, "back": 0})

        # Furniture outline (solid)
        furn_pts = [x, y, x+width, y, x+width, y+depth, x, y+depth, x, y]
        furn = _polyline(space, furn_pts, closed=True)
        furn.Layer = layer; handles.append(furn.Handle)

        # Clearance zone (dashed, expanded)
        front = cl["front"]; side = cl["side"]; back = cl["back"]
        cl_pts = [
            x - side, y - front,
            x + width + side, y - front,
            x + width + side, y + depth + back,
            x - side, y + depth + back,
            x - side, y - front
        ]
        cl_pl = _polyline(space, cl_pts, closed=True)
        cl_pl.Layer = layer; cl_pl.Linetype = "DASHED"; handles.append(cl_pl.Handle)

        # Dimension annotations
        ann_data = [
            (x + width/2, y - front/2, f"CLEARANCE {front}mm"),
            (x + width + side/2, y + depth/2, f"{side}mm"),
        ]
        for tx, ty, lbl in ann_data:
            t = space.AddText(lbl, point(tx, ty), 25)
            t.Layer = layer; handles.append(t.Handle)

        return {
            "furniture": {"x": x, "y": y, "width": width, "depth": depth},
            "clearances": cl,
            "clearance_type": clearance_type,
            "total_footprint": {
                "width": width + 2 * side,
                "depth": depth + front + back
            },
            "message": f"Clearance zone drawn for {clearance_type} ({width}x{depth}mm)"
        }

    @mcp.tool()
    def draw_wheelchair_turning_circle(
        cx: float, cy: float,
        layer: str = "A-FURN-ADA"
    ) -> dict:
        """
        Draw a 1500mm wheelchair turning circle with approach clearances.
        Standard requirement for ADA/universal design compliance.
        """
        space = get_model_space()
        handles = []

        r = 750  # 1500mm diameter
        c = _circle(space, cx, cy, r)
        c.Layer = layer; handles.append(c.Handle)

        # Diameter annotations
        for angle in [0, 90]:
            a = math.radians(angle)
            ln = _line(space, cx - r*math.cos(a), cy - r*math.sin(a),
                       cx + r*math.cos(a), cy + r*math.sin(a))
            ln.Layer = layer; ln.Linetype = "DASHED"; handles.append(ln.Handle)

        t = space.AddText("O1500 TURNING CIRCLE", point(cx, cy + r + 40), 35)
        t.Layer = layer; handles.append(t.Handle)
        t2 = space.AddText("(ADA COMPLIANT)", point(cx, cy + r + 80), 30)
        t2.Layer = layer; handles.append(t2.Handle)

        return {
            "center": [cx, cy],
            "diameter": 1500,
            "handle_count": len(handles),
            "message": "Wheelchair turning circle (1500mm) drawn"
        }

    # ------------------------------------------------------------------
    # SPACE STANDARDS
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_corridor_standard(
        x1: float, y1: float,
        length: float,
        corridor_type: str = "standard",
        orientation: str = "horizontal",
        layer: str = "A-ANNO-DIMS"
    ) -> dict:
        """
        Draw a corridor with standard minimum width annotations.
        corridor_type: 'standard' (900mm), 'comfortable' (1200mm),
                       'accessible' (1500mm), 'commercial' (1800mm)
        """
        space = get_model_space()

        widths = {
            "standard":    900,
            "comfortable": 1200,
            "accessible":  1500,
            "commercial":  1800,
        }
        w = widths.get(corridor_type, 900)
        handles = []

        if orientation == "horizontal":
            pts = [x1, y1, x1+length, y1, x1+length, y1+w, x1, y1+w, x1, y1]
        else:
            pts = [x1, y1, x1+w, y1, x1+w, y1+length, x1, y1+length, x1, y1]

        corridor = _polyline(space, pts, closed=True)
        corridor.Layer = layer; handles.append(corridor.Handle)

        # Width dimension line
        if orientation == "horizontal":
            dim = space.AddDimAligned(
                point(x1, y1), point(x1, y1+w), point(x1-150, y1+w/2)
            )
        else:
            dim = space.AddDimAligned(
                point(x1, y1), point(x1+w, y1), point(x1+w/2, y1-150)
            )
        dim.Layer = layer; handles.append(dim.Handle)

        # Label
        cx = x1 + (length if orientation == "horizontal" else w) / 2
        cy = y1 + (w if orientation == "horizontal" else length) / 2
        t = space.AddText(f"{corridor_type.upper()} CORRIDOR  {w}mm WIDE", point(cx, cy), 30)
        t.Layer = layer; handles.append(t.Handle)

        return {
            "corridor_type": corridor_type,
            "width_mm": w,
            "length": length,
            "handle_count": len(handles),
            "message": f"{corridor_type} corridor: {w}mm wide, {length}mm long"
        }

    @mcp.tool()
    def check_space_compliance(
        room_width: float,
        room_depth: float,
        room_type: str = "bedroom"
    ) -> dict:
        """
        Check a room's dimensions against standard minimum space requirements.
        Returns pass/fail for each standard and recommended dimensions.

        room_type: 'bedroom', 'bathroom', 'kitchen', 'living_room',
                   'corridor', 'toilet', 'office_workstation'
        Covers curriculum: Anthropometry — scale and proportion in interior spaces.
        """
        standards = {
            "bedroom": {
                "min_area": 9_500_000,  # 9.5 sqm in mm²
                "min_width": 3000,
                "recommended_area": 12_000_000,
                "notes": "Min 600mm clearance each side of bed"
            },
            "bathroom": {
                "min_area": 4_000_000,
                "min_width": 1500,
                "recommended_area": 6_000_000,
                "notes": "Min 760mm clearance in front of fixtures"
            },
            "kitchen": {
                "min_area": 5_000_000,
                "min_width": 2400,
                "recommended_area": 8_000_000,
                "notes": "Min 1200mm between opposing counters"
            },
            "living_room": {
                "min_area": 12_000_000,
                "min_width": 3000,
                "recommended_area": 20_000_000,
                "notes": "Min 900mm circulation paths"
            },
            "corridor": {
                "min_area": 0,
                "min_width": 900,
                "recommended_area": 0,
                "notes": "ADA: min 1500mm for wheelchair turning"
            },
            "toilet": {
                "min_area": 1_500_000,
                "min_width": 900,
                "recommended_area": 2_500_000,
                "notes": "Min 460mm each side of toilet"
            },
            "office_workstation": {
                "min_area": 4_800_000,
                "min_width": 1500,
                "recommended_area": 6_000_000,
                "notes": "Min 900mm behind desk for chair movement"
            },
        }

        std = standards.get(room_type, standards["bedroom"])
        area = room_width * room_depth
        checks = {
            "width_ok": room_width >= std["min_width"],
            "area_ok": area >= std["min_area"],
            "width_recommended": room_width >= std["min_width"] * 1.2,
            "area_recommended": area >= std["recommended_area"],
        }

        status = "PASS" if checks["width_ok"] and checks["area_ok"] else "FAIL"

        return {
            "room_type": room_type,
            "room_dimensions": {"width": room_width, "depth": room_depth},
            "area_sqm": round(area / 1_000_000, 2),
            "min_width_mm": std["min_width"],
            "min_area_sqm": round(std["min_area"] / 1_000_000, 2),
            "recommended_area_sqm": round(std["recommended_area"] / 1_000_000, 2),
            "compliance": checks,
            "status": status,
            "notes": std["notes"],
            "message": f"{room_type} {status}: {room_width}x{room_depth}mm = {round(area/1_000_000,2)}sqm"
        }

    # ------------------------------------------------------------------
    # KITCHEN WORK TRIANGLE
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_kitchen_work_triangle(
        sink_x: float, sink_y: float,
        hob_x: float, hob_y: float,
        fridge_x: float, fridge_y: float,
        layer: str = "A-FURN"
    ) -> dict:
        """
        Draw the kitchen work triangle between sink, hob (cooktop), and fridge.
        Checks against standard guidelines:
          • Each leg: 1200–2700mm
          • Total perimeter: 4000–8000mm
        Places labelled markers at each vertex and draws the triangle with analysis.
        Covers curriculum: Anthropometry in kitchen design.
        """
        space = get_model_space()
        handles = []

        pts_dict = {
            "sink": (sink_x, sink_y),
            "hob": (hob_x, hob_y),
            "fridge": (fridge_x, fridge_y),
        }

        def dist(a, b):
            return math.hypot(b[0] - a[0], b[1] - a[1])

        legs = {
            "sink_to_hob": dist(pts_dict["sink"], pts_dict["hob"]),
            "hob_to_fridge": dist(pts_dict["hob"], pts_dict["fridge"]),
            "fridge_to_sink": dist(pts_dict["fridge"], pts_dict["sink"]),
        }
        perimeter = sum(legs.values())

        # Draw triangle
        tri_pts = [sink_x, sink_y, hob_x, hob_y, fridge_x, fridge_y, sink_x, sink_y]
        tri = _polyline(space, tri_pts, closed=True)
        tri.Layer = layer; handles.append(tri.Handle)

        # Labels at vertices
        for name, (px, py) in pts_dict.items():
            c = _circle(space, px, py, 150)
            c.Layer = layer; handles.append(c.Handle)
            t = space.AddText(name.upper(), point(px, py + 200), 60)
            t.Layer = layer; handles.append(t.Handle)

        # Leg length annotations (mid-points)
        for (a_name, b_name, leg_key) in [
            ("sink", "hob", "sink_to_hob"),
            ("hob", "fridge", "hob_to_fridge"),
            ("fridge", "sink", "fridge_to_sink"),
        ]:
            a, b = pts_dict[a_name], pts_dict[b_name]
            mx = (a[0] + b[0]) / 2
            my = (a[1] + b[1]) / 2
            d = legs[leg_key]
            color = "OK" if 1200 <= d <= 2700 else "WARNING"
            t = space.AddText(f"{round(d)}mm [{color}]", point(mx, my + 80), 50)
            t.Layer = layer; handles.append(t.Handle)

        # Compliance check
        leg_checks = {k: (1200 <= v <= 2700) for k, v in legs.items()}
        perimeter_ok = 4000 <= perimeter <= 8000
        status = "COMPLIANT" if all(leg_checks.values()) and perimeter_ok else "NON-COMPLIANT"

        summary = space.AddText(
            f"WORK TRIANGLE: {round(perimeter)}mm [{status}]",
            point(min(sink_x, hob_x, fridge_x), min(sink_y, hob_y, fridge_y) - 200),
            60
        )
        summary.Layer = layer; handles.append(summary.Handle)

        return {
            "legs_mm": {k: round(v) for k, v in legs.items()},
            "perimeter_mm": round(perimeter),
            "perimeter_ok": perimeter_ok,
            "leg_compliance": leg_checks,
            "status": status,
            "guidelines": "Each leg 1200–2700mm, perimeter 4000–8000mm",
            "message": f"Kitchen work triangle {status}: perimeter={round(perimeter)}mm"
        }

    # ------------------------------------------------------------------
    # FURNITURE ERGONOMIC DIMENSIONS TABLE
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_ergonomic_dimensions_table(
        origin_x: float, origin_y: float,
        category: str = "all",
        layer: str = "A-ANNO-TEXT"
    ) -> dict:
        """
        Draw a reference table of standard ergonomic dimensions in the drawing.
        category: 'seating', 'storage', 'tables', 'bathroom', 'kitchen', 'all'
        Useful for design reference sheets and client presentations.
        """
        space = get_model_space()
        handles = []

        data = {
            "seating": [
                ("Seat height",         "430–460mm"),
                ("Seat depth",          "380–420mm"),
                ("Seat width",          "450–500mm"),
                ("Back height",         "300–400mm above seat"),
                ("Armrest height",      "230mm above seat"),
                ("Dining table height", "720–760mm"),
                ("Coffee table height", "400–450mm"),
            ],
            "storage": [
                ("Wardrobe hanging rod", "1700–1800mm"),
                ("Shelf spacing (books)", "300–320mm"),
                ("Shelf spacing (clothes)", "450–500mm"),
                ("Max shelf reach",      "1900mm from floor"),
                ("Base cabinet height",  "850–900mm"),
                ("Wall cabinet base",    "1450–1500mm from floor"),
            ],
            "tables": [
                ("Dining table H",       "720–760mm"),
                ("Desk/Work table H",    "720–750mm"),
                ("Kitchen counter H",    "850–900mm"),
                ("Bar counter H",        "1050–1100mm"),
                ("Coffee table H",       "400–450mm"),
            ],
            "bathroom": [
                ("Vanity height",        "800–850mm"),
                ("Shower head height",   "2000–2100mm"),
                ("Towel bar height",     "1200–1500mm"),
                ("Toilet seat height",   "400–430mm"),
                ("Mirror centre",        "1500–1650mm from floor"),
                ("Min shower size",      "900x900mm"),
            ],
            "kitchen": [
                ("Counter height",       "850–900mm"),
                ("Counter depth",        "600mm"),
                ("Wall cabinet base",    "1450mm"),
                ("Overhead clearance",   "450mm above counter"),
                ("Min work corridor",    "1200mm between counters"),
                ("Sink centre",          "900–1050mm from floor"),
            ],
        }

        if category == "all":
            rows = []
            for cat, items in data.items():
                rows.append((cat.upper(), ""))
                rows.extend(items)
        else:
            rows = data.get(category, [])

        # Table header
        col_w1, col_w2 = 500, 400
        row_h = 70
        x, y = origin_x, origin_y + len(rows) * row_h

        header_bg_pts = [x, y, x+col_w1+col_w2, y,
                         x+col_w1+col_w2, y+row_h, x, y+row_h, x, y]
        hdr = _polyline(space, header_bg_pts, closed=True)
        hdr.Layer = layer; handles.append(hdr.Handle)

        ht = space.AddText(f"ERGONOMIC DIMENSIONS — {category.upper()}", point(x+10, y+20), 35)
        ht.Layer = layer; handles.append(ht.Handle)

        for i, row in enumerate(rows):
            ry = origin_y + (len(rows) - 1 - i) * row_h
            if isinstance(row, tuple) and len(row) == 2:
                dim_name, dim_val = row
                # Row lines
                rp = [x, ry, x+col_w1+col_w2, ry,
                      x+col_w1+col_w2, ry+row_h, x, ry+row_h, x, ry]
                rpl = _polyline(space, rp, closed=True)
                rpl.Layer = layer; handles.append(rpl.Handle)

                if dim_val == "":
                    # Category header row
                    ct = space.AddText(dim_name, point(x+10, ry+20), 32)
                    ct.Layer = layer; handles.append(ct.Handle)
                else:
                    t1 = space.AddText(dim_name, point(x+10, ry+20), 28)
                    t1.Layer = layer; handles.append(t1.Handle)
                    t2 = space.AddText(dim_val, point(x+col_w1+10, ry+20), 28)
                    t2.Layer = layer; handles.append(t2.Handle)
                    # Divider between columns
                    dl = _line(space, x+col_w1, ry, x+col_w1, ry+row_h)
                    dl.Layer = layer; handles.append(dl.Handle)

        return {
            "category": category,
            "rows": len(rows),
            "origin": [origin_x, origin_y],
            "table_size": [col_w1+col_w2, (len(rows)+1)*row_h],
            "message": f"Ergonomic dimensions table ({category}) drawn at ({origin_x},{origin_y})"
        }

    # ------------------------------------------------------------------
    # COUNTER-HEIGHT / ELEVATION STANDARD LINES
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_elevation_height_standards(
        x: float, y: float,
        width: float = 3000.0,
        show_human: bool = True,
        layer: str = "A-ANNO-DIMS"
    ) -> dict:
        """
        Draw standard height reference lines in an elevation view:
        floor, knee, seat, counter, work surface, switch, eye level,
        shelf reach, door head, ceiling.
        Essential for elevation drawing set-up.
        Covers curriculum: Anthropometry for interior elevations.
        """
        space = get_model_space()
        handles = []

        height_standards = [
            (0,    "FLOOR LEVEL", "CONTINUOUS"),
            (430,  "SEAT HEIGHT 430mm", "DASHED"),
            (745,  "COUNTER/KNUCKLE 745mm", "DASHED"),
            (870,  "KITCHEN COUNTER 870mm", "DASHED"),
            (1050, "ELBOW/SWITCH HEIGHT 1050mm", "DASHED"),
            (1200, "DOOR HANDLE 1200mm", "DASHED"),
            (1430, "SHOULDER HEIGHT 1430mm", "DASHED"),
            (1500, "WALL UNIT BASE 1500mm", "DASHED"),
            (1620, "EYE LEVEL 1620mm", "DASHDOT"),
            (1750, "STANDING HEIGHT 1750mm", "DASHDOT"),
            (1900, "MAX REACH 1900mm", "DASHED"),
            (2100, "DOOR HEAD 2100mm", "CONTINUOUS"),
            (2400, "WALL UNIT TOP 2400mm", "DASHED"),
            (2700, "CEILING (STANDARD) 2700mm", "CONTINUOUS"),
        ]

        for h, label, ltype in height_standards:
            ln = _line(space, x, y + h, x + width, y + h)
            ln.Layer = layer
            try:
                ln.Linetype = ltype
            except Exception:
                pass
            handles.append(ln.Handle)

            t = space.AddText(label, point(x + width + 30, y + h - 10), 30)
            t.Layer = layer; handles.append(t.Handle)

        if show_human:
            # Simple stick figure at 1750mm
            hx = x + width * 0.1
            head = _circle(space, hx, y + 1650, 100)
            head.Layer = layer; handles.append(head.Handle)
            body = _line(space, hx, y + 1550, hx, y + 950)
            body.Layer = layer; handles.append(body.Handle)

        return {
            "origin": [x, y],
            "width": width,
            "height_lines": len(height_standards),
            "message": f"Elevation height standards drawn ({len(height_standards)} reference lines)"
        }
