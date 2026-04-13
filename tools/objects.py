"""
tools/objects.py
Tools for selecting, manipulating, and modifying existing AutoCAD objects.
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_active_doc, get_model_space, ensure_layer, point, color_index


def _make_variant(values):
    return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in values])


def _exec_op(doc, space, op_dict):
    """Execute a single batch_execute operation dict. Returns a result dict."""
    op = str(op_dict.get("op", "")).lower()

    if op == "move":
        obj = doc.HandleToObject(op_dict["handle"])
        obj.Move(_make_variant([0, 0, 0]),
                 _make_variant([op_dict["dx"], op_dict["dy"], op_dict.get("dz", 0)]))
        return {"status": "ok"}

    if op == "copy":
        obj = doc.HandleToObject(op_dict["handle"])
        cp = obj.Copy()
        cp.Move(_make_variant([0, 0, 0]),
                _make_variant([op_dict["dx"], op_dict["dy"], op_dict.get("dz", 0)]))
        return {"status": "ok", "new_handle": cp.Handle}

    if op == "mirror":
        obj = doc.HandleToObject(op_dict["handle"])
        mirrored = obj.Mirror(point(op_dict["x1"], op_dict["y1"]),
                              point(op_dict["x2"], op_dict["y2"]))
        if op_dict.get("delete_original", False):
            obj.Delete()
        return {"status": "ok", "new_handle": mirrored.Handle}

    if op == "rotate":
        obj = doc.HandleToObject(op_dict["handle"])
        obj.Rotate(point(op_dict["pivot_x"], op_dict["pivot_y"]),
                   math.radians(float(op_dict["angle_deg"])))
        return {"status": "ok"}

    if op == "scale":
        obj = doc.HandleToObject(op_dict["handle"])
        obj.ScaleEntity(point(op_dict["base_x"], op_dict["base_y"]), float(op_dict["factor"]))
        return {"status": "ok"}

    if op == "delete":
        doc.HandleToObject(op_dict["handle"]).Delete()
        return {"status": "ok"}

    if op == "set_layer":
        ensure_layer(doc, op_dict["layer"])
        doc.HandleToObject(op_dict["handle"]).Layer = op_dict["layer"]
        return {"status": "ok"}

    if op == "set_color":
        obj = doc.HandleToObject(op_dict["handle"])
        try:
            obj.color = int(op_dict["color"])
        except (ValueError, TypeError):
            obj.color = color_index(str(op_dict["color"]))
        return {"status": "ok"}

    if op == "draw_line":
        line = space.AddLine(point(op_dict["x1"], op_dict["y1"]),
                             point(op_dict["x2"], op_dict["y2"]))
        if op_dict.get("layer"):
            ensure_layer(doc, op_dict["layer"])
            line.Layer = op_dict["layer"]
        return {"status": "ok", "handle": line.Handle}

    if op == "draw_circle":
        circle = space.AddCircle(point(op_dict["cx"], op_dict["cy"]),
                                 float(op_dict["radius"]))
        if op_dict.get("layer"):
            ensure_layer(doc, op_dict["layer"])
            circle.Layer = op_dict["layer"]
        return {"status": "ok", "handle": circle.Handle}

    if op == "draw_polyline":
        pts = op_dict["points"]  # list of [x, y]
        flat = [coord for xy in pts for coord in (float(xy[0]), float(xy[1]))]
        pline = space.AddLightWeightPolyline(_make_variant(flat))
        if op_dict.get("closed", False):
            pline.Closed = True
        if op_dict.get("layer"):
            ensure_layer(doc, op_dict["layer"])
            pline.Layer = op_dict["layer"]
        return {"status": "ok", "handle": pline.Handle}

    raise ValueError(f"Unknown operation: '{op_dict.get('op')}'")



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
            # Append bounding info where available
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
        # Type-specific extras
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
        return info

    @mcp.tool()
    def move_entity(handle: str, dx: float, dy: float, dz: float = 0.0) -> str:
        """Move an entity by a displacement vector (dx, dy, dz)."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        origin = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0]
        )
        displacement = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(dx), float(dy), float(dz)]
        )
        obj.Move(origin, displacement)
        return f"Entity {handle} moved by ({dx}, {dy}, {dz})"

    @mcp.tool()
    def copy_entity(handle: str, dx: float, dy: float, dz: float = 0.0) -> str:
        """Copy an entity and place the copy offset by (dx, dy, dz)."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        origin = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0]
        )
        displacement = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(dx), float(dy), float(dz)]
        )
        copy = obj.Copy()
        copy.Move(origin, displacement)
        return f"Entity {handle} copied; new handle = {copy.Handle}"

    @mcp.tool()
    def rotate_entity(
        handle: str,
        pivot_x: float, pivot_y: float,
        angle_deg: float
    ) -> str:
        """Rotate an entity around a pivot point by angle_deg degrees."""
        import math
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Rotate(point(pivot_x, pivot_y), math.radians(angle_deg))
        return f"Entity {handle} rotated {angle_deg}° around ({pivot_x}, {pivot_y})"

    @mcp.tool()
    def scale_entity(
        handle: str,
        base_x: float, base_y: float,
        scale_factor: float
    ) -> str:
        """Scale an entity uniformly from a base point."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.ScaleEntity(point(base_x, base_y), float(scale_factor))
        return f"Entity {handle} scaled by {scale_factor} from ({base_x}, {base_y})"

    @mcp.tool()
    def mirror_entity(
        handle: str,
        x1: float, y1: float,
        x2: float, y2: float,
        delete_original: bool = False
    ) -> str:
        """Mirror an entity across a line defined by two points."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        mirrored = obj.Mirror(point(x1, y1), point(x2, y2))
        if delete_original:
            obj.Delete()
            return f"Entity {handle} mirrored and original deleted; new handle = {mirrored.Handle}"
        return f"Entity {handle} mirrored; new handle = {mirrored.Handle}"

    @mcp.tool()
    def delete_entity(handle: str) -> str:
        """Delete an entity by its handle."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Delete()
        return f"Entity {handle} deleted"

    @mcp.tool()
    def set_entity_layer(handle: str, layer: str) -> str:
        """Move an entity to a different layer."""
        doc = get_active_doc()
        ensure_layer(doc, layer)
        obj = doc.HandleToObject(handle)
        obj.Layer = layer
        return f"Entity {handle} moved to layer '{layer}'"

    @mcp.tool()
    def set_entity_color(handle: str, color: str) -> str:
        """Set the color of an entity. color can be a name or ACI integer string."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        try:
            idx = int(color)
        except ValueError:
            idx = color_index(color)
        obj.color = idx
        return f"Entity {handle} color set to {color}"

    @mcp.tool()
    def set_entity_linetype(handle: str, linetype: str) -> str:
        """Set the linetype of an entity (e.g. 'Continuous', 'DASHED', 'CENTER')."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Linetype = linetype
        return f"Entity {handle} linetype set to '{linetype}'"

    @mcp.tool()
    def set_entity_lineweight(handle: str, lineweight: int) -> str:
        """
        Set the lineweight of an entity. Valid values (in hundredths of mm):
        0, 5, 9, 13, 15, 18, 20, 25, 30, 35, 40, 50, 53, 60, 70, 80, 90, 100,
        106, 120, 140, 158, 200, 211, or -1 (ByLayer), -2 (ByBlock), -3 (Default).
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Lineweight = int(lineweight)
        return f"Entity {handle} lineweight set to {lineweight}"

    @mcp.tool()
    def explode_entity(handle: str) -> str:
        """Explode a block reference, polyline, or other compound entity into its components."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        result = obj.Explode()
        handles = [r.Handle for r in result]
        obj.Delete()
        return f"Entity {handle} exploded into {len(handles)} objects: {handles}"

    @mcp.tool()
    def offset_entity(handle: str, distance: float) -> str:
        """
        Offset a line, polyline, arc, circle, or spline by the given distance.
        Returns the handle of the new offset entity.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        result = obj.Offset(float(distance))
        new_handles = [r.Handle for r in result]
        return f"Entity {handle} offset by {distance}; new handles: {new_handles}"

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
        origin = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0]
        )
        displacement = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(dx), float(dy), 0.0]
        )
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
        origin = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0]
        )
        displacement = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(dx), float(dy), 0.0]
        )
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
        Each operation is a dict with an 'op' key and its parameters.

        Supported operations:
          move        — {op, handle, dx, dy, dz=0}
          copy        — {op, handle, dx, dy, dz=0}           → new_handle
          mirror      — {op, handle, x1, y1, x2, y2, delete_original=false} → new_handle
          rotate      — {op, handle, pivot_x, pivot_y, angle_deg}
          scale       — {op, handle, base_x, base_y, factor}
          delete      — {op, handle}
          set_layer   — {op, handle, layer}
          set_color   — {op, handle, color}
          draw_line   — {op, x1, y1, x2, y2, layer=""}      → handle
          draw_circle — {op, cx, cy, radius, layer=""}       → handle
          draw_polyline — {op, points: [[x,y],...], closed=false, layer=""} → handle

        Every task phase (delete, draw, move, mirror, copy) becomes a single call.
        Operations that fail are reported with status='error'; others continue.
        Returns one result dict per operation, in order.
        """
        doc = get_active_doc()
        space = get_model_space()
        results = []
        for i, op_dict in enumerate(operations):
            entry: dict = {"index": i, "op": op_dict.get("op", "?")}
            try:
                res = _exec_op(doc, space, op_dict)
                entry.update(res)
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)
            results.append(entry)
        return results
