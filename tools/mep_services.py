"""
tools/mep_services.py
MEP (Mechanical, Electrical, Plumbing) Services tools.
Maps to B.Des Interior Design vocational skills:
  • Interior lighting and Electrification
  • Plumbing & Sanitation
  • Air conditioning

Covers:
  • Electrical layout (outlets, switches, panel schedule, circuit lines)
  • Lighting layout (downlights, fluorescent strips, pendants, track lighting)
  • Plumbing layout (supply/waste/vent symbols, pipe runs, fixture connections)
  • HVAC / AC layout (units, diffusers, grilles, ductwork)
  • Smoke/fire detection layout
  • Data/comms points
  • Service legend and symbol key
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_model_space, point


def _var(coords):
    return win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(c) for c in coords]
    )


def _polyline(space, pts, closed=False):
    pl = space.AddLightWeightPolyline(_var(pts))
    if closed:
        pl.Closed = True
    return pl


def _circle(space, cx, cy, r):
    return space.AddCircle(point(cx, cy), r)


def _line(space, x1, y1, x2, y2):
    return space.AddLine(point(x1, y1), point(x2, y2))


def _text(space, txt, tx, ty, h=30, layer="A-ANNO-TEXT"):
    t = space.AddText(str(txt), point(tx, ty), h)
    t.Layer = layer
    return t


def register_mep_services_tools(mcp):

    # ==================================================================
    # ELECTRICAL
    # ==================================================================

    @mcp.tool()
    def place_power_outlet(
        x: float, y: float,
        outlet_type: str = "single",
        voltage: str = "230V",
        height_aff: float = 300.0,
        layer: str = "E-POWR"
    ) -> dict:
        """
        Place a power outlet symbol at (x, y).
        outlet_type: 'single', 'double', 'triple', 'gfci', 'floor', '20A', 'data+power'
        height_aff: height above finished floor in mm (annotation only).
        Returns the handle of the outlet symbol group.
        """
        space = get_model_space()
        handles = []
        r = 75

        # Base circle
        c = _circle(space, x, y, r)
        c.Layer = layer; handles.append(c.Handle)

        # Half-circle fill (wall side indicator)
        arc = space.AddArc(point(x, y), r, math.radians(0), math.radians(180))
        arc.Layer = layer; handles.append(arc.Handle)

        # Type markers inside
        type_symbols = {
            "single": [(x, y - r * 0.3, x, y + r * 0.3)],
            "double": [(x - r*0.25, y-r*0.3, x-r*0.25, y+r*0.3),
                       (x + r*0.25, y-r*0.3, x+r*0.25, y+r*0.3)],
            "triple": [(x - r*0.4, y-r*0.3, x-r*0.4, y+r*0.3),
                       (x,          y-r*0.3, x,          y+r*0.3),
                       (x + r*0.4, y-r*0.3, x+r*0.4, y+r*0.3)],
            "gfci":   [(x-r*0.3, y, x+r*0.3, y)],   # horizontal bar = GFCI
            "floor":  [(x, y-r*0.5, x, y+r*0.5), (x-r*0.5, y, x+r*0.5, y)],  # cross
            "20A":    [],  # label only
            "data+power": [(x-r*0.3, y-r*0.3, x+r*0.3, y+r*0.3)],  # diagonal
        }
        for ln_pts in type_symbols.get(outlet_type, []):
            ln = _line(space, *ln_pts)
            ln.Layer = layer; handles.append(ln.Handle)

        # Label
        label = f"{outlet_type.upper()}\n{voltage}"
        if height_aff:
            label += f"\n{int(height_aff)}AFF"
        t = _text(space, label.replace("\n", " "), x + r + 30, y, 25, layer)
        handles.append(t.Handle)

        return {
            "position": [x, y],
            "outlet_type": outlet_type,
            "voltage": voltage,
            "height_aff": height_aff,
            "handles": handles,
            "message": f"{outlet_type} outlet placed at ({x},{y})"
        }

    @mcp.tool()
    def place_light_switch(
        x: float, y: float,
        switch_type: str = "single",
        height_aff: float = 1200.0,
        layer: str = "E-LITE"
    ) -> dict:
        """
        Place a light switch symbol.
        switch_type: 'single', 'double', 'triple', 'dimmer', '2way', '3way'
        height_aff: switch height above finished floor (typically 1200mm).
        """
        space = get_model_space()
        handles = []
        r = 60

        # Square symbol body
        s = r * 1.2
        sq_pts = [x-s, y-s, x+s, y-s, x+s, y+s, x-s, y+s, x-s, y-s]
        sq = _polyline(space, sq_pts, closed=True)
        sq.Layer = layer; handles.append(sq.Handle)

        # Internal markings
        if switch_type in ("single", "double", "triple"):
            count = {"single": 1, "double": 2, "triple": 3}[switch_type]
            for i in range(count):
                ix = x + (i - (count-1)/2) * s * 0.6
                ln = _line(space, ix, y - s * 0.5, ix, y + s * 0.5)
                ln.Layer = layer; handles.append(ln.Handle)
        elif switch_type == "dimmer":
            # Diagonal arrow
            arr = _line(space, x - s*0.5, y - s*0.5, x + s*0.5, y + s*0.5)
            arr.Layer = layer; handles.append(arr.Handle)
        elif switch_type == "2way":
            t_mark = _text(space, "2W", x, y - 5, 30, layer)
            handles.append(t_mark.Handle)
        elif switch_type == "3way":
            t_mark = _text(space, "3W", x, y - 5, 30, layer)
            handles.append(t_mark.Handle)

        t = _text(space, f"S{switch_type[0].upper()} {int(height_aff)}AFF", x + s + 20, y, 25, layer)
        handles.append(t.Handle)

        return {
            "position": [x, y],
            "switch_type": switch_type,
            "height_aff": height_aff,
            "handles": handles,
            "message": f"{switch_type} switch at ({x},{y}), {height_aff}mm AFF"
        }

    @mcp.tool()
    def draw_electrical_circuit(
        points: list,
        circuit_id: str = "C1",
        circuit_type: str = "lighting",
        layer: str = "E-WIRE"
    ) -> dict:
        """
        Draw an electrical circuit run as a polyline connecting fixtures/outlets.
        points: list of [x, y] pairs defining the circuit path.
        circuit_type: 'lighting', 'power', 'dedicated', 'data', 'emergency'
        Each type uses a different linetype/color convention.
        """
        space = get_model_space()

        linetypes = {
            "lighting":   "DASHED",
            "power":      "CONTINUOUS",
            "dedicated":  "HIDDEN",
            "data":       "DASHDOT",
            "emergency":  "PHANTOM",
        }
        colors = {
            "lighting":   3,   # green
            "power":      1,   # red
            "dedicated":  6,   # magenta
            "data":       4,   # cyan
            "emergency":  1,   # red
        }

        flat = []
        for p in points:
            flat.extend([float(p[0]), float(p[1])])
        pl = _polyline(space, flat)
        pl.Layer = layer
        pl.Linetype = linetypes.get(circuit_type, "DASHED")
        pl.color = colors.get(circuit_type, 3)

        # Circuit ID label at midpoint
        mid_idx = len(points) // 2
        mx, my = points[mid_idx][0], points[mid_idx][1]
        _text(space, circuit_id, mx, my + 60, 40, layer)

        return {
            "circuit_id": circuit_id,
            "circuit_type": circuit_type,
            "points": len(points),
            "circuit_handle": pl.Handle,
            "message": f"Circuit {circuit_id} ({circuit_type}) drawn through {len(points)} points"
        }

    @mcp.tool()
    def draw_electrical_panel(
        origin_x: float, origin_y: float,
        panel_name: str = "MDB",
        circuits: list = None,
        layer: str = "E-POWR"
    ) -> dict:
        """
        Draw an electrical panel/distribution board symbol with a circuit schedule table.
        circuits: list of dicts, each with keys: id, type, rating, load (watts), description.
        Example: [{"id": "C1", "type": "lighting", "rating": "10A", "load": 500, "description": "Living Room"}]
        """
        space = get_model_space()
        handles = []

        if circuits is None:
            circuits = []

        # Panel symbol (rectangle with symbol)
        pw, ph = 400, 600
        panel_pts = [origin_x, origin_y, origin_x+pw, origin_y,
                     origin_x+pw, origin_y+ph, origin_x, origin_y+ph, origin_x, origin_y]
        panel = _polyline(space, panel_pts, closed=True)
        panel.Layer = layer; handles.append(panel.Handle)

        # X cross inside panel symbol
        for pts in [(origin_x, origin_y, origin_x+pw, origin_y+ph),
                    (origin_x+pw, origin_y, origin_x, origin_y+ph)]:
            ln = _line(space, *pts)
            ln.Layer = layer; handles.append(ln.Handle)

        ht = _text(space, panel_name, origin_x + pw/2, origin_y + ph + 30, 60, layer)
        handles.append(ht.Handle)

        # Circuit schedule table
        if circuits:
            tx = origin_x + pw + 100
            ty = origin_y + ph
            row_h, col1_w, col2_w, col3_w, col4_w = 60, 80, 120, 100, 300

            # Header
            headers = ["ID", "RATING", "LOAD", "DESCRIPTION"]
            widths = [col1_w, col2_w, col3_w, col4_w]
            cx = tx
            for hdr, w in zip(headers, widths):
                hp = [cx, ty-row_h, cx+w, ty-row_h, cx+w, ty, cx, ty, cx, ty-row_h]
                hpl = _polyline(space, hp, closed=True)
                hpl.Layer = layer; handles.append(hpl.Handle)
                ht2 = _text(space, hdr, cx + 8, ty - row_h + 18, 28, layer)
                handles.append(ht2.Handle)
                cx += w

            # Data rows
            for i, circ in enumerate(circuits):
                ry = ty - (i + 2) * row_h
                row_data = [
                    circ.get("id", ""),
                    circ.get("rating", ""),
                    f"{circ.get('load', '')}W",
                    circ.get("description", ""),
                ]
                cx = tx
                for val, w in zip(row_data, widths):
                    cp = [cx, ry, cx+w, ry, cx+w, ry+row_h, cx, ry+row_h, cx, ry]
                    cpl = _polyline(space, cp, closed=True)
                    cpl.Layer = layer; handles.append(cpl.Handle)
                    ct = _text(space, str(val), cx + 8, ry + 18, 25, layer)
                    handles.append(ct.Handle)
                    cx += w

        return {
            "panel_name": panel_name,
            "circuits": len(circuits),
            "origin": [origin_x, origin_y],
            "handles_count": len(handles),
            "message": f"Electrical panel '{panel_name}' drawn with {len(circuits)} circuits"
        }

    # ==================================================================
    # PLUMBING
    # ==================================================================

    @mcp.tool()
    def draw_plumbing_symbol(
        x: float, y: float,
        symbol_type: str,
        layer: str = "P-PIPE"
    ) -> dict:
        """
        Place a standard plumbing symbol at (x, y).
        symbol_type:
          'cold_supply', 'hot_supply', 'waste', 'vent',
          'floor_drain', 'cleanout', 'water_heater',
          'gate_valve', 'ball_valve', 'check_valve',
          'hose_bib', 'p_trap', 'shower_drain'
        """
        space = get_model_space()
        handles = []
        r = 80

        if symbol_type == "cold_supply":
            c = _circle(space, x, y, r); c.Layer = layer; handles.append(c.Handle)
            ln = _line(space, x - r*0.6, y, x + r*0.6, y)
            ln.Layer = layer; handles.append(ln.Handle)
            t = _text(space, "CW", x, y - r - 35, 30, layer)
            handles.append(t.Handle)

        elif symbol_type == "hot_supply":
            c = _circle(space, x, y, r); c.Layer = layer; handles.append(c.Handle)
            for i in range(3):  # three arcs to suggest heat
                arc = space.AddArc(point(x - r*0.3 + i*r*0.3, y), r*0.3,
                                   math.radians(0), math.radians(180))
                arc.Layer = layer; handles.append(arc.Handle)
            t = _text(space, "HW", x, y - r - 35, 30, layer)
            handles.append(t.Handle)

        elif symbol_type in ("waste", "vent"):
            # Dashed circle
            c = _circle(space, x, y, r); c.Layer = layer
            c.Linetype = "DASHED"; handles.append(c.Handle)
            t = _text(space, symbol_type[0].upper(), x - 15, y - 12, 40, layer)
            handles.append(t.Handle)

        elif symbol_type == "floor_drain":
            c = _circle(space, x, y, r); c.Layer = layer; handles.append(c.Handle)
            c2 = _circle(space, x, y, r * 0.4); c2.Layer = layer; handles.append(c2.Handle)
            for ang in [45, 135, 225, 315]:
                a = math.radians(ang)
                ln = _line(space, x + r*0.4*math.cos(a), y + r*0.4*math.sin(a),
                           x + r*math.cos(a), y + r*math.sin(a))
                ln.Layer = layer; handles.append(ln.Handle)
            t = _text(space, "FD", x + r + 20, y, 30, layer)
            handles.append(t.Handle)

        elif symbol_type == "cleanout":
            # Double circle with CO
            c = _circle(space, x, y, r); c.Layer = layer; handles.append(c.Handle)
            c2 = _circle(space, x, y, r*0.6); c2.Layer = layer; handles.append(c2.Handle)
            t = _text(space, "CO", x - 20, y - 12, 35, layer)
            handles.append(t.Handle)

        elif symbol_type == "water_heater":
            # Rectangle with WH
            s = r * 1.5
            wh_pts = [x-s, y-s*1.5, x+s, y-s*1.5, x+s, y+s*1.5, x-s, y+s*1.5, x-s, y-s*1.5]
            wh = _polyline(space, wh_pts, closed=True)
            wh.Layer = layer; handles.append(wh.Handle)
            c = _circle(space, x, y, s*0.6); c.Layer = layer; handles.append(c.Handle)
            t = _text(space, "WH", x - 25, y - 15, 40, layer)
            handles.append(t.Handle)

        elif symbol_type in ("gate_valve", "ball_valve", "check_valve"):
            # Bowtie or circle symbol
            c = _circle(space, x, y, r*0.4); c.Layer = layer; handles.append(c.Handle)
            ln1 = _line(space, x - r, y, x + r, y)
            ln1.Layer = layer; handles.append(ln1.Handle)
            if symbol_type == "gate_valve":
                # Diamond at centre
                d_pts = [x, y - r*0.4, x + r*0.4, y, x, y + r*0.4, x - r*0.4, y, x, y - r*0.4]
                d = _polyline(space, d_pts, closed=True)
                d.Layer = layer; handles.append(d.Handle)
            t = _text(space, symbol_type[:2].upper(), x, y - r - 35, 25, layer)
            handles.append(t.Handle)

        elif symbol_type == "shower_drain":
            c = _circle(space, x, y, r); c.Layer = layer; handles.append(c.Handle)
            for i in range(4):
                a = math.radians(i * 90)
                ln = _line(space, x, y, x + r * math.cos(a), y + r * math.sin(a))
                ln.Layer = layer; handles.append(ln.Handle)
            t = _text(space, "SD", x + r + 15, y, 30, layer)
            handles.append(t.Handle)

        else:
            # Generic: circle + label
            c = _circle(space, x, y, r); c.Layer = layer; handles.append(c.Handle)
            t = _text(space, symbol_type[:3].upper(), x - 20, y - 12, 35, layer)
            handles.append(t.Handle)

        return {
            "symbol_type": symbol_type,
            "position": [x, y],
            "handles": handles,
            "message": f"Plumbing symbol '{symbol_type}' placed at ({x},{y})"
        }

    @mcp.tool()
    def draw_pipe_run(
        points: list,
        pipe_type: str = "cold_supply",
        pipe_size: str = "15mm",
        layer: str = "P-PIPE"
    ) -> dict:
        """
        Draw a pipe run through a series of [x,y] points.
        pipe_type: 'cold_supply', 'hot_supply', 'waste', 'vent', 'gas', 'rainwater'
        Each type uses standard linetype and colour conventions.
        """
        space = get_model_space()

        config = {
            "cold_supply": {"color": 4, "linetype": "CONTINUOUS", "abbr": "CW"},
            "hot_supply":  {"color": 1, "linetype": "DASHED",     "abbr": "HW"},
            "waste":       {"color": 6, "linetype": "HIDDEN",      "abbr": "W"},
            "vent":        {"color": 3, "linetype": "DASHDOT",     "abbr": "V"},
            "gas":         {"color": 2, "linetype": "PHANTOM",     "abbr": "G"},
            "rainwater":   {"color": 5, "linetype": "DASHED",      "abbr": "RW"},
        }
        cfg = config.get(pipe_type, {"color": 256, "linetype": "CONTINUOUS", "abbr": "P"})

        flat = []
        for p in points:
            flat.extend([float(p[0]), float(p[1])])
        pl = _polyline(space, flat)
        pl.Layer = layer
        pl.Linetype = cfg["linetype"]
        pl.color = cfg["color"]

        # Size callout at midpoint
        mid = len(points) // 2
        mx, my = float(points[mid][0]), float(points[mid][1])
        _text(space, f"{cfg['abbr']} Ø{pipe_size}", mx, my + 60, 35, layer)

        return {
            "pipe_type": pipe_type,
            "pipe_size": pipe_size,
            "points": len(points),
            "handle": pl.Handle,
            "message": f"{pipe_type} pipe run ({pipe_size}) through {len(points)} points"
        }

    @mcp.tool()
    def draw_wet_room_plumbing(
        origin_x: float, origin_y: float,
        room_width: float,
        room_depth: float,
        layout: str = "standard",
        layer: str = "P-PIPE"
    ) -> dict:
        """
        Draw a complete wet room plumbing layout showing supply, waste,
        and vent connections for a bathroom/wet area.
        layout: 'standard' (bath + WC + basin), 'ensuite' (shower + WC + basin),
                'wetroom' (open shower), 'kitchen'
        Draws: fixture outlines, supply lines (cold/hot), waste lines, floor drain.
        """
        space = get_model_space()
        handles = []
        ox, oy = origin_x, origin_y
        W, D = room_width, room_depth

        # Room boundary
        rm_pts = [ox, oy, ox+W, oy, ox+W, oy+D, ox, oy+D, ox, oy]
        rm = _polyline(space, rm_pts, closed=True)
        rm.Layer = "A-WALL"; handles.append(rm.Handle)

        def _place(sym, sx, sy):
            c = _circle(space, sx, sy, 80)
            c.Layer = layer; handles.append(c.Handle)
            t = _text(space, sym, sx, sy - 120, 35, layer)
            handles.append(t.Handle)
            return (sx, sy)

        if layout == "standard":
            # WC bottom-left, Basin top-left, Bath right
            wc   = _place("WC",    ox + 400, oy + 400)
            basin= _place("BASIN", ox + 400, oy + D - 400)
            bath = _place("BATH",  ox + W - 900, oy + D/2)
            fixtures = [wc, basin, bath]

        elif layout == "ensuite":
            wc     = _place("WC",     ox + 350, oy + 350)
            basin  = _place("BASIN",  ox + W - 350, oy + 350)
            shower = _place("SHOWER", ox + W/2, oy + D - 400)
            fixtures = [wc, basin, shower]

        elif layout == "wetroom":
            basin  = _place("BASIN",  ox + 350, oy + D - 350)
            shower = _place("SHOWER", ox + W/2, oy + D/2)
            _place("FD", ox + W/2, oy + 300)   # floor drain at low point
            fixtures = [basin, shower]

        elif layout == "kitchen":
            sink   = _place("SINK",   ox + W/2, oy + D - 350)
            dw     = _place("D/W",    ox + W/2 + 600, oy + D - 350)
            fixtures = [sink, dw]

        else:
            fixtures = []

        # Cold and hot supply mains (from left wall)
        if fixtures:
            cw_y = oy + 200
            hw_y = oy + 300
            cw_main = space.AddLine(point(ox, cw_y), point(ox + W, cw_y))
            cw_main.Layer = layer; cw_main.color = 4; handles.append(cw_main.Handle)
            hw_main = space.AddLine(point(ox, hw_y), point(ox + W, hw_y))
            hw_main.Layer = layer; hw_main.color = 1; handles.append(hw_main.Handle)
            cw_lbl = _text(space, "CW SUPPLY MAIN", ox + 20, cw_y + 30, 25, layer)
            handles.append(cw_lbl.Handle)
            hw_lbl = _text(space, "HW SUPPLY MAIN", ox + 20, hw_y + 30, 25, layer)
            handles.append(hw_lbl.Handle)

            # Branches to each fixture
            for fx, fy in fixtures:
                for main_y, color in [(cw_y, 4), (hw_y, 1)]:
                    br = space.AddLine(point(fx, main_y), point(fx, fy))
                    br.Layer = layer; br.color = color; br.Linetype = "DASHED"
                    handles.append(br.Handle)

            # Waste main (bottom of room)
            wm = space.AddLine(point(ox, oy + 150), point(ox + W, oy + 150))
            wm.Layer = layer; wm.color = 6; handles.append(wm.Handle)
            wm_lbl = _text(space, "WASTE MAIN", ox + 20, oy + 170, 25, layer)
            handles.append(wm_lbl.Handle)
            for fx, fy in fixtures:
                wb = space.AddLine(point(fx, oy + 150), point(fx, fy))
                wb.Layer = layer; wb.color = 6; wb.Linetype = "HIDDEN"
                handles.append(wb.Handle)

        return {
            "layout": layout,
            "room_size": [room_width, room_depth],
            "fixtures": len(fixtures),
            "handles_count": len(handles),
            "message": f"Wet room plumbing layout '{layout}' drawn ({room_width}x{room_depth}mm)"
        }

    # ==================================================================
    # HVAC / AIR CONDITIONING
    # ==================================================================

    @mcp.tool()
    def place_ac_unit(
        x: float, y: float,
        unit_type: str = "split_indoor",
        width: float = 800.0,
        height: float = 250.0,
        rotation_deg: float = 0.0,
        layer: str = "M-HVAC"
    ) -> dict:
        """
        Place an AC unit symbol (plan or elevation).
        unit_type: 'split_indoor', 'split_outdoor', 'cassette', 'ducted',
                   'floor_standing', 'window'
        """
        space = get_model_space()
        handles = []

        rot = math.radians(rotation_deg)
        W, H = width / 2, height / 2

        def _rotpt(dx, dy):
            rx = x + dx * math.cos(rot) - dy * math.sin(rot)
            ry = y + dx * math.sin(rot) + dy * math.cos(rot)
            return rx, ry

        corners = [_rotpt(-W, -H), _rotpt(W, -H), _rotpt(W, H), _rotpt(-W, H)]
        pts = []
        for cx2, cy2 in corners:
            pts.extend([cx2, cy2])
        pts.extend(pts[:2])
        body = _polyline(space, pts, closed=True)
        body.Layer = layer; handles.append(body.Handle)

        # Internal symbol based on type
        if unit_type in ("split_indoor", "floor_standing", "window"):
            # Horizontal airflow fins
            for i in range(3):
                fy = -H * 0.4 + i * H * 0.4
                p1 = _rotpt(-W * 0.7, fy)
                p2 = _rotpt(W * 0.7, fy)
                ln = _line(space, *p1, *p2)
                ln.Layer = layer; handles.append(ln.Handle)

        elif unit_type == "cassette":
            # Four-way diffuser symbol: circle with 4 arrows
            cr = _circle(space, x, y, min(W, H) * 0.5)
            cr.Layer = layer; handles.append(cr.Handle)
            for ang in [0, 90, 180, 270]:
                a = math.radians(ang)
                inner_r = min(W, H) * 0.3
                outer_r = min(W, H) * 0.8
                p1 = _rotpt(inner_r * math.cos(a), inner_r * math.sin(a))
                p2 = _rotpt(outer_r * math.cos(a), outer_r * math.sin(a))
                ln = _line(space, *p1, *p2)
                ln.Layer = layer; handles.append(ln.Handle)

        elif unit_type == "split_outdoor":
            # Grid pattern for condenser fins
            for i in range(4):
                fx = -W * 0.6 + i * W * 0.4
                ln = _line(space, *_rotpt(fx, -H * 0.7), *_rotpt(fx, H * 0.7))
                ln.Layer = layer; handles.append(ln.Handle)

        t = _text(space, unit_type.upper().replace("_", "\n"), *_rotpt(0, -H - 50), 30, layer)
        handles.append(t.Handle)

        return {
            "unit_type": unit_type,
            "position": [x, y],
            "size": [width, height],
            "rotation": rotation_deg,
            "handles": handles,
            "message": f"AC unit ({unit_type}) placed at ({x},{y})"
        }

    @mcp.tool()
    def draw_ac_diffuser(
        x: float, y: float,
        diffuser_type: str = "square",
        size: float = 300.0,
        cfm: float = 0.0,
        layer: str = "M-HVAC"
    ) -> dict:
        """
        Draw an HVAC diffuser/grille symbol in plan view.
        diffuser_type: 'square', 'round', 'linear', 'slot'
        size: face size in mm.
        cfm: airflow in CFM (annotated if non-zero).
        """
        space = get_model_space()
        handles = []
        s = size / 2

        if diffuser_type == "square":
            sq_pts = [x-s, y-s, x+s, y-s, x+s, y+s, x-s, y+s, x-s, y-s]
            sq = _polyline(space, sq_pts, closed=True)
            sq.Layer = layer; handles.append(sq.Handle)
            # Cross lines
            for pts in [(x-s, y, x+s, y), (x, y-s, x, y+s)]:
                ln = _line(space, *pts)
                ln.Layer = layer; handles.append(ln.Handle)
            # Diagonal lines (supply pattern)
            for pts in [(x-s, y-s, x+s, y+s), (x+s, y-s, x-s, y+s)]:
                ln = _line(space, *pts)
                ln.Layer = layer; handles.append(ln.Handle)

        elif diffuser_type == "round":
            c = _circle(space, x, y, s)
            c.Layer = layer; handles.append(c.Handle)
            c2 = _circle(space, x, y, s * 0.6)
            c2.Layer = layer; handles.append(c2.Handle)
            for ang in [0, 45, 90, 135]:
                a = math.radians(ang)
                ln = _line(space, x + s*0.6*math.cos(a), y + s*0.6*math.sin(a),
                           x + s*math.cos(a), y + s*math.sin(a))
                ln.Layer = layer; handles.append(ln.Handle)

        elif diffuser_type == "linear":
            # Long rectangle
            rp = [x - s*3, y - s*0.3, x + s*3, y - s*0.3,
                  x + s*3, y + s*0.3, x - s*3, y + s*0.3, x - s*3, y - s*0.3]
            rpl = _polyline(space, rp, closed=True)
            rpl.Layer = layer; handles.append(rpl.Handle)
            for i in range(7):
                ix = x - s*3 + i * s
                ln = _line(space, ix, y - s*0.3, ix, y + s*0.3)
                ln.Layer = layer; handles.append(ln.Handle)

        elif diffuser_type == "slot":
            rp = [x - s*2, y - s*0.15, x + s*2, y - s*0.15,
                  x + s*2, y + s*0.15, x - s*2, y + s*0.15, x - s*2, y - s*0.15]
            rpl = _polyline(space, rp, closed=True)
            rpl.Layer = layer; handles.append(rpl.Handle)

        if cfm:
            t = _text(space, f"{cfm:.0f}CFM", x + s + 30, y, 30, layer)
            handles.append(t.Handle)

        return {
            "diffuser_type": diffuser_type,
            "position": [x, y],
            "size": size,
            "cfm": cfm,
            "handles": handles,
            "message": f"{diffuser_type} diffuser placed at ({x},{y}), size={size}mm"
        }

    @mcp.tool()
    def draw_ductwork(
        points: list,
        duct_width: float = 300.0,
        duct_type: str = "supply",
        layer: str = "M-HVAC"
    ) -> dict:
        """
        Draw rectangular ductwork as a double-line run.
        points: list of [x, y] centreline points.
        duct_type: 'supply' (solid), 'return' (dashed), 'exhaust' (dotted)
        duct_width: width of duct in mm.
        """
        space = get_model_space()
        handles = []
        hw = duct_width / 2

        linetypes = {"supply": "CONTINUOUS", "return": "DASHED", "exhaust": "DASHDOT"}
        ltype = linetypes.get(duct_type, "CONTINUOUS")

        for i in range(len(points) - 1):
            x1, y1 = float(points[i][0]),   float(points[i][1])
            x2, y2 = float(points[i+1][0]), float(points[i+1][1])
            angle = math.atan2(y2 - y1, x2 - x1)
            perp = angle + math.pi / 2

            # Offset lines (duct walls)
            for sign in [-1, 1]:
                ox = sign * hw * math.cos(perp)
                oy = sign * hw * math.sin(perp)
                ln = _line(space, x1+ox, y1+oy, x2+ox, y2+oy)
                ln.Layer = layer; ln.Linetype = ltype; handles.append(ln.Handle)

        # Centreline
        flat = []
        for p in points:
            flat.extend([float(p[0]), float(p[1])])
        cl = _polyline(space, flat)
        cl.Layer = layer; cl.Linetype = "CENTER"; handles.append(cl.Handle)

        mid = len(points) // 2
        t = _text(space, f"{duct_type.upper()} DUCT {int(duct_width)}mm",
                  float(points[mid][0]), float(points[mid][1]) + hw + 40, 30, layer)
        handles.append(t.Handle)

        return {
            "duct_type": duct_type,
            "duct_width": duct_width,
            "segments": len(points) - 1,
            "handle_count": len(handles),
            "message": f"{duct_type} ductwork ({duct_width}mm) drawn"
        }

    # ==================================================================
    # FIRE / SAFETY
    # ==================================================================

    @mcp.tool()
    def place_smoke_detector(
        x: float, y: float,
        detector_type: str = "smoke",
        layer: str = "FP-DETE"
    ) -> dict:
        """
        Place a fire/smoke detection symbol.
        detector_type: 'smoke', 'heat', 'co', 'sprinkler', 'pull_station',
                       'exit_sign', 'emergency_light'
        """
        space = get_model_space()
        handles = []
        r = 100

        c = _circle(space, x, y, r)
        c.Layer = layer; handles.append(c.Handle)

        symbol_marks = {
            "smoke":   "S",
            "heat":    "H",
            "co":      "CO",
            "sprinkler": "SP",
            "pull_station": "PS",
            "exit_sign": "EXIT",
            "emergency_light": "EL",
        }
        mark = symbol_marks.get(detector_type, detector_type[:2].upper())
        t = _text(space, mark, x - len(mark)*15, y - 15, 40, layer)
        handles.append(t.Handle)

        # Sprinkler: cross symbol
        if detector_type == "sprinkler":
            for ang in [0, 90, 45, 135]:
                a = math.radians(ang)
                ln = _line(space, x - r*math.cos(a), y - r*math.sin(a),
                           x + r*math.cos(a), y + r*math.sin(a))
                ln.Layer = layer; handles.append(ln.Handle)

        return {
            "detector_type": detector_type,
            "position": [x, y],
            "handles": handles,
            "message": f"{detector_type} detector placed at ({x},{y})"
        }

    @mcp.tool()
    def draw_services_legend(
        origin_x: float, origin_y: float,
        services: list = None,
        layer: str = "A-ANNO-TEXT"
    ) -> dict:
        """
        Draw a services legend / symbol key in the drawing.
        services: list of service types to include.
        If omitted, draws all standard MEP symbols with descriptions.
        """
        space = get_model_space()
        handles = []

        all_services = [
            ("E", "E-POWR", "Power Outlet (Single)"),
            ("E2", "E-POWR", "Power Outlet (Double)"),
            ("S", "E-LITE", "Light Switch"),
            ("D", "E-LITE", "Dimmer Switch"),
            ("CW", "P-PIPE", "Cold Water Supply"),
            ("HW", "P-PIPE", "Hot Water Supply"),
            ("W", "P-PIPE", "Waste Pipe"),
            ("FD", "P-PIPE", "Floor Drain"),
            ("AC", "M-HVAC", "Split A/C Indoor Unit"),
            ("SD", "M-HVAC", "Supply Air Diffuser"),
            ("RD", "M-HVAC", "Return Air Grille"),
            ("SM", "FP-DETE", "Smoke Detector"),
            ("SP", "FP-DETE", "Sprinkler Head"),
            ("EL", "FP-DETE", "Emergency Light"),
        ]

        if services:
            filtered = [s for s in all_services if s[0] in services]
        else:
            filtered = all_services

        row_h = 100
        sym_col = 120
        text_col = 200

        # Title
        title = _text(space, "SERVICES LEGEND", origin_x, origin_y + len(filtered)*row_h + 40, 50, layer)
        handles.append(title.Handle)

        for i, (abbr, sym_layer, desc) in enumerate(filtered):
            ry = origin_y + (len(filtered) - 1 - i) * row_h
            # Symbol circle
            c = _circle(space, origin_x + sym_col/2, ry + row_h/2, 35)
            c.Layer = sym_layer; handles.append(c.Handle)
            st = _text(space, abbr, origin_x + sym_col/2 - len(abbr)*10, ry + row_h/2 - 12, 28, sym_layer)
            handles.append(st.Handle)
            # Description
            dt = _text(space, desc, origin_x + text_col, ry + row_h/2 - 12, 30, layer)
            handles.append(dt.Handle)
            # Row divider
            ln = _line(space, origin_x, ry, origin_x + 600, ry)
            ln.Layer = layer; handles.append(ln.Handle)

        # Border
        brd_pts = [origin_x, origin_y,
                   origin_x + 620, origin_y,
                   origin_x + 620, origin_y + (len(filtered)+1)*row_h,
                   origin_x, origin_y + (len(filtered)+1)*row_h,
                   origin_x, origin_y]
        brd = _polyline(space, brd_pts, closed=True)
        brd.Layer = layer; handles.append(brd.Handle)

        return {
            "services_shown": len(filtered),
            "origin": [origin_x, origin_y],
            "handles_count": len(handles),
            "message": f"Services legend drawn with {len(filtered)} symbols"
        }
