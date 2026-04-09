"""
tools/objects.py
Tools for selecting, manipulating, and modifying existing AutoCAD objects.
"""

import pythoncom
import win32com.client
from autocad_helpers import get_active_doc, get_model_space, point, color_index


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
