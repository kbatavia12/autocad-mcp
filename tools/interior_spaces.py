"""
tools/interior_spaces.py
Interior design space tools — rooms, walls, doors, windows, openings.
All dimensions assumed in millimetres (standard ID practice).
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_active_doc, ensure_layer, ensure_standard_linetypes, point


def register_interior_space_tools(mcp):

    # -----------------------------------------------------------------------
    # LAYER SETUP
    # -----------------------------------------------------------------------

    @mcp.tool()
    def setup_id_layers() -> str:
        """
        Create a standard interior design layer set based on AIA layer naming.
        Covers walls, doors, windows, furniture, fixtures, electrical,
        dimensions, annotations, ceiling, floor finish, and titleblock.
        """
        doc = get_active_doc()
        layers = [
            # (name,         ACI color, description)
            ("A-WALL",       1,  "Walls - full height"),
            ("A-WALL-PATT",  8,  "Wall hatching / fill"),
            ("A-DOOR",       3,  "Doors and swings"),
            ("A-GLAZ",       4,  "Windows and glazing"),
            ("A-FURN",       5,  "Loose furniture"),
            ("A-FURN-FIXD",  6,  "Fixed furniture / built-ins"),
            ("A-FIXT",       2,  "Fixtures (sanitary, kitchen)"),
            ("A-FLOR-PATT",  8,  "Floor finish / tile pattern"),
            ("A-CLNG",       7,  "Ceiling elements"),
            ("A-CLNG-GRID",  8,  "Ceiling grid / tiles"),
            ("E-LITE",       2,  "Lighting fixtures"),
            ("E-POWR",       5,  "Power outlets"),
            ("E-SWTC",       6,  "Switches"),
            ("A-DIMS",       3,  "Dimensions"),
            ("A-ANNO",       7,  "General annotations / text"),
            ("A-ANNO-ROOM",  2,  "Room names and area tags"),
            ("A-ANNO-MATL",  4,  "Material callouts"),
            ("A-ELEV",       1,  "Elevation markers"),
            ("A-SECT",       1,  "Section cut markers"),
            ("A-GRID",       8,  "Reference grid"),
            ("A-TITLE",      7,  "Title block"),
            ("A-VPRT",       8,  "Viewport borders (non-plot)"),
            ("A-XREF",       8,  "External reference geometry"),
        ]
        created = []
        for name, color, _ in layers:
            try:
                layer = doc.Layers.Add(name)
                layer.color = color
                layer.Linetype = "Continuous"
                created.append(name)
            except Exception:
                pass  # layer already exists

        return f"ID layer set created: {len(created)} layers added ({', '.join(created[:5])}...)"

    # -----------------------------------------------------------------------
    # WALLS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def draw_wall(
        x1: float, y1: float,
        x2: float, y2: float,
        thickness: float = 150.0,
        layer: str = "A-WALL"
    ) -> dict:
        """
        Draw a wall as a closed polyline with the given thickness.
        The wall runs from (x1,y1) to (x2,y2) and is extruded perpendicular by thickness.
        Returns handles for the wall outline and optional hatch.
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        ensure_layer(doc, "A-WALL-PATT", 8)
        space = doc.ModelSpace

        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            raise ValueError("Wall start and end points are the same")

        # Perpendicular unit vector
        nx = -dy / length * thickness
        ny = dx / length * thickness

        pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x1, y1,
             x2, y2,
             x2 + nx, y2 + ny,
             x1 + nx, y1 + ny]
        )
        wall = space.AddLightWeightPolyline(pts)
        wall.Closed = True
        wall.Layer = layer
        wall.Lineweight = 35  # 0.35mm — standard wall line weight

        # Hatch the wall solid
        hatch = space.AddHatch(0, "SOLID", True)
        outer = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [wall]
        )
        hatch.AppendOuterLoop(outer)
        hatch.Evaluate()
        hatch.Layer = "A-WALL-PATT"
        doc.Regen(1)

        return {
            "wall_handle": wall.Handle,
            "hatch_handle": hatch.Handle,
            "length": round(length, 1),
            "thickness": thickness,
            "message": f"Wall drawn {length:.0f}mm long × {thickness}mm thick"
        }

    @mcp.tool()
    def draw_room(
        x: float, y: float,
        width: float, depth: float,
        wall_thickness: float = 150.0,
        name: str = "",
        layer: str = "A-WALL"
    ) -> dict:
        """
        Draw a rectangular room with walls on all four sides.
        x, y: bottom-left internal corner. width, depth: internal dimensions.
        Returns handles for all 4 walls and adds a room label if name is given.
        """
        t = wall_thickness
        # Four walls: bottom, right, top, left
        walls = [
            (x - t,       y - t,       x + width + t, y),            # bottom
            (x + width,   y - t,       x + width + t, y + depth + t), # right
            (x - t,       y + depth,   x + width + t, y + depth + t), # top
            (x - t,       y - t,       x,             y + depth + t), # left
        ]
        doc = get_active_doc()
        ensure_layer(doc, layer)
        ensure_layer(doc, "A-WALL-PATT", 8)
        ensure_layer(doc, "A-ANNO-ROOM", 2)
        space = doc.ModelSpace
        handles = []
        for wx1, wy1, wx2, wy2 in walls:
            pts = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8,
                [wx1, wy1, wx2, wy1, wx2, wy2, wx1, wy2, wx1, wy1]
            )
            wall = space.AddLightWeightPolyline(pts)
            wall.Closed = True
            wall.Layer = layer
            wall.Lineweight = 35
            hatch = space.AddHatch(0, "SOLID", True)
            outer = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [wall]
            )
            hatch.AppendOuterLoop(outer)
            hatch.Evaluate()
            hatch.Layer = "A-WALL-PATT"
            handles.append(wall.Handle)

        doc.Regen(1)

        label_handle = None
        if name:
            cx = x + width / 2
            cy = y + depth / 2
            pt = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8, [cx, cy, 0.0]
            )
            txt = doc.ModelSpace.AddText(name, pt, min(width, depth) * 0.06)
            txt.Layer = "A-ANNO-ROOM"
            txt.Alignment = 4  # acAlignmentMiddleCenter
            txt.TextAlignmentPoint = pt
            label_handle = txt.Handle

        area_m2 = (width * depth) / 1e6
        return {
            "wall_handles": handles,
            "room_label_handle": label_handle,
            "internal_width": width,
            "internal_depth": depth,
            "area_m2": round(area_m2, 2),
            "message": f"Room '{name}' drawn: {width}×{depth}mm ({area_m2:.2f} m²)"
        }

    # -----------------------------------------------------------------------
    # DOORS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def add_door(
        x: float, y: float,
        width: float = 900.0,
        rotation_deg: float = 0.0,
        swing_direction: str = "left",
        layer: str = "A-DOOR"
    ) -> dict:
        """
        Draw a door symbol (opening + swing arc) at the given position.
        width: door leaf width in mm (common: 700, 800, 900, 1000).
        rotation_deg: rotation of the door assembly.
        swing_direction: 'left' or 'right' (which side the hinge is on).
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        ensure_standard_linetypes(doc)
        space = doc.ModelSpace
        angle = math.radians(rotation_deg)
        sw = 1.0 if swing_direction.lower() == "right" else -1.0

        # Door opening line
        ex = x + width * math.cos(angle)
        ey = y + width * math.sin(angle)
        door_line = space.AddLine(point(x, y), point(ex, ey))
        door_line.Layer = layer
        door_line.Lineweight = 25

        # Swing arc (90 degrees)
        arc_start = math.radians(rotation_deg) if sw > 0 else math.radians(rotation_deg + 90)
        arc_end = arc_start + math.radians(90)
        arc = space.AddArc(point(x, y), float(width), arc_start, arc_end)
        arc.Layer = layer
        arc.Linetype = "DASHED"

        doc.Regen(1)
        return {
            "door_line_handle": door_line.Handle,
            "swing_arc_handle": arc.Handle,
            "width": width,
            "message": f"Door {width}mm wide added at ({x},{y}), rotation={rotation_deg}°"
        }

    @mcp.tool()
    def add_double_door(
        x: float, y: float,
        total_width: float = 1800.0,
        rotation_deg: float = 0.0,
        layer: str = "A-DOOR"
    ) -> dict:
        """
        Draw a double door symbol (two leaves with opposing swings).
        total_width: combined width of both door leaves.
        """
        leaf = total_width / 2
        angle = math.radians(rotation_deg)
        mid_x = x + leaf * math.cos(angle)
        mid_y = y + leaf * math.sin(angle)

        doc = get_active_doc()
        ensure_layer(doc, layer)
        ensure_standard_linetypes(doc)
        space = doc.ModelSpace
        handles = []

        for origin_x, origin_y, sw in [(x, y, 1), (mid_x, mid_y, -1)]:
            ex = origin_x + leaf * math.cos(angle)
            ey = origin_y + leaf * math.sin(angle)
            line = space.AddLine(point(origin_x, origin_y), point(ex, ey))
            line.Layer = layer
            line.Lineweight = 25
            handles.append(line.Handle)

            arc_start = math.radians(rotation_deg) if sw > 0 else math.radians(rotation_deg + 90)
            arc_end = arc_start + math.radians(90 * sw)
            if arc_end < arc_start:
                arc_start, arc_end = arc_end, arc_start
            arc = space.AddArc(point(origin_x, origin_y), float(leaf), arc_start, arc_end)
            arc.Layer = layer
            arc.Linetype = "DASHED"
            handles.append(arc.Handle)

        return {
            "handles": handles,
            "total_width": total_width,
            "message": f"Double door {total_width}mm wide at ({x},{y})"
        }

    @mcp.tool()
    def add_sliding_door(
        x: float, y: float,
        width: float = 1200.0,
        rotation_deg: float = 0.0,
        layer: str = "A-DOOR"
    ) -> dict:
        """
        Draw a sliding door symbol (two overlapping rectangles indicating track).
        width: total opening width.
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        space = doc.ModelSpace
        angle = math.radians(rotation_deg)
        perp_x = -math.sin(angle) * 100
        perp_y = math.cos(angle) * 100
        leaf = width / 2
        handles = []

        for offset in [0, leaf * 0.5]:
            sx = x + offset * math.cos(angle)
            sy = y + offset * math.sin(angle)
            pts = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8,
                [sx, sy,
                 sx + leaf * math.cos(angle), sy + leaf * math.sin(angle),
                 sx + leaf * math.cos(angle) + perp_x,
                 sy + leaf * math.sin(angle) + perp_y,
                 sx + perp_x, sy + perp_y,
                 sx, sy]
            )
            rect = space.AddLightWeightPolyline(pts)
            rect.Closed = True
            rect.Layer = layer
            handles.append(rect.Handle)

        return {
            "handles": handles,
            "width": width,
            "message": f"Sliding door {width}mm wide at ({x},{y})"
        }

    # -----------------------------------------------------------------------
    # WINDOWS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def add_window(
        x: float, y: float,
        width: float = 1200.0,
        wall_thickness: float = 150.0,
        rotation_deg: float = 0.0,
        layer: str = "A-GLAZ"
    ) -> dict:
        """
        Draw a window symbol in plan view (3-line symbol within wall thickness).
        width: window opening width. wall_thickness: depth of window in wall.
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        space = doc.ModelSpace
        angle = math.radians(rotation_deg)
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle)
        handles = []

        # Outer sill lines
        for offset in [0, wall_thickness]:
            sx = x + offset * perp_x
            sy = y + offset * perp_y
            ex = sx + width * math.cos(angle)
            ey = sy + width * math.sin(angle)
            line = space.AddLine(point(sx, sy), point(ex, ey))
            line.Layer = layer
            line.Lineweight = 18
            handles.append(line.Handle)

        # Glass line (middle)
        mid = wall_thickness / 2
        mx1 = x + mid * perp_x
        my1 = y + mid * perp_y
        mx2 = mx1 + width * math.cos(angle)
        my2 = my1 + width * math.sin(angle)
        glass = space.AddLine(point(mx1, my1), point(mx2, my2))
        glass.Layer = layer
        glass.Lineweight = 35
        handles.append(glass.Handle)

        return {
            "handles": handles,
            "width": width,
            "wall_thickness": wall_thickness,
            "message": f"Window {width}mm wide at ({x},{y}), rotation={rotation_deg}°"
        }

    @mcp.tool()
    def add_opening(
        x: float, y: float,
        width: float = 900.0,
        rotation_deg: float = 0.0,
        layer: str = "A-DOOR"
    ) -> dict:
        """
        Draw a simple opening (no door/window symbol) — just gap lines in a wall.
        Used for archways, pass-throughs, and open plan transitions.
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        ensure_standard_linetypes(doc)
        space = doc.ModelSpace
        angle = math.radians(rotation_deg)
        ex = x + width * math.cos(angle)
        ey = y + width * math.sin(angle)

        line = space.AddLine(point(x, y), point(ex, ey))
        line.Layer = layer
        line.Linetype = "DASHED"

        return {
            "handle": line.Handle,
            "width": width,
            "message": f"Opening {width}mm wide at ({x},{y})"
        }

    # -----------------------------------------------------------------------
    # SPACE CALCULATIONS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def calculate_room_area(
        x: float, y: float,
        width: float, depth: float
    ) -> dict:
        """
        Calculate area, perimeter, and common use metrics for a rectangular room.
        """
        area_mm2 = width * depth
        area_m2 = area_mm2 / 1e6
        perimeter_mm = 2 * (width + depth)
        perimeter_m = perimeter_mm / 1000

        return {
            "width_mm": width,
            "depth_mm": depth,
            "area_m2": round(area_m2, 3),
            "perimeter_m": round(perimeter_m, 2),
            "skirting_board_m": round(perimeter_m, 2),
            "paint_area_m2_per_2400_ceiling": round(perimeter_m * 2.4, 2),
            "note": "Paint area assumes 2400mm ceiling height, no deductions for openings"
        }

    @mcp.tool()
    def calculate_flooring(
        room_width: float, room_depth: float,
        tile_width: float = 600.0, tile_depth: float = 600.0,
        waste_pct: float = 10.0
    ) -> dict:
        """
        Calculate flooring quantities for a rectangular room.
        All dimensions in mm. waste_pct adds percentage for cuts and waste.
        Returns tile count, area, and box/pack quantities.
        """
        room_area_m2 = (room_width * room_depth) / 1e6
        tile_area_m2 = (tile_width * tile_depth) / 1e6
        net_tiles = room_area_m2 / tile_area_m2
        gross_tiles = net_tiles * (1 + waste_pct / 100)
        tiles_per_sqm = 1 / tile_area_m2

        return {
            "room_area_m2": round(room_area_m2, 3),
            "tile_size_mm": f"{tile_width}×{tile_depth}",
            "tile_area_m2": round(tile_area_m2, 4),
            "net_tiles": math.ceil(net_tiles),
            "gross_tiles_with_waste": math.ceil(gross_tiles),
            "tiles_per_sqm": round(tiles_per_sqm, 2),
            "gross_area_m2_to_order": round(room_area_m2 * (1 + waste_pct / 100), 3),
            "waste_pct": waste_pct,
        }

    @mcp.tool()
    def calculate_paint(
        room_width: float, room_depth: float,
        ceiling_height: float = 2400.0,
        num_doors: int = 1, num_windows: int = 1,
        door_width: float = 900.0, door_height: float = 2100.0,
        window_width: float = 1200.0, window_height: float = 1100.0,
        coats: int = 2
    ) -> dict:
        """
        Calculate paint quantities for a room.
        All dimensions in mm. Returns wall area, ceiling area, and litres needed.
        Assumes ~12 m² per litre per coat for standard emulsion.
        """
        wall_area = (2 * (room_width + room_depth) * ceiling_height) / 1e6
        door_area = (num_doors * door_width * door_height) / 1e6
        window_area = (num_windows * window_width * window_height) / 1e6
        net_wall_area = wall_area - door_area - window_area
        ceiling_area = (room_width * room_depth) / 1e6

        coverage = 12.0  # m² per litre
        wall_litres = (net_wall_area * coats) / coverage
        ceiling_litres = (ceiling_area * coats) / coverage

        return {
            "gross_wall_area_m2": round(wall_area, 2),
            "deductions_m2": round(door_area + window_area, 2),
            "net_wall_area_m2": round(net_wall_area, 2),
            "ceiling_area_m2": round(ceiling_area, 2),
            "coats": coats,
            "wall_paint_litres": round(wall_litres, 2),
            "ceiling_paint_litres": round(ceiling_litres, 2),
            "total_paint_litres": round(wall_litres + ceiling_litres, 2),
            "note": f"Based on {coverage} m²/litre coverage; verify with product spec"
        }

    @mcp.tool()
    def tag_room(
        x: float, y: float,
        room_name: str,
        area_m2: float,
        text_height: float = 200.0,
        layer: str = "A-ANNO-ROOM"
    ) -> dict:
        """
        Place a room tag with name and area label at a given point.
        text_height in mm (e.g. 200 = 200mm at 1:50 scale = 4mm on paper).
        """
        doc = get_active_doc()
        ensure_layer(doc, layer)
        space = doc.ModelSpace

        name_pt = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y) + text_height * 0.7, 0.0]
        )
        name_txt = space.AddText(room_name.upper(), name_pt, float(text_height))
        name_txt.Layer = layer
        name_txt.Alignment = 4  # acAlignmentMiddleCenter
        name_txt.TextAlignmentPoint = name_pt

        area_pt = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y) - text_height * 0.3, 0.0]
        )
        area_txt = space.AddText(f"{area_m2:.2f} sqm", area_pt, float(text_height) * 0.7)
        area_txt.Layer = layer
        area_txt.Alignment = 4
        area_txt.TextAlignmentPoint = area_pt

        return {
            "name_handle": name_txt.Handle,
            "area_handle": area_txt.Handle,
            "message": f"Room tag '{room_name}' ({area_m2} m²) placed at ({x},{y})"
        }
