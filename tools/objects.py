"""
tools/objects.py
Tools for selecting, manipulating, and modifying existing AutoCAD objects.

All mutation helpers are exposed as module-level _do_* functions so that
batch_execute can dispatch any operation with a single dict — no per-tool
tool-call quota required.
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_active_doc, get_model_space, ensure_layer, point, color_index


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_variant(values):
    return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in values])


def _region_objects(space, x1, y1, x2, y2, layer_filter=None):
    """Return COM objects whose bounding boxes overlap the given region."""
    result = []
    lf = [l.upper() for l in layer_filter] if layer_filter else None
    for i in range(space.Count):
        obj = space.Item(i)
        try:
            mn, mx = obj.GetBoundingBox()
            if mx[0] >= x1 and mn[0] <= x2 and mx[1] >= y1 and mn[1] <= y2:
                if lf and obj.Layer.upper() not in lf:
                    continue
                result.append(obj)
        except Exception:
            pass
    return result


# ---------------------------------------------------------------------------
# Core _do_* functions — batchable, self-contained
# ---------------------------------------------------------------------------

def _do_move(handle: str, dx: float, dy: float, dz: float = 0.0) -> dict:
    doc = get_active_doc()
    doc.HandleToObject(handle).Move(
        _make_variant([0, 0, 0]),
        _make_variant([dx, dy, dz]),
    )
    return {"status": "ok", "message": f"Entity {handle} moved by ({dx},{dy},{dz})"}


def _do_copy(handle: str, dx: float, dy: float, dz: float = 0.0) -> dict:
    doc = get_active_doc()
    obj = doc.HandleToObject(handle)
    cp = obj.Copy()
    cp.Move(_make_variant([0, 0, 0]), _make_variant([dx, dy, dz]))
    return {"status": "ok", "new_handle": cp.Handle,
            "message": f"Entity {handle} copied → {cp.Handle}"}


def _do_mirror(
    handle: str,
    x1: float, y1: float,
    x2: float, y2: float,
    delete_original: bool = False,
) -> dict:
    doc = get_active_doc()
    obj = doc.HandleToObject(handle)
    mirrored = obj.Mirror(point(x1, y1), point(x2, y2))
    if delete_original:
        obj.Delete()
    return {"status": "ok", "new_handle": mirrored.Handle,
            "message": f"Entity {handle} mirrored → {mirrored.Handle}"}


def _do_rotate(
    handle: str,
    pivot_x: float, pivot_y: float,
    angle_deg: float,
) -> dict:
    doc = get_active_doc()
    doc.HandleToObject(handle).Rotate(point(pivot_x, pivot_y), math.radians(angle_deg))
    return {"status": "ok", "message": f"Entity {handle} rotated {angle_deg}°"}


def _do_scale(
    handle: str,
    base_x: float, base_y: float,
    factor: float,
) -> dict:
    doc = get_active_doc()
    doc.HandleToObject(handle).ScaleEntity(point(base_x, base_y), float(factor))
    return {"status": "ok", "message": f"Entity {handle} scaled by {factor}"}


def _do_delete(handle: str) -> dict:
    doc = get_active_doc()
    doc.HandleToObject(handle).Delete()
    return {"status": "ok", "message": f"Entity {handle} deleted"}


def _do_set_layer(handle: str, layer: str) -> dict:
    doc = get_active_doc()
    ensure_layer(doc, layer)
    doc.HandleToObject(handle).Layer = layer
    return {"status": "ok", "message": f"Entity {handle} → layer '{layer}'"}


def _do_set_color(handle: str, color) -> dict:
    doc = get_active_doc()
    obj = doc.HandleToObject(handle)
    try:
        obj.color = int(color)
    except (ValueError, TypeError):
        obj.color = color_index(str(color))
    return {"status": "ok", "message": f"Entity {handle} color → {color}"}


def _do_set_linetype(handle: str, linetype: str) -> dict:
    doc = get_active_doc()
    doc.HandleToObject(handle).Linetype = linetype
    return {"status": "ok", "message": f"Entity {handle} linetype → '{linetype}'"}


def _do_set_lineweight(handle: str, lineweight: int) -> dict:
    doc = get_active_doc()
    doc.HandleToObject(handle).Lineweight = int(lineweight)
    return {"status": "ok", "message": f"Entity {handle} lineweight → {lineweight}"}


def _do_offset_entity(handle: str, distance: float) -> dict:
    doc = get_active_doc()
    result = doc.HandleToObject(handle).Offset(float(distance))
    new_handles = [r.Handle for r in result]
    return {"status": "ok", "new_handles": new_handles,
            "message": f"Entity {handle} offset by {distance} → {new_handles}"}


def _do_explode_entity(handle: str) -> dict:
    doc = get_active_doc()
    obj = doc.HandleToObject(handle)
    result = obj.Explode()
    handles = [r.Handle for r in result]
    obj.Delete()
    return {"status": "ok", "new_handles": handles,
            "message": f"Entity {handle} exploded into {len(handles)} objects"}


# ---------------------------------------------------------------------------
# Lazy _OP_MAP — populated on first call to avoid circular imports
# ---------------------------------------------------------------------------

_OP_MAP: dict | None = None


def _build_op_map() -> dict:
    from tools.drawing import (
        _do_draw_line, _do_draw_circle, _do_draw_arc, _do_draw_rectangle,
        _do_draw_polyline, _do_draw_text, _do_draw_mtext,
        _do_draw_ellipse, _do_draw_spline, _do_draw_hatch,
    )
    from tools.arrays import (
        _do_rectangular_array, _do_polar_array, _do_grid_array,
    )
    from tools.query import (
        _do_insert_block, _do_add_linear_dimension, _do_add_radius_dimension,
    )
    from tools.blocks_xrefs_styles import (
        _do_set_block_attribute_value,
        _do_add_angular_dimension, _do_add_diameter_dimension,
        _do_add_ordinate_dimension, _do_add_leader,
        _do_create_table, _do_set_table_cell,
        _do_set_table_column_width, _do_set_table_row_height,
    )

    return {
        # ── object manipulation ──────────────────────────────────────────
        "move":             lambda d: _do_move(d["handle"], d["dx"], d["dy"], d.get("dz", 0.0)),
        "copy":             lambda d: _do_copy(d["handle"], d["dx"], d["dy"], d.get("dz", 0.0)),
        "mirror":           lambda d: _do_mirror(d["handle"], d["x1"], d["y1"], d["x2"], d["y2"],
                                                 d.get("delete_original", False)),
        "rotate":           lambda d: _do_rotate(d["handle"], d["pivot_x"], d["pivot_y"],
                                                 d["angle_deg"]),
        "scale":            lambda d: _do_scale(d["handle"], d["base_x"], d["base_y"],
                                                d["factor"]),
        "delete":           lambda d: _do_delete(d["handle"]),
        "set_layer":        lambda d: _do_set_layer(d["handle"], d["layer"]),
        "set_color":        lambda d: _do_set_color(d["handle"], d["color"]),
        "set_linetype":     lambda d: _do_set_linetype(d["handle"], d["linetype"]),
        "set_lineweight":   lambda d: _do_set_lineweight(d["handle"], d["lineweight"]),
        "offset":           lambda d: _do_offset_entity(d["handle"], d["distance"]),
        "explode":          lambda d: _do_explode_entity(d["handle"]),

        # ── drawing ─────────────────────────────────────────────────────
        "draw_line":        lambda d: _do_draw_line(d["x1"], d["y1"], d["x2"], d["y2"],
                                                    d.get("layer", "")),
        "draw_circle":      lambda d: _do_draw_circle(d["cx"], d["cy"], d["radius"],
                                                      d.get("layer", "")),
        "draw_arc":         lambda d: _do_draw_arc(d["cx"], d["cy"], d["radius"],
                                                   d["start_angle_deg"], d["end_angle_deg"],
                                                   d.get("layer", "")),
        "draw_rectangle":   lambda d: _do_draw_rectangle(d["x1"], d["y1"], d["x2"], d["y2"],
                                                         d.get("layer", "")),
        "draw_polyline":    lambda d: _do_draw_polyline(d["points_flat"],
                                                        d.get("closed", False),
                                                        d.get("layer", "")),
        "draw_text":        lambda d: _do_draw_text(d["x"], d["y"], d["text"],
                                                    d.get("height", 2.5),
                                                    d.get("rotation_deg", 0.0),
                                                    d.get("layer", "")),
        "draw_mtext":       lambda d: _do_draw_mtext(d["x"], d["y"], d["text"],
                                                     d.get("width", 100.0),
                                                     d.get("height", 2.5),
                                                     d.get("layer", "")),
        "draw_ellipse":     lambda d: _do_draw_ellipse(d["cx"], d["cy"],
                                                       d["major_x"], d["major_y"],
                                                       d["ratio"], d.get("layer", "")),
        "draw_spline":      lambda d: _do_draw_spline(d["points_flat"], d.get("layer", "")),
        "draw_hatch":       lambda d: _do_draw_hatch(d["boundary_x1"], d["boundary_y1"],
                                                     d["boundary_x2"], d["boundary_y2"],
                                                     d.get("pattern", "ANSI31"),
                                                     d.get("scale", 1.0),
                                                     d.get("layer", "")),

        # ── blocks & dimensions ──────────────────────────────────────────
        "insert_block":     lambda d: _do_insert_block(d["name"], d["x"], d["y"],
                                                       d.get("z", 0.0),
                                                       d.get("x_scale", 1.0),
                                                       d.get("y_scale", 1.0),
                                                       d.get("z_scale", 1.0),
                                                       d.get("rotation_deg", 0.0),
                                                       d.get("layer", "")),
        "set_attr":         lambda d: _do_set_block_attribute_value(d["handle"], d["tag"],
                                                                    d["value"]),
        "dim_linear":       lambda d: _do_add_linear_dimension(d["x1"], d["y1"],
                                                               d["x2"], d["y2"],
                                                               d["text_x"], d["text_y"],
                                                               d.get("layer", "")),
        "dim_radius":       lambda d: _do_add_radius_dimension(d["handle"],
                                                               d["leader_x"], d["leader_y"],
                                                               d.get("layer", "")),
        "dim_angular":      lambda d: _do_add_angular_dimension(d["arc_x"], d["arc_y"],
                                                                d["x1"], d["y1"],
                                                                d["x2"], d["y2"],
                                                                d["text_x"], d["text_y"],
                                                                d.get("layer", "")),
        "dim_diameter":     lambda d: _do_add_diameter_dimension(d["handle"],
                                                                 d["leader_x"], d["leader_y"],
                                                                 d.get("layer", "")),
        "dim_ordinate":     lambda d: _do_add_ordinate_dimension(d["feature_x"], d["feature_y"],
                                                                 d["leader_x"], d["leader_y"],
                                                                 d.get("use_x_axis", False),
                                                                 d.get("layer", "")),
        "add_leader":       lambda d: _do_add_leader(d["points_flat"], d["annotation"],
                                                     d.get("layer", "")),

        # ── tables ───────────────────────────────────────────────────────
        "create_table":     lambda d: _do_create_table(d["x"], d["y"],
                                                       d["num_rows"], d["num_cols"],
                                                       d.get("row_height", 8.0),
                                                       d.get("col_width", 40.0),
                                                       d.get("title", ""),
                                                       d.get("layer", "")),
        "set_table_cell":   lambda d: _do_set_table_cell(d["handle"], d["row"], d["col"],
                                                         d["value"]),
        "set_col_width":    lambda d: _do_set_table_column_width(d["handle"], d["col"],
                                                                 d["width"]),
        "set_row_height":   lambda d: _do_set_table_row_height(d["handle"], d["row"],
                                                               d["height"]),

        # ── arrays ───────────────────────────────────────────────────────
        "rect_array":       lambda d: _do_rectangular_array(d["handle"],
                                                            d["num_rows"], d["num_cols"],
                                                            d["row_spacing"], d["col_spacing"],
                                                            d.get("rotation_deg", 0.0)),
        "polar_array":      lambda d: _do_polar_array(d["handle"],
                                                      d["center_x"], d["center_y"],
                                                      d["num_items"],
                                                      d.get("total_angle_deg", 360.0),
                                                      d.get("rotate_items", True)),
        "grid_array":       lambda d: _do_grid_array(d["handle"],
                                                     d["num_rows"], d["num_cols"],
                                                     d["row_spacing"], d["col_spacing"],
                                                     d.get("x_offset_per_row", 0.0)),
    }


def _exec_op(op_dict: dict) -> dict:
    """Dispatch a single batch operation dict. Raises ValueError for unknown ops."""
    global _OP_MAP
    if _OP_MAP is None:
        _OP_MAP = _build_op_map()
    op = str(op_dict.get("op", "")).lower()
    if op not in _OP_MAP:
        raise ValueError(f"Unknown operation: '{op_dict.get('op')}'")
    return _OP_MAP[op](op_dict)


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------

def register_object_tools(mcp):

    @mcp.tool()
    def list_entities(layer: str = "", entity_type: str = "") -> list[dict]:
        """
        List all entities in model space. Optionally filter by layer name
        and/or entity type (e.g. 'AcDbLine', 'AcDbCircle', 'AcDbText').
        """
        space = get_model_space()
        result = []
        for i in range(space.Count):
            obj = space.Item(i)
            if layer and obj.Layer != layer:
                continue
            if entity_type and obj.ObjectName != entity_type:
                continue
            entry = {
                "handle": obj.Handle,
                "type": obj.ObjectName,
                "layer": obj.Layer,
            }
            try:
                entry["color"] = obj.color
            except Exception:
                pass
            result.append(entry)
        return result

    @mcp.tool()
    def get_entity_by_handle(handle: str) -> dict:
        """Get detailed properties of an entity by its handle string."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        info = {
            "handle": obj.Handle,
            "type": obj.ObjectName,
            "layer": obj.Layer,
            "color": obj.color,
            "linetype": obj.Linetype,
            "lineweight": obj.Lineweight,
            "visible": obj.Visible,
        }
        try:
            info["start_point"] = list(obj.StartPoint)
            info["end_point"] = list(obj.EndPoint)
        except Exception:
            pass
        try:
            info["center"] = list(obj.Center)
            info["radius"] = obj.Radius
        except Exception:
            pass
        try:
            info["text_string"] = obj.TextString
        except Exception:
            pass
        try:
            if obj.ObjectName == "AcDbLwPolyline":
                coords = list(obj.Coordinates)
                n = obj.NumberOfVertices
                info["vertices"] = [
                    [round(coords[i * 2], 3), round(coords[i * 2 + 1], 3)]
                    for i in range(n)
                ]
                info["closed"] = obj.Closed
                info["vertex_count"] = n
        except Exception:
            pass
        return info

    @mcp.tool()
    def move_entity(handle: str, dx: float, dy: float, dz: float = 0.0) -> dict:
        """Move an entity by a displacement vector (dx, dy, dz)."""
        return _do_move(handle, dx, dy, dz)

    @mcp.tool()
    def copy_entity(handle: str, dx: float, dy: float, dz: float = 0.0) -> dict:
        """Copy an entity and place the copy offset by (dx, dy, dz)."""
        return _do_copy(handle, dx, dy, dz)

    @mcp.tool()
    def rotate_entity(
        handle: str,
        pivot_x: float, pivot_y: float,
        angle_deg: float
    ) -> dict:
        """Rotate an entity around a pivot point by angle_deg degrees."""
        return _do_rotate(handle, pivot_x, pivot_y, angle_deg)

    @mcp.tool()
    def scale_entity(
        handle: str,
        base_x: float, base_y: float,
        scale_factor: float
    ) -> dict:
        """Scale an entity uniformly from a base point."""
        return _do_scale(handle, base_x, base_y, scale_factor)

    @mcp.tool()
    def mirror_entity(
        handle: str,
        x1: float, y1: float,
        x2: float, y2: float,
        delete_original: bool = False
    ) -> dict:
        """Mirror an entity across a line defined by two points."""
        return _do_mirror(handle, x1, y1, x2, y2, delete_original)

    @mcp.tool()
    def delete_entity(handle: str) -> dict:
        """Delete an entity by its handle."""
        return _do_delete(handle)

    @mcp.tool()
    def set_entity_layer(handle: str, layer: str) -> dict:
        """Move an entity to a different layer."""
        return _do_set_layer(handle, layer)

    @mcp.tool()
    def set_entity_color(handle: str, color: str) -> dict:
        """Set the color of an entity. color can be a name or ACI integer string."""
        return _do_set_color(handle, color)

    @mcp.tool()
    def set_entity_linetype(handle: str, linetype: str) -> dict:
        """Set the linetype of an entity (e.g. 'Continuous', 'DASHED', 'CENTER')."""
        return _do_set_linetype(handle, linetype)

    @mcp.tool()
    def set_entity_lineweight(handle: str, lineweight: int) -> dict:
        """
        Set the lineweight of an entity. Valid values (in hundredths of mm):
        0, 5, 9, 13, 15, 18, 20, 25, 30, 35, 40, 50, 53, 60, 70, 80, 90, 100,
        106, 120, 140, 158, 200, 211, or -1 (ByLayer), -2 (ByBlock), -3 (Default).
        """
        return _do_set_lineweight(handle, lineweight)

    @mcp.tool()
    def explode_entity(handle: str) -> dict:
        """Explode a block reference, polyline, or other compound entity into its components."""
        return _do_explode_entity(handle)

    @mcp.tool()
    def offset_entity(handle: str, distance: float) -> dict:
        """
        Offset a line, polyline, arc, circle, or spline by the given distance.
        Returns the handles of the new offset entities.
        """
        return _do_offset_entity(handle, distance)

    @mcp.tool()
    def copy_region(
        x1: float, y1: float, x2: float, y2: float,
        dx: float, dy: float,
        layer_filter: list[str] = None,
    ) -> dict:
        """
        Copy every entity whose bounding box overlaps the region (x1,y1)-(x2,y2),
        offset by (dx, dy). Optionally restrict to specific layers.
        Returns the count and handles of the new copies.
        """
        space = get_model_space()
        origin = _make_variant([0.0, 0.0, 0.0])
        displacement = _make_variant([float(dx), float(dy), 0.0])
        new_handles = []
        for obj in _region_objects(space, x1, y1, x2, y2, layer_filter):
            copy = obj.Copy()
            copy.Move(origin, displacement)
            new_handles.append(copy.Handle)
        return {"copied_count": len(new_handles), "new_handles": new_handles}

    @mcp.tool()
    def move_region(
        x1: float, y1: float, x2: float, y2: float,
        dx: float, dy: float,
        layer_filter: list[str] = None,
    ) -> dict:
        """
        Move every entity whose bounding box overlaps the region (x1,y1)-(x2,y2)
        by the displacement (dx, dy). Optionally restrict to specific layers.
        Returns the count and handles of the moved entities.
        """
        space = get_model_space()
        origin = _make_variant([0.0, 0.0, 0.0])
        displacement = _make_variant([float(dx), float(dy), 0.0])
        handles = []
        for obj in _region_objects(space, x1, y1, x2, y2, layer_filter):
            obj.Move(origin, displacement)
            handles.append(obj.Handle)
        return {"moved_count": len(handles), "handles": handles}

    @mcp.tool()
    def mirror_region(
        x1: float, y1: float, x2: float, y2: float,
        mirror_x1: float, mirror_y1: float,
        mirror_x2: float, mirror_y2: float,
        delete_original: bool = False,
        layer_filter: list[str] = None,
    ) -> dict:
        """
        Mirror every entity whose bounding box overlaps the region (x1,y1)-(x2,y2)
        across the axis defined by (mirror_x1,mirror_y1)-(mirror_x2,mirror_y2).
        Optionally delete originals and restrict to specific layers.
        Returns the count and handles of the mirrored entities.
        """
        space = get_model_space()
        mp1 = point(mirror_x1, mirror_y1)
        mp2 = point(mirror_x2, mirror_y2)
        new_handles = []
        for obj in _region_objects(space, x1, y1, x2, y2, layer_filter):
            mirrored = obj.Mirror(mp1, mp2)
            new_handles.append(mirrored.Handle)
            if delete_original:
                obj.Delete()
        return {"mirrored_count": len(new_handles), "new_handles": new_handles}

    @mcp.tool()
    def batch_delete(handles: list[str]) -> dict:
        """
        Delete multiple entities in one call given a list of handles.
        Returns the count of deleted entities and any handles that failed.
        """
        doc = get_active_doc()
        deleted = 0
        failed = []
        for handle in handles:
            try:
                doc.HandleToObject(handle).Delete()
                deleted += 1
            except Exception:
                failed.append(handle)
        return {"deleted_count": deleted, "failed_handles": failed}

    @mcp.tool()
    def batch_execute(operations: list[dict]) -> list[dict]:
        """
        Execute any sequence of drawing operations in a single server-side call.
        Each operation is a dict with an 'op' key plus the parameters for that op.
        Operations that fail are reported with status='error'; others continue.
        Returns one result dict per operation, in order.

        ── Object manipulation ─────────────────────────────────────────────────
          move            {op, handle, dx, dy, dz=0}
          copy            {op, handle, dx, dy, dz=0}             → new_handle
          mirror          {op, handle, x1,y1, x2,y2,
                           delete_original=false}                 → new_handle
          rotate          {op, handle, pivot_x, pivot_y, angle_deg}
          scale           {op, handle, base_x, base_y, factor}
          delete          {op, handle}
          set_layer       {op, handle, layer}
          set_color       {op, handle, color}
          set_linetype    {op, handle, linetype}
          set_lineweight  {op, handle, lineweight}
          offset          {op, handle, distance}                  → new_handles
          explode         {op, handle}                            → new_handles

        ── Drawing ────────────────────────────────────────────────────────────
          draw_line       {op, x1,y1, x2,y2, layer=""}           → handle
          draw_circle     {op, cx,cy, radius, layer=""}           → handle
          draw_arc        {op, cx,cy, radius, start_angle_deg,
                           end_angle_deg, layer=""}               → handle
          draw_rectangle  {op, x1,y1, x2,y2, layer=""}           → handle
          draw_polyline   {op, points_flat:[x,y,...],
                           closed=false, layer=""}                → handle
          draw_text       {op, x,y, text, height=2.5,
                           rotation_deg=0, layer=""}              → handle
          draw_mtext      {op, x,y, text, width=100,
                           height=2.5, layer=""}                  → handle
          draw_ellipse    {op, cx,cy, major_x,major_y,
                           ratio, layer=""}                       → handle
          draw_spline     {op, points_flat:[x,y,z,...],
                           layer=""}                              → handle
          draw_hatch      {op, boundary_x1,boundary_y1,
                           boundary_x2,boundary_y2,
                           pattern="ANSI31", scale=1, layer=""}  → handle

        ── Blocks & dimensions ────────────────────────────────────────────────
          insert_block    {op, name, x,y, z=0,
                           x_scale=1, y_scale=1, z_scale=1,
                           rotation_deg=0, layer=""}              → handle
          set_attr        {op, handle, tag, value}
          dim_linear      {op, x1,y1, x2,y2, text_x,text_y,
                           layer=""}                              → handle
          dim_radius      {op, handle, leader_x,leader_y,
                           layer=""}                              → handle
          dim_angular     {op, arc_x,arc_y, x1,y1, x2,y2,
                           text_x,text_y, layer=""}              → handle
          dim_diameter    {op, handle, leader_x,leader_y,
                           layer=""}                              → handle
          dim_ordinate    {op, feature_x,feature_y,
                           leader_x,leader_y,
                           use_x_axis=false, layer=""}            → handle
          add_leader      {op, points_flat:[x,y,z,...],
                           annotation, layer=""}                  → handle

        ── Tables ─────────────────────────────────────────────────────────────
          create_table    {op, x,y, num_rows,num_cols,
                           row_height=8, col_width=40,
                           title="", layer=""}                    → handle
          set_table_cell  {op, handle, row, col, value}
          set_col_width   {op, handle, col, width}
          set_row_height  {op, handle, row, height}

        ── Arrays ─────────────────────────────────────────────────────────────
          rect_array      {op, handle, num_rows,num_cols,
                           row_spacing,col_spacing,
                           rotation_deg=0}                        → handles
          polar_array     {op, handle, center_x,center_y,
                           num_items, total_angle_deg=360,
                           rotate_items=true}                     → handles
          grid_array      {op, handle, num_rows,num_cols,
                           row_spacing,col_spacing,
                           x_offset_per_row=0}                   → handles
        """
        results = []
        for i, op_dict in enumerate(operations):
            entry: dict = {"index": i, "op": op_dict.get("op", "?")}
            try:
                res = _exec_op(op_dict)
                entry.update(res)
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)
            results.append(entry)
        return results
