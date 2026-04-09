"""
tools/schedules.py
Schedule and table generation tools for interior designers.
Auto-generates room schedules, door/window schedules, material
finish schedules, and FF&E (Furniture, Fixtures & Equipment) schedules.
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_active_doc, get_model_space, point


def _make_table(space, x, y, rows, cols, row_h, col_widths, layer="A-ANNO"):
    """
    Draw a table manually using lines (more reliable than AddTable in all versions).
    col_widths: list of widths for each column.
    Returns list of cell (x,y) centers for text placement.
    """
    doc = get_active_doc()
    total_w = sum(col_widths)
    total_h = rows * row_h
    handles = []
    cell_centers = []

    # Horizontal lines
    for r in range(rows + 1):
        ln = space.AddLine(
            point(x, y - r * row_h),
            point(x + total_w, y - r * row_h)
        )
        ln.Layer = layer
        ln.Lineweight = 18 if r > 0 else 35
        handles.append(ln.Handle)

    # Vertical lines
    cx = x
    for c, cw in enumerate(col_widths):
        ln = space.AddLine(point(cx, y), point(cx, y - total_h))
        ln.Layer = layer
        ln.Lineweight = 18 if c > 0 else 35
        handles.append(ln.Handle)
        cx += cw
    # Final right border
    ln = space.AddLine(point(x + total_w, y), point(x + total_w, y - total_h))
    ln.Layer = layer
    ln.Lineweight = 35
    handles.append(ln.Handle)

    # Cell centers
    cum_x = x
    for c, cw in enumerate(col_widths):
        for r in range(rows):
            cell_centers.append((cum_x + cw / 2, y - r * row_h - row_h / 2))
        cum_x += cw

    return handles, cell_centers


def _add_cell_text(space, cx, cy, text, height, layer="A-ANNO", bold_layer=None):
    pt = win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(cx), float(cy), 0.0]
    )
    txt = space.AddText(str(text), pt, float(height))
    txt.Layer = bold_layer if bold_layer else layer
    txt.Alignment = 4  # Middle center
    txt.TextAlignmentPoint = pt
    return txt.Handle


def register_schedule_tools(mcp):

    @mcp.tool()
    def create_room_schedule(
        x: float, y: float,
        rooms: list[dict],
        text_height: float = 150.0,
        layer: str = "A-ANNO"
    ) -> dict:
        """
        Generate a room schedule table at position (x,y).
        rooms: list of dicts with keys: name, number, area_m2, floor_finish, wall_finish, ceiling_finish, remarks
        Example: [{"name": "Living Room", "number": "01", "area_m2": 28.5, "floor_finish": "Engineered Oak", ...}]
        """
        doc = get_active_doc()
        space = doc.ModelSpace

        headers = ["No.", "Room Name", "Area m²", "Floor", "Walls", "Ceiling", "Remarks"]
        col_widths = [300, 1200, 500, 1000, 1000, 1000, 1200]
        row_h = text_height * 3
        rows = len(rooms) + 2  # title row + header row + data rows

        table_handles, cell_centers = _make_table(
            space, x, y, rows, len(headers), row_h, col_widths, layer
        )

        # Title row
        title_pt = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x + sum(col_widths) / 2, y - row_h / 2, 0.0]
        )
        title = space.AddText("ROOM FINISH SCHEDULE", title_pt, text_height * 1.4)
        title.Layer = layer
        title.Alignment = 4
        title.TextAlignmentPoint = title_pt
        table_handles.append(title.Handle)

        # Header row (row index 1)
        for c, header in enumerate(headers):
            cx_cell = x + sum(col_widths[:c]) + col_widths[c] / 2
            cy_cell = y - row_h - row_h / 2
            h = _add_cell_text(space, cx_cell, cy_cell, header, text_height, layer)
            table_handles.append(h)

        # Data rows
        for r, room in enumerate(rooms):
            row_y = y - (r + 2) * row_h - row_h / 2
            values = [
                room.get("number", str(r + 1)),
                room.get("name", ""),
                room.get("area_m2", ""),
                room.get("floor_finish", ""),
                room.get("wall_finish", ""),
                room.get("ceiling_finish", ""),
                room.get("remarks", ""),
            ]
            for c, val in enumerate(values):
                cx_cell = x + sum(col_widths[:c]) + col_widths[c] / 2
                h = _add_cell_text(space, cx_cell, row_y, val, text_height * 0.85, layer)
                table_handles.append(h)

        return {
            "handles": table_handles,
            "row_count": len(rooms),
            "message": f"Room schedule with {len(rooms)} rooms placed at ({x},{y})"
        }

    @mcp.tool()
    def create_door_schedule(
        x: float, y: float,
        doors: list[dict],
        text_height: float = 150.0,
        layer: str = "A-ANNO"
    ) -> dict:
        """
        Generate a door schedule table.
        doors: list of dicts with keys: mark, location, width, height, type,
               material, finish, hardware, fire_rating, remarks.
        Example: [{"mark": "D01", "location": "Entry", "width": 900, "height": 2100,
                   "type": "Single Hinged", "material": "Timber", "finish": "White Paint"}]
        """
        doc = get_active_doc()
        space = doc.ModelSpace

        headers = ["Mark", "Location", "W (mm)", "H (mm)", "Type", "Material", "Finish", "Hardware", "FR", "Remarks"]
        col_widths = [300, 900, 400, 400, 700, 700, 700, 700, 300, 900]
        row_h = text_height * 3
        rows = len(doors) + 2

        table_handles, _ = _make_table(space, x, y, rows, len(headers), row_h, col_widths, layer)

        title_pt = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x + sum(col_widths) / 2, y - row_h / 2, 0.0]
        )
        title = space.AddText("DOOR SCHEDULE", title_pt, text_height * 1.4)
        title.Layer = layer
        title.Alignment = 4
        title.TextAlignmentPoint = title_pt
        table_handles.append(title.Handle)

        for c, header in enumerate(headers):
            cx_cell = x + sum(col_widths[:c]) + col_widths[c] / 2
            cy_cell = y - row_h - row_h / 2
            h = _add_cell_text(space, cx_cell, cy_cell, header, text_height, layer)
            table_handles.append(h)

        for r, door in enumerate(doors):
            row_y = y - (r + 2) * row_h - row_h / 2
            values = [
                door.get("mark", ""),
                door.get("location", ""),
                door.get("width", ""),
                door.get("height", ""),
                door.get("type", ""),
                door.get("material", ""),
                door.get("finish", ""),
                door.get("hardware", ""),
                door.get("fire_rating", "-"),
                door.get("remarks", ""),
            ]
            for c, val in enumerate(values):
                cx_cell = x + sum(col_widths[:c]) + col_widths[c] / 2
                h = _add_cell_text(space, cx_cell, row_y, val, text_height * 0.85, layer)
                table_handles.append(h)

        return {
            "handles": table_handles,
            "row_count": len(doors),
            "message": f"Door schedule with {len(doors)} entries at ({x},{y})"
        }

    @mcp.tool()
    def create_window_schedule(
        x: float, y: float,
        windows: list[dict],
        text_height: float = 150.0,
        layer: str = "A-ANNO"
    ) -> dict:
        """
        Generate a window schedule table.
        windows: list of dicts with keys: mark, location, width, height,
                 sill_height, type, glazing, frame_material, finish, remarks.
        """
        doc = get_active_doc()
        space = doc.ModelSpace

        headers = ["Mark", "Location", "W (mm)", "H (mm)", "Sill H", "Type", "Glazing", "Frame", "Finish", "Remarks"]
        col_widths = [300, 900, 400, 400, 400, 700, 700, 700, 700, 900]
        row_h = text_height * 3
        rows = len(windows) + 2

        table_handles, _ = _make_table(space, x, y, rows, len(headers), row_h, col_widths, layer)

        title_pt = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x + sum(col_widths) / 2, y - row_h / 2, 0.0]
        )
        title = space.AddText("WINDOW SCHEDULE", title_pt, text_height * 1.4)
        title.Layer = layer
        title.Alignment = 4
        title.TextAlignmentPoint = title_pt
        table_handles.append(title.Handle)

        for c, header in enumerate(headers):
            cx_cell = x + sum(col_widths[:c]) + col_widths[c] / 2
            cy_cell = y - row_h - row_h / 2
            h = _add_cell_text(space, cx_cell, cy_cell, header, text_height, layer)
            table_handles.append(h)

        for r, win in enumerate(windows):
            row_y = y - (r + 2) * row_h - row_h / 2
            values = [
                win.get("mark", ""),
                win.get("location", ""),
                win.get("width", ""),
                win.get("height", ""),
                win.get("sill_height", ""),
                win.get("type", ""),
                win.get("glazing", ""),
                win.get("frame_material", ""),
                win.get("finish", ""),
                win.get("remarks", ""),
            ]
            for c, val in enumerate(values):
                cx_cell = x + sum(col_widths[:c]) + col_widths[c] / 2
                h = _add_cell_text(space, cx_cell, row_y, val, text_height * 0.85, layer)
                table_handles.append(h)

        return {
            "handles": table_handles,
            "row_count": len(windows),
            "message": f"Window schedule with {len(windows)} entries at ({x},{y})"
        }

    @mcp.tool()
    def create_ffe_schedule(
        x: float, y: float,
        items: list[dict],
        text_height: float = 150.0,
        layer: str = "A-ANNO"
    ) -> dict:
        """
        Generate an FF&E (Furniture, Fixtures & Equipment) schedule.
        items: list of dicts with keys: item_no, description, supplier, model,
               finish, qty, unit, unit_cost, total_cost, room, remarks.
        Example: [{"item_no": "F01", "description": "3-Seat Sofa", "supplier": "Minotti",
                   "model": "Lawrence", "finish": "Grey Boucle", "qty": 1}]
        """
        doc = get_active_doc()
        space = doc.ModelSpace

        headers = ["Item", "Description", "Supplier", "Model/Ref", "Finish", "Room", "Qty", "Remarks"]
        col_widths = [300, 1200, 900, 900, 900, 900, 300, 900]
        row_h = text_height * 3
        rows = len(items) + 2

        table_handles, _ = _make_table(space, x, y, rows, len(headers), row_h, col_widths, layer)

        title_pt = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x + sum(col_widths) / 2, y - row_h / 2, 0.0]
        )
        title = space.AddText("FF&E SCHEDULE", title_pt, text_height * 1.4)
        title.Layer = layer
        title.Alignment = 4
        title.TextAlignmentPoint = title_pt
        table_handles.append(title.Handle)

        for c, header in enumerate(headers):
            cx_cell = x + sum(col_widths[:c]) + col_widths[c] / 2
            cy_cell = y - row_h - row_h / 2
            h = _add_cell_text(space, cx_cell, cy_cell, header, text_height, layer)
            table_handles.append(h)

        for r, item in enumerate(items):
            row_y = y - (r + 2) * row_h - row_h / 2
            values = [
                item.get("item_no", ""),
                item.get("description", ""),
                item.get("supplier", ""),
                item.get("model", ""),
                item.get("finish", ""),
                item.get("room", ""),
                item.get("qty", ""),
                item.get("remarks", ""),
            ]
            for c, val in enumerate(values):
                cx_cell = x + sum(col_widths[:c]) + col_widths[c] / 2
                h = _add_cell_text(space, cx_cell, row_y, val, text_height * 0.85, layer)
                table_handles.append(h)

        return {
            "handles": table_handles,
            "row_count": len(items),
            "message": f"FF&E schedule with {len(items)} items at ({x},{y})"
        }

    @mcp.tool()
    def create_material_legend(
        x: float, y: float,
        materials: list[dict],
        swatch_size: float = 400.0,
        text_height: float = 150.0,
        layer: str = "A-ANNO-MATL"
    ) -> dict:
        """
        Draw a material legend with hatch swatches and labels.
        materials: list of dicts with keys: name, hatch_pattern, hatch_scale, description, supplier, code.
        Example: [{"name": "Herringbone Oak", "hatch_pattern": "ANSI31", "hatch_scale": 0.5,
                   "description": "Engineered Oak", "supplier": "Quick-Step", "code": "QS-001"}]
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []
        col_gap = swatch_size * 0.5
        text_col_w = swatch_size * 5

        for i, mat in enumerate(materials):
            row_y = y - i * (swatch_size + swatch_size * 0.3)

            # Swatch box
            pts = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8,
                [x, row_y, 0,
                 x + swatch_size, row_y, 0,
                 x + swatch_size, row_y - swatch_size, 0,
                 x, row_y - swatch_size, 0,
                 x, row_y, 0]
            )
            box = space.AddLightWeightPolyline(pts)
            box.Closed = True
            box.Layer = layer
            handles.append(box.Handle)

            # Hatch swatch
            pattern = mat.get("hatch_pattern", "ANSI31")
            scale = mat.get("hatch_scale", 1.0)
            try:
                hatch = space.AddHatch(0, pattern, True)
                outer = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [box]
                )
                hatch.AppendOuterLoop(outer)
                hatch.PatternScale = float(scale)
                hatch.Evaluate()
                hatch.Layer = layer
                handles.append(hatch.Handle)
            except Exception:
                pass

            # Label
            label_x = x + swatch_size + col_gap
            mat_name = mat.get("name", "")
            supplier = mat.get("supplier", "")
            code = mat.get("code", "")
            desc = mat.get("description", "")

            for j, line_text in enumerate([mat_name, f"{supplier} — {code}", desc]):
                if not line_text.strip("— "):
                    continue
                pt = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8,
                    [label_x, row_y - j * text_height * 1.5 - text_height * 0.5, 0.0]
                )
                ht = text_height * (1.1 if j == 0 else 0.8)
                txt = space.AddText(line_text, pt, float(ht))
                txt.Layer = layer
                handles.append(txt.Handle)

        doc.Regen(1)
        return {
            "handles": handles,
            "count": len(materials),
            "message": f"Material legend with {len(materials)} entries placed at ({x},{y})"
        }

    @mcp.tool()
    def create_revision_table(
        x: float, y: float,
        revisions: list[dict],
        text_height: float = 150.0,
        layer: str = "A-ANNO"
    ) -> dict:
        """
        Create a revision history table for a drawing.
        revisions: list of dicts with keys: rev, date, description, drawn_by, checked_by.
        """
        doc = get_active_doc()
        space = doc.ModelSpace

        headers = ["Rev", "Date", "Description", "Drawn", "Checked"]
        col_widths = [200, 600, 2000, 400, 400]
        row_h = text_height * 3
        rows = len(revisions) + 2

        table_handles, _ = _make_table(space, x, y, rows, len(headers), row_h, col_widths, layer)

        title_pt = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x + sum(col_widths) / 2, y - row_h / 2, 0.0]
        )
        title = space.AddText("REVISION HISTORY", title_pt, text_height * 1.3)
        title.Layer = layer
        title.Alignment = 4
        title.TextAlignmentPoint = title_pt
        table_handles.append(title.Handle)

        for c, header in enumerate(headers):
            cx_cell = x + sum(col_widths[:c]) + col_widths[c] / 2
            cy_cell = y - row_h - row_h / 2
            h = _add_cell_text(space, cx_cell, cy_cell, header, text_height, layer)
            table_handles.append(h)

        for r, rev in enumerate(revisions):
            row_y = y - (r + 2) * row_h - row_h / 2
            values = [
                rev.get("rev", ""),
                rev.get("date", ""),
                rev.get("description", ""),
                rev.get("drawn_by", ""),
                rev.get("checked_by", ""),
            ]
            for c, val in enumerate(values):
                cx_cell = x + sum(col_widths[:c]) + col_widths[c] / 2
                h = _add_cell_text(space, cx_cell, row_y, val, text_height * 0.85, layer)
                table_handles.append(h)

        return {
            "handles": table_handles,
            "message": f"Revision table with {len(revisions)} entries at ({x},{y})"
        }
