"""
tools/tile_design.py
Advanced Tile Design tools — tile drops, looping layouts, cut optimisation.

Covers:
  • Standard grid layout (centred, edge-started, custom drop point)
  • Running / offset bond (brick pattern) — horizontal and vertical
  • Herringbone (45° and 90°)
  • Chevron / arrow herringbone
  • Basket weave (2×1 and square)
  • Versailles / French pattern (multi-size)
  • Diagonal grid (45°)
  • Stack bond (pure grid variant)
  • Custom looping repeat (user-defined tile arrangement)
  • Drop point (datum) control — centre, corner, custom coordinate
  • Tile waste / cut analysis and quantity schedule
  • Grout joint visualisation
  • Feature / border strip insertion
  • Tile zone splitting (different tiles per zone)
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_model_space, point


def _var(coords):
    return win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(c) for c in coords]
    )


def _rect(space, x, y, w, h, layer, closed=True, hatch=None, hatch_scale=1.0, hatch_angle=0.0):
    """Draw a rectangle; optionally hatch it. Returns (polyline, hatch) or (polyline, None)."""
    pts = [x, y, x+w, y, x+w, y+h, x, y+h, x, y]
    pl = space.AddLightWeightPolyline(_var(pts))
    pl.Layer = layer
    if closed:
        pl.Closed = True
    h_obj = None
    if hatch:
        try:
            h_obj = space.AddHatch(0, hatch, True)
            h_obj.PatternScale = hatch_scale
            h_obj.PatternAngle = math.radians(hatch_angle)
            h_obj.Layer = layer
            loop = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [pl])
            h_obj.AppendOuterLoop(loop)
            h_obj.Evaluate()
        except Exception:
            h_obj = None
    return pl, h_obj


def _rotated_rect(space, cx, cy, w, h, angle_deg, layer):
    """Draw a rectangle centred at (cx,cy) rotated by angle_deg."""
    a = math.radians(angle_deg)
    corners = [
        (-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)
    ]
    pts = []
    for dx, dy in corners:
        rx = cx + dx * math.cos(a) - dy * math.sin(a)
        ry = cy + dx * math.sin(a) + dy * math.cos(a)
        pts.extend([rx, ry])
    pts.extend(pts[:2])
    pl = space.AddLightWeightPolyline(_var(pts))
    pl.Layer = layer; pl.Closed = True
    return pl


def _clip_to_room(x, y, w, h, rx, ry, rw, rh):
    """Return True if a tile rect has any overlap with room rect."""
    return not (x + w <= rx or x >= rx + rw or y + h <= ry or y >= ry + rh)


def register_tile_design_tools(mcp):

    # ------------------------------------------------------------------
    # UTILITY: compute drop point
    # ------------------------------------------------------------------

    def _compute_drop(room_x, room_y, room_w, room_h,
                      tile_w, tile_h, grout,
                      drop_mode, drop_x, drop_y):
        """
        Return the starting (bottom-left) coordinate for the first full tile,
        based on the chosen drop mode.

        drop_mode: 'centre'  — tile grid centred on room
                   'corner'  — grid starts at room origin
                   'custom'  — grid starts at (drop_x, drop_y)
                   'wall'    — align first full tile to the left wall,
                               equal cuts top/bottom
        """
        step_x = tile_w + grout
        step_y = tile_h + grout

        if drop_mode == "corner":
            return room_x, room_y

        elif drop_mode == "centre":
            # Centre of room, snap so centre of a tile lands at room centre
            cx = room_x + room_w / 2
            cy = room_y + room_h / 2
            # Start tile whose centre is nearest the room centre
            sx = cx - (tile_w / 2) - math.floor((cx - room_x) / step_x) * step_x + room_x % step_x
            sy = cy - (tile_h / 2) - math.floor((cy - room_y) / step_y) * step_y + room_y % step_y
            # Adjust to nearest full grid step back from room origin
            sx = room_x + ((cx - room_x - tile_w / 2) % step_x) - step_x
            sy = room_y + ((cy - room_y - tile_h / 2) % step_y) - step_y
            return sx, sy

        elif drop_mode == "wall":
            # Left wall aligned; equal cuts at top & bottom
            n_full_y = math.floor(room_h / step_y)
            leftover_y = room_h - n_full_y * step_y - grout
            start_y = room_y - leftover_y / 2
            return room_x, start_y

        else:  # custom
            return drop_x, drop_y

    # ------------------------------------------------------------------
    # 1. STANDARD GRID LAYOUT
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_tile_grid(
        room_x: float, room_y: float,
        room_w: float, room_h: float,
        tile_w: float = 600.0, tile_h: float = 600.0,
        grout: float = 3.0,
        drop_mode: str = "centre",
        drop_x: float = 0.0, drop_y: float = 0.0,
        hatch_pattern: str = "",
        hatch_alt_pattern: str = "",
        layer: str = "A-TILE"
    ) -> dict:
        """
        Lay a standard square/rectangular tile grid in a room area.

        drop_mode: 'centre' (balanced), 'corner' (starts at room corner),
                   'wall' (full tile from left wall, balanced cuts top/bottom),
                   'custom' (grid origin at drop_x, drop_y)
        hatch_pattern: optional AutoCAD hatch pattern to fill tiles (e.g. 'AR-SAND', 'ANSI37')
        hatch_alt_pattern: alternating pattern for checkerboard effect (leave empty to skip)

        Returns full tile count, cut tile count, and area coverage stats.
        """
        space = get_model_space()

        step_x = tile_w + grout
        step_y = tile_h + grout
        sx, sy = _compute_drop(room_x, room_y, room_w, room_h,
                               tile_w, tile_h, grout, drop_mode, drop_x, drop_y)

        full_tiles = 0; cut_tiles = 0; handles = []
        row = 0
        y = sy
        while y < room_y + room_h:
            col = 0
            x = sx
            while x < room_x + room_w:
                if _clip_to_room(x, y, tile_w, tile_h, room_x, room_y, room_w, room_h):
                    is_full = (x >= room_x and x + tile_w <= room_x + room_w and
                               y >= room_y and y + tile_h <= room_y + room_h)
                    if is_full:
                        full_tiles += 1
                    else:
                        cut_tiles += 1
                    pat = hatch_pattern
                    if hatch_alt_pattern and (row + col) % 2 == 1:
                        pat = hatch_alt_pattern
                    pl, _ = _rect(space, x, y, tile_w, tile_h, layer,
                                  hatch=pat if pat else None)
                    handles.append(pl.Handle)
                x += step_x
                col += 1
            y += step_y
            row += 1

        # Room boundary
        rm_pts = [room_x, room_y, room_x+room_w, room_y,
                  room_x+room_w, room_y+room_h, room_x, room_y+room_h, room_x, room_y]
        rm = space.AddLightWeightPolyline(_var(rm_pts))
        rm.Layer = layer; rm.color = 1  # red boundary

        total = full_tiles + cut_tiles
        area_sqm = round(room_w * room_h / 1_000_000, 2)
        return {
            "pattern": "grid",
            "tile_size": [tile_w, tile_h],
            "grout": grout,
            "drop_mode": drop_mode,
            "full_tiles": full_tiles,
            "cut_tiles": cut_tiles,
            "total_tiles": total,
            "tiles_with_10pct_waste": math.ceil(total * 1.1),
            "room_area_sqm": area_sqm,
            "tiles_per_sqm": round(1 / (step_x * step_y / 1_000_000), 2),
            "message": f"Grid layout: {full_tiles} full + {cut_tiles} cut = {total} tiles ({area_sqm}m²)"
        }

    # ------------------------------------------------------------------
    # 2. RUNNING / OFFSET BOND
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_tile_running_bond(
        room_x: float, room_y: float,
        room_w: float, room_h: float,
        tile_w: float = 600.0, tile_h: float = 300.0,
        grout: float = 3.0,
        offset_ratio: float = 0.5,
        direction: str = "horizontal",
        drop_mode: str = "centre",
        drop_x: float = 0.0, drop_y: float = 0.0,
        layer: str = "A-TILE"
    ) -> dict:
        """
        Lay tiles in a running / offset bond (brick pattern).

        offset_ratio: how much alternate rows are offset (default 0.5 = half-brick).
                      Common values: 0.5 (standard), 0.33 (third), 0.25 (quarter)
        direction: 'horizontal' (offset is in X per row) or
                   'vertical'   (offset is in Y per column)
        """
        space = get_model_space()

        step_x = tile_w + grout
        step_y = tile_h + grout
        offset_mm = tile_w * offset_ratio if direction == "horizontal" else tile_h * offset_ratio
        sx, sy = _compute_drop(room_x, room_y, room_w, room_h,
                               tile_w, tile_h, grout, drop_mode, drop_x, drop_y)

        full_tiles = 0; cut_tiles = 0; handles = []
        row = 0
        y = sy
        while y < room_y + room_h:
            row_offset = (row % 2) * offset_mm if direction == "horizontal" else 0
            col = 0
            x = sx - row_offset
            while x < room_x + room_w:
                if _clip_to_room(x, y, tile_w, tile_h, room_x, room_y, room_w, room_h):
                    is_full = (x >= room_x and x + tile_w <= room_x + room_w and
                               y >= room_y and y + tile_h <= room_y + room_h)
                    full_tiles += 1 if is_full else 0
                    cut_tiles += 0 if is_full else 1
                    pl, _ = _rect(space, x, y, tile_w, tile_h, layer)
                    handles.append(pl.Handle)
                x += step_x
                col += 1
            y += step_y
            row += 1

        total = full_tiles + cut_tiles
        return {
            "pattern": "running_bond",
            "offset_ratio": offset_ratio,
            "direction": direction,
            "tile_size": [tile_w, tile_h],
            "full_tiles": full_tiles,
            "cut_tiles": cut_tiles,
            "total_tiles": total,
            "tiles_with_10pct_waste": math.ceil(total * 1.1),
            "message": f"Running bond ({offset_ratio*100:.0f}% offset): {total} tiles"
        }

    # ------------------------------------------------------------------
    # 3. HERRINGBONE
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_tile_herringbone(
        room_x: float, room_y: float,
        room_w: float, room_h: float,
        tile_w: float = 600.0, tile_h: float = 300.0,
        grout: float = 3.0,
        angle: float = 45.0,
        drop_mode: str = "centre",
        drop_x: float = 0.0, drop_y: float = 0.0,
        layer: str = "A-TILE"
    ) -> dict:
        """
        Lay tiles in a herringbone pattern.

        angle: 45 for classic diagonal herringbone, 90 for straight herringbone.

        In 45° herringbone: pairs of tiles are laid diagonally at ±45°
        creating a zigzag.
        In 90° (straight) herringbone: tiles alternate horizontal/vertical.
        """
        space = get_model_space()

        # Determine drop centre
        if drop_mode == "centre":
            cx = room_x + room_w / 2
            cy = room_y + room_h / 2
        elif drop_mode == "custom":
            cx, cy = drop_x, drop_y
        else:
            cx = room_x
            cy = room_y

        tile_count = 0; handles = []

        if abs(angle - 90) < 1:
            # STRAIGHT HERRINGBONE (90°): alternate H and V tiles
            step = tile_w + grout
            n_cols = int(room_w / step) + 4
            n_rows = int(room_h / step) + 4
            sx = cx - (n_cols // 2) * step
            sy = cy - (n_rows // 2) * step

            for row in range(n_rows):
                for col in range(n_cols):
                    # Alternate horizontal / vertical per cell
                    if (row + col) % 2 == 0:
                        x = sx + col * step
                        y = sy + row * step
                        tw, th = tile_w, tile_h
                    else:
                        x = sx + col * step
                        y = sy + row * step
                        tw, th = tile_h, tile_w

                    if _clip_to_room(x, y, tw, th, room_x, room_y, room_w, room_h):
                        pl, _ = _rect(space, x, y, tw, th, layer)
                        handles.append(pl.Handle)
                        tile_count += 1

        else:
            # DIAGONAL HERRINGBONE (45°): pairs of tiles at ±45°
            # Unit cell: two tiles at right angles to each other, both rotated 45°
            unit = tile_w + grout   # unit repeat distance along diagonal
            diag = unit * math.sqrt(2)

            n = int(max(room_w, room_h) / diag) + 6
            for i in range(-n, n):
                for j in range(-n, n):
                    for (pair_dx, pair_dy, tile_angle) in [
                        (0, 0, 45),
                        (unit * math.cos(math.radians(45)),
                         unit * math.sin(math.radians(45)), -45)
                    ]:
                        tx = cx + i * tile_w * math.sqrt(2) + pair_dx
                        ty = cy + j * tile_h * math.sqrt(2) + pair_dy
                        # Bounding box check (approximate)
                        diag_half = math.hypot(tile_w, tile_h) / 2
                        if _clip_to_room(tx - diag_half, ty - diag_half,
                                         diag_half*2, diag_half*2,
                                         room_x, room_y, room_w, room_h):
                            pl = _rotated_rect(space, tx, ty, tile_w, tile_h, tile_angle, layer)
                            handles.append(pl.Handle)
                            tile_count += 1

        return {
            "pattern": "herringbone",
            "angle": angle,
            "tile_size": [tile_w, tile_h],
            "tiles_drawn": tile_count,
            "tiles_with_15pct_waste": math.ceil(tile_count * 1.15),
            "note": "Herringbone requires ~15% extra for cuts",
            "message": f"Herringbone ({angle}°): {tile_count} tiles"
        }

    # ------------------------------------------------------------------
    # 4. CHEVRON
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_tile_chevron(
        room_x: float, room_y: float,
        room_w: float, room_h: float,
        tile_w: float = 600.0, tile_h: float = 150.0,
        grout: float = 3.0,
        drop_mode: str = "centre",
        drop_x: float = 0.0, drop_y: float = 0.0,
        layer: str = "A-TILE"
    ) -> dict:
        """
        Lay tiles in a true chevron (arrowhead) pattern.
        Unlike herringbone (tiles are rectangular and butt-jointed),
        chevron uses parallelogram-shaped tiles that form a perfect V.
        Simulated here using pairs of rotated rectangles.

        tile_w: long dimension, tile_h: short dimension.
        The V-angle is determined by the tile aspect ratio.
        """
        space = get_model_space()

        if drop_mode == "centre":
            cx, cy = room_x + room_w / 2, room_y + room_h / 2
        elif drop_mode == "custom":
            cx, cy = drop_x, drop_y
        else:
            cx, cy = room_x, room_y

        chevron_angle = math.degrees(math.atan2(tile_h, tile_w))
        step_x = tile_w + grout
        step_y = (tile_h + grout) * 2  # two rows per chevron repeat

        tile_count = 0; handles = []
        n_cols = int(room_w / step_x) + 4
        n_rows = int(room_h / step_y) + 4
        sx = cx - (n_cols // 2) * step_x
        sy = cy - (n_rows // 2) * step_y

        for row in range(n_rows):
            for col in range(n_cols):
                # Left tile of chevron pair (rotated +angle)
                lx = sx + col * step_x
                ly = sy + row * step_y
                tcx = lx + tile_w / 2
                tcy = ly + tile_h / 2
                diag = math.hypot(tile_w, tile_h) / 2
                if _clip_to_room(tcx - diag, tcy - diag, diag*2, diag*2,
                                  room_x, room_y, room_w, room_h):
                    pl = _rotated_rect(space, tcx, tcy, tile_w, tile_h, chevron_angle, layer)
                    handles.append(pl.Handle)
                    tile_count += 1

                # Right tile (mirrored, rotated -angle)
                rx2 = lx + tile_w
                ry2 = ly
                tcx2 = rx2 + tile_w / 2
                tcy2 = ry2 + tile_h / 2
                if _clip_to_room(tcx2 - diag, tcy2 - diag, diag*2, diag*2,
                                  room_x, room_y, room_w, room_h):
                    pl2 = _rotated_rect(space, tcx2, tcy2, tile_w, tile_h, -chevron_angle, layer)
                    handles.append(pl2.Handle)
                    tile_count += 1

        return {
            "pattern": "chevron",
            "tile_size": [tile_w, tile_h],
            "chevron_angle_deg": round(chevron_angle, 1),
            "tiles_drawn": tile_count,
            "tiles_with_15pct_waste": math.ceil(tile_count * 1.15),
            "message": f"Chevron pattern: {tile_count} tiles at ±{round(chevron_angle,1)}°"
        }

    # ------------------------------------------------------------------
    # 5. BASKET WEAVE
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_tile_basket_weave(
        room_x: float, room_y: float,
        room_w: float, room_h: float,
        tile_w: float = 300.0, tile_h: float = 150.0,
        tiles_per_group: int = 2,
        grout: float = 3.0,
        drop_mode: str = "centre",
        drop_x: float = 0.0, drop_y: float = 0.0,
        layer: str = "A-TILE"
    ) -> dict:
        """
        Lay tiles in a basket weave pattern.
        tiles_per_group: number of tiles per group (typically 2).
        Groups alternate 90° — like a woven basket.

        For a 2×1 tile: groups of 2 tiles horizontal alternating with 2 tiles vertical.
        For square tiles (tile_w == tile_h): classic pinwheel basket weave.
        """
        space = get_model_space()

        g = tiles_per_group
        # Cell size = g tiles wide × 1 tile tall (in one orientation)
        cell_w = tile_w * g + grout * (g - 1) + grout
        cell_h = tile_h * g + grout * (g - 1) + grout

        if drop_mode == "centre":
            sx = room_x + (room_w % cell_w) / 2 - cell_w
            sy = room_y + (room_h % cell_h) / 2 - cell_h
        elif drop_mode == "custom":
            sx, sy = drop_x, drop_y
        else:
            sx, sy = room_x, room_y

        tile_count = 0; handles = []
        row = 0
        y = sy
        while y < room_y + room_h:
            col = 0
            x = sx
            while x < room_x + room_w:
                # Alternating orientation per cell
                horiz = (row + col) % 2 == 0
                if horiz:
                    # g tiles laid horizontally
                    for i in range(g):
                        tx = x + i * (tile_w + grout)
                        ty = y
                        if _clip_to_room(tx, ty, tile_w, tile_h, room_x, room_y, room_w, room_h):
                            pl, _ = _rect(space, tx, ty, tile_w, tile_h, layer)
                            handles.append(pl.Handle); tile_count += 1
                else:
                    # g tiles laid vertically (swap w & h)
                    for i in range(g):
                        tx = x
                        ty = y + i * (tile_h + grout)
                        if _clip_to_room(tx, ty, tile_h, tile_w, room_x, room_y, room_w, room_h):
                            pl, _ = _rect(space, tx, ty, tile_h, tile_w, layer)
                            handles.append(pl.Handle); tile_count += 1
                x += cell_w
                col += 1
            y += cell_h
            row += 1

        return {
            "pattern": "basket_weave",
            "tile_size": [tile_w, tile_h],
            "tiles_per_group": tiles_per_group,
            "cell_size": [cell_w, cell_h],
            "tiles_drawn": tile_count,
            "tiles_with_10pct_waste": math.ceil(tile_count * 1.1),
            "message": f"Basket weave: {tile_count} tiles"
        }

    # ------------------------------------------------------------------
    # 6. VERSAILLES / FRENCH PATTERN
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_tile_versailles(
        room_x: float, room_y: float,
        room_w: float, room_h: float,
        module: float = 300.0,
        grout: float = 3.0,
        drop_mode: str = "centre",
        drop_x: float = 0.0, drop_y: float = 0.0,
        layer: str = "A-TILE"
    ) -> dict:
        """
        Lay a Versailles / French / Roman pattern:
        A repeating 4-tile module consisting of one large square, two medium rectangles,
        and one small square — the classic Opus Romanum stone-laying pattern.

        module: base dimension (mm). The repeat cell is 2×2 modules.
        Tile sizes within the cell:
          • 1 large square:   1.5m × 1.5m  → module * 1.5
          • 2 rectangles:     1.5m × 1.0m  → module * 1.5 × module * 1.0
          • 1 small square:   1.0m × 1.0m  → module * 1.0
        """
        space = get_model_space()

        M = module
        G = grout
        # Cell total size = 2.5M + 2G (approximately)
        cell_w = 2.5 * M + 2 * G
        cell_h = 2.5 * M + 2 * G

        if drop_mode == "centre":
            sx = room_x + (room_w % cell_w) / 2 - cell_w
            sy = room_y + (room_h % cell_h) / 2 - cell_h
        elif drop_mode == "custom":
            sx, sy = drop_x, drop_y
        else:
            sx, sy = room_x, room_y

        # Tile positions within one cell (relative to cell origin)
        # Large square: top-left
        # Two rectangles: top-right (horizontal), bottom-left (vertical)
        # Small square: bottom-right
        cell_tiles = [
            (0,           M + G,       1.5*M, 1.5*M),   # large square top-left
            (1.5*M + G,   M + G,       M,     1.5*M),   # rect top-right (vertical)
            (0,           0,           1.5*M, M),        # rect bottom-left (horizontal)
            (1.5*M + G,   0,           M,     M),        # small square bottom-right
        ]

        tile_count = 0; handles = []
        y = sy
        while y < room_y + room_h:
            x = sx
            while x < room_x + room_w:
                for (dx, dy, tw, th) in cell_tiles:
                    tx, ty = x + dx, y + dy
                    if _clip_to_room(tx, ty, tw, th, room_x, room_y, room_w, room_h):
                        pl, _ = _rect(space, tx, ty, tw, th, layer)
                        handles.append(pl.Handle)
                        tile_count += 1
                x += cell_w
            y += cell_h

        return {
            "pattern": "versailles",
            "module": module,
            "cell_size": [round(cell_w, 1), round(cell_h, 1)],
            "tiles_per_cell": 4,
            "total_tiles_drawn": tile_count,
            "tiles_with_10pct_waste": math.ceil(tile_count * 1.1),
            "message": f"Versailles pattern (module={module}mm): {tile_count} tiles"
        }

    # ------------------------------------------------------------------
    # 7. DIAGONAL GRID
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_tile_diagonal(
        room_x: float, room_y: float,
        room_w: float, room_h: float,
        tile_size: float = 400.0,
        grout: float = 3.0,
        drop_mode: str = "centre",
        drop_x: float = 0.0, drop_y: float = 0.0,
        layer: str = "A-TILE"
    ) -> dict:
        """
        Lay square tiles on the diagonal (45°).
        All tiles are square, rotated 45°. The tile_size is the side length.
        """
        space = get_model_space()

        if drop_mode == "centre":
            cx, cy = room_x + room_w / 2, room_y + room_h / 2
        elif drop_mode == "custom":
            cx, cy = drop_x, drop_y
        else:
            cx, cy = room_x, room_y

        diag_step = tile_size + grout

        tile_count = 0; handles = []
        diag_r = math.hypot(tile_size, tile_size) / 2

        n = int(max(room_w, room_h) / diag_step) + 4
        for i in range(-n, n):
            for j in range(-n, n):
                tx = cx + (i + j) * diag_step / math.sqrt(2)
                ty = cy + (j - i) * diag_step / math.sqrt(2)
                if _clip_to_room(tx - diag_r, ty - diag_r, diag_r*2, diag_r*2,
                                  room_x, room_y, room_w, room_h):
                    pl = _rotated_rect(space, tx, ty, tile_size, tile_size, 45, layer)
                    handles.append(pl.Handle)
                    tile_count += 1

        return {
            "pattern": "diagonal_45",
            "tile_size": tile_size,
            "tiles_drawn": tile_count,
            "tiles_with_15pct_waste": math.ceil(tile_count * 1.15),
            "note": "Diagonal layout requires ~15% extra waste for border cuts",
            "message": f"Diagonal 45° grid: {tile_count} tiles"
        }

    # ------------------------------------------------------------------
    # 8. CUSTOM LOOPING REPEAT
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_tile_custom_repeat(
        room_x: float, room_y: float,
        room_w: float, room_h: float,
        cell_w: float,
        cell_h: float,
        tile_definitions: list,
        grout: float = 3.0,
        drop_mode: str = "corner",
        drop_x: float = 0.0, drop_y: float = 0.0,
        layer: str = "A-TILE"
    ) -> dict:
        """
        Lay tiles using a completely custom repeating cell pattern.
        The cell is tiled (looped) across the entire room.

        cell_w, cell_h: the total size of one repeating unit (in mm).
        tile_definitions: list of dicts, each defining one tile within the cell:
          {"x": offset_x, "y": offset_y, "w": width, "h": height, "hatch": "ANSI31"}
          x, y are relative to the cell origin (bottom-left of cell = 0, 0).
          hatch is optional.

        Example cell for a pinwheel pattern (module=100):
          cell_w=210, cell_h=210,
          tile_definitions=[
            {"x":0, "y":0, "w":100, "h":100},          # centre square
            {"x":110, "y":0, "w":100, "h":100},         # right
            {"x":0, "y":110, "w":100, "h":100},         # top
            {"x":110, "y":110, "w":100, "h":100},       # top-right
            {"x":50, "y":50, "w":100, "h":100},         # diagonal offset
          ]
        """
        space = get_model_space()

        if drop_mode == "centre":
            sx = room_x + (room_w % cell_w) / 2 - cell_w
            sy = room_y + (room_h % cell_h) / 2 - cell_h
        elif drop_mode == "custom":
            sx, sy = drop_x, drop_y
        else:
            sx, sy = room_x, room_y

        tile_count = 0; handles = []
        y = sy
        while y < room_y + room_h + cell_h:
            x = sx
            while x < room_x + room_w + cell_w:
                for td in tile_definitions:
                    tx = x + td.get("x", 0)
                    ty = y + td.get("y", 0)
                    tw = td.get("w", 100)
                    th = td.get("h", 100)
                    hatch = td.get("hatch", "")
                    if _clip_to_room(tx, ty, tw, th, room_x, room_y, room_w, room_h):
                        pl, _ = _rect(space, tx, ty, tw, th, layer,
                                      hatch=hatch if hatch else None)
                        handles.append(pl.Handle)
                        tile_count += 1
                x += cell_w
            y += cell_h

        return {
            "pattern": "custom_repeat",
            "cell_size": [cell_w, cell_h],
            "tiles_per_cell": len(tile_definitions),
            "total_tiles_drawn": tile_count,
            "tiles_with_10pct_waste": math.ceil(tile_count * 1.1),
            "message": f"Custom repeat pattern: {len(tile_definitions)} tiles/cell × {tile_count//len(tile_definitions) if tile_definitions else 0} cells = {tile_count} tiles"
        }

    # ------------------------------------------------------------------
    # 9. BORDER / FEATURE STRIP
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_tile_border_strip(
        room_x: float, room_y: float,
        room_w: float, room_h: float,
        border_width: float = 200.0,
        border_tile_w: float = 200.0,
        border_tile_h: float = 50.0,
        grout: float = 3.0,
        position: str = "all",
        layer: str = "A-TILE-BORDER"
    ) -> dict:
        """
        Draw a border / feature strip around the perimeter of the tiled area.
        position: 'all' (all 4 sides), 'bottom', 'top', 'left', 'right', 'perimeter'
        The border strip is inset from the room edge by border_width.
        Remaining interior is left clear for the main tile fill.
        """
        space = get_model_space()
        handles = []
        tile_count = 0
        G = grout

        def _strip_horizontal(sx, sy, length, tw, th):
            nonlocal tile_count
            x = sx
            while x < sx + length:
                if _clip_to_room(x, sy, tw, th, room_x, room_y, room_w, room_h):
                    pl, _ = _rect(space, x, sy, tw, th, layer)
                    handles.append(pl.Handle)
                    tile_count += 1
                x += tw + G

        def _strip_vertical(sx, sy, length, tw, th):
            nonlocal tile_count
            y = sy
            while y < sy + length:
                if _clip_to_room(sx, y, th, tw, room_x, room_y, room_w, room_h):
                    pl, _ = _rect(space, sx, y, th, tw, layer)
                    handles.append(pl.Handle)
                    tile_count += 1
                y += tw + G

        bw = border_width
        if position in ("all", "perimeter", "bottom"):
            _strip_horizontal(room_x + bw, room_y, room_w - 2*bw, border_tile_w, border_tile_h)
        if position in ("all", "perimeter", "top"):
            _strip_horizontal(room_x + bw, room_y + room_h - bw, room_w - 2*bw, border_tile_w, border_tile_h)
        if position in ("all", "perimeter", "left"):
            _strip_vertical(room_x, room_y, room_h, border_tile_w, border_tile_h)
        if position in ("all", "perimeter", "right"):
            _strip_vertical(room_x + room_w - bw, room_y, room_h, border_tile_w, border_tile_h)

        return {
            "border_position": position,
            "border_width": border_width,
            "border_tile_size": [border_tile_w, border_tile_h],
            "tiles_drawn": tile_count,
            "message": f"Border strip ({position}): {tile_count} tiles"
        }

    # ------------------------------------------------------------------
    # 10. TILE WASTE ANALYSIS
    # ------------------------------------------------------------------

    @mcp.tool()
    def calculate_tile_waste(
        room_w: float, room_h: float,
        tile_w: float, tile_h: float,
        pattern: str = "grid",
        grout: float = 3.0,
        wastage_percent: float = 10.0,
        price_per_sqm: float = 0.0
    ) -> dict:
        """
        Calculate tile quantities, waste, and optional cost for a room.

        pattern: affects waste factor —
          'grid' or 'running_bond' → 10% waste
          'diagonal' or 'herringbone' → 15% waste
          'versailles' or 'chevron' → 12% waste

        Returns: net tiles needed, tiles with wastage, boxes required,
                 total area covered, and cost estimate.
        """
        waste_factors = {
            "grid":          0.10,
            "running_bond":  0.10,
            "stack":         0.08,
            "diagonal":      0.15,
            "herringbone":   0.15,
            "chevron":       0.15,
            "basket_weave":  0.10,
            "versailles":    0.12,
        }
        waste_factor = waste_factors.get(pattern, wastage_percent / 100)

        room_area = room_w * room_h / 1_000_000  # m²
        tile_area = tile_w * tile_h / 1_000_000  # m²
        step_x = tile_w + grout
        step_y = tile_h + grout
        tiles_per_sqm = 1_000_000 / (step_x * step_y)

        net_tiles = room_area * tiles_per_sqm
        tiles_with_waste = math.ceil(net_tiles * (1 + waste_factor))

        # Typical box quantities
        tile_area_sqm_each = tile_w * tile_h / 1_000_000
        tiles_per_box = max(1, round(1.5 / tile_area_sqm_each))  # ~1.5m² per box typical
        boxes = math.ceil(tiles_with_waste / tiles_per_box)

        cost = 0.0
        if price_per_sqm > 0:
            coverage_with_waste = tiles_with_waste * tile_area_sqm_each
            cost = round(coverage_with_waste * price_per_sqm, 2)

        return {
            "room_area_sqm": round(room_area, 2),
            "tile_size_mm": [tile_w, tile_h],
            "tile_area_sqm": round(tile_area, 4),
            "tiles_per_sqm": round(tiles_per_sqm, 2),
            "net_tiles_needed": math.ceil(net_tiles),
            "waste_factor_pct": round(waste_factor * 100, 1),
            "tiles_with_waste": tiles_with_waste,
            "tiles_per_box_estimate": tiles_per_box,
            "boxes_required": boxes,
            "cost_estimate": cost,
            "currency_note": "cost = tiles_with_waste × tile_area × price_per_sqm",
            "message": (
                f"{pattern} layout: {tiles_with_waste} tiles needed "
                f"({math.ceil(net_tiles)} net + {round(waste_factor*100,1)}% waste)"
                + (f" — Est. cost: {cost}" if cost else "")
            )
        }

    # ------------------------------------------------------------------
    # 11. TILE ZONE SPLITTER
    # ------------------------------------------------------------------

    @mcp.tool()
    def draw_tile_zones(
        room_x: float, room_y: float,
        room_w: float, room_h: float,
        zones: list,
        layer_prefix: str = "A-TILE"
    ) -> dict:
        """
        Divide a room into multiple tile zones, each with its own tile size and pattern.

        zones: list of dicts, each with:
          {
            "name": "Zone A",
            "x": relative x from room_x, "y": relative y from room_y,
            "w": zone width, "h": zone height,
            "tile_w": tile width, "tile_h": tile height,
            "pattern": "grid" | "running_bond" | "diagonal",
            "grout": 3.0,
            "drop_mode": "centre"
          }
        Each zone gets its own layer: {layer_prefix}-{zone_name}
        """
        space = get_model_space()
        results = []

        for zone in zones:
            name = zone.get("name", "Zone")
            zx = room_x + zone.get("x", 0)
            zy = room_y + zone.get("y", 0)
            zw = zone.get("w", room_w)
            zh = zone.get("h", room_h)
            tw = zone.get("tile_w", 600)
            th = zone.get("tile_h", 600)
            pat = zone.get("pattern", "grid")
            g = zone.get("grout", 3.0)
            dm = zone.get("drop_mode", "centre")
            z_layer = f"{layer_prefix}-{name.upper().replace(' ', '-')}"

            # Zone boundary
            z_pts = [zx, zy, zx+zw, zy, zx+zw, zy+zh, zx, zy+zh, zx, zy]
            z_bound = space.AddLightWeightPolyline(_var(z_pts))
            z_bound.Layer = z_layer; z_bound.color = 2  # yellow boundary

            # Zone label
            zt = space.AddText(name, point(zx + 50, zy + 50), 60)
            zt.Layer = z_layer

            # Draw tile pattern for this zone
            step_x = tw + g; step_y = th + g
            cx = zx + (zw % step_x) / 2 - step_x
            cy = zy + (zh % step_y) / 2 - step_y
            if dm == "centre":
                sx, sy = cx, cy
            else:
                sx, sy = zx, zy

            tile_count = 0
            y = sy
            while y < zy + zh:
                x = sx
                while x < zx + zw:
                    if _clip_to_room(x, y, tw, th, zx, zy, zw, zh):
                        pl, _ = _rect(space, x, y, tw, th, z_layer)
                        tile_count += 1
                    x += step_x
                y += step_y

            results.append({
                "zone": name,
                "size": [zw, zh],
                "tile_size": [tw, th],
                "pattern": pat,
                "tile_count": tile_count,
                "layer": z_layer,
            })

        return {
            "zones_drawn": len(zones),
            "zone_results": results,
            "message": f"{len(zones)} tile zones drawn"
        }
