"""
tools/query.py
Tools for inspecting and querying AutoCAD drawings and their contents.
"""

import math
from autocad_helpers import get_acad, get_active_doc, get_model_space, point


def register_query_tools(mcp):

    @mcp.tool()
    def get_drawing_info() -> dict:
        """Return metadata about the active drawing."""
        acad = get_acad()
        doc = get_active_doc()
        return {
            "name": doc.Name,
            "full_path": doc.FullName,
            "saved": doc.Saved,
            "read_only": doc.ReadOnly,
            "entity_count": doc.ModelSpace.Count,
            "active_layer": doc.ActiveLayer.Name,
            "autocad_version": acad.Version,
            "units": doc.GetVariable("INSUNITS"),
            "limits_min": list(doc.GetVariable("LIMMIN")),
            "limits_max": list(doc.GetVariable("LIMMAX")),
        }

    @mcp.tool()
    def count_entities_by_type() -> dict:
        """Count all entities in model space grouped by their type."""
        space = get_model_space()
        counts: dict[str, int] = {}
        for i in range(space.Count):
            obj = space.Item(i)
            t = obj.ObjectName
            counts[t] = counts.get(t, 0) + 1
        return dict(sorted(counts.items()))

    @mcp.tool()
    def get_bounding_box(handle: str) -> dict:
        """
        Return the bounding box of an entity as min/max corner points.
        Works on most entity types that support GetBoundingBox().
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        min_pt, max_pt = obj.GetBoundingBox()
        return {
            "min": list(min_pt),
            "max": list(max_pt),
            "width": max_pt[0] - min_pt[0],
            "height": max_pt[1] - min_pt[1],
        }

    @mcp.tool()
    def get_drawing_extents() -> dict:
        """Return the overall bounding extents of all objects in model space."""
        space = get_model_space()
        if space.Count == 0:
            return {"error": "No entities in model space"}
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")
        for i in range(space.Count):
            try:
                mn, mx = space.Item(i).GetBoundingBox()
                min_x = min(min_x, mn[0])
                min_y = min(min_y, mn[1])
                max_x = max(max_x, mx[0])
                max_y = max(max_y, mx[1])
            except Exception:
                pass
        return {
            "min": [min_x, min_y],
            "max": [max_x, max_y],
            "width": max_x - min_x,
            "height": max_y - min_y,
        }

    @mcp.tool()
    def measure_distance(
        x1: float, y1: float, x2: float, y2: float
    ) -> dict:
        """Calculate the straight-line distance between two 2D points."""
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        angle = math.degrees(math.atan2(dy, dx))
        return {
            "distance": dist,
            "angle_deg": angle,
            "delta_x": dx,
            "delta_y": dy,
        }

    @mcp.tool()
    def get_area(handle: str) -> dict:
        """Return the area (and perimeter where available) of a closed entity."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        result = {"handle": handle, "type": obj.ObjectName}
        try:
            result["area"] = obj.Area
        except Exception:
            result["area"] = None
        try:
            result["perimeter"] = obj.Perimeter
        except Exception:
            try:
                result["circumference"] = 2 * math.pi * obj.Radius
            except Exception:
                pass
        return result

    @mcp.tool()
    def get_system_variable(name: str) -> str:
        """Get the value of an AutoCAD system variable (e.g. 'OSMODE', 'UNITS', 'DIMSCALE')."""
        doc = get_active_doc()
        val = doc.GetVariable(name.upper())
        return f"{name.upper()} = {val}"

    @mcp.tool()
    def set_system_variable(name: str, value: str) -> str:
        """
        Set an AutoCAD system variable. value is always passed as a string;
        AutoCAD will attempt to coerce it to the correct type.
        """
        doc = get_active_doc()
        # Try int, then float, then string
        for cast in (int, float, str):
            try:
                doc.SetVariable(name.upper(), cast(value))
                return f"{name.upper()} set to {value}"
            except Exception:
                continue
        raise ValueError(f"Could not set system variable {name} to {value}")

    @mcp.tool()
    def find_entities_in_region(
        x1: float, y1: float, x2: float, y2: float
    ) -> list[dict]:
        """
        Return all entities whose bounding boxes overlap the given rectangular region.
        """
        space = get_model_space()
        result = []
        for i in range(space.Count):
            obj = space.Item(i)
            try:
                mn, mx = obj.GetBoundingBox()
                if mx[0] >= x1 and mn[0] <= x2 and mx[1] >= y1 and mn[1] <= y2:
                    result.append({
                        "handle": obj.Handle,
                        "type": obj.ObjectName,
                        "layer": obj.Layer,
                    })
            except Exception:
                pass
        return result

    @mcp.tool()
    def list_blocks() -> list[dict]:
        """List all block definitions in the active drawing."""
        doc = get_active_doc()
        result = []
        for block in doc.Blocks:
            if block.Name.startswith("*"):
                continue  # Skip model/paper space pseudo-blocks
            result.append({
                "name": block.Name,
                "entity_count": block.Count,
                "is_xref": block.IsXRef,
                "is_layout": block.IsLayout,
            })
        return result

    @mcp.tool()
    def insert_block(
        name: str,
        x: float, y: float, z: float = 0.0,
        x_scale: float = 1.0, y_scale: float = 1.0, z_scale: float = 1.0,
        rotation_deg: float = 0.0,
        layer: str = ""
    ) -> str:
        """Insert a block reference into model space by block name."""
        import math
        space = get_model_space()
        ref = space.InsertBlock(
            [x, y, z], name,
            x_scale, y_scale, z_scale,
            math.radians(rotation_deg)
        )
        if layer:
            ref.Layer = layer
        return f"Block '{name}' inserted at ({x},{y},{z}); handle={ref.Handle}"

    @mcp.tool()
    def list_linetypes() -> list[str]:
        """Return all linetypes loaded in the active drawing."""
        doc = get_active_doc()
        return [doc.Linetypes.Item(i).Name for i in range(doc.Linetypes.Count)]

    @mcp.tool()
    def load_linetype(linetype_name: str, linetype_file: str = "acad.lin") -> str:
        """
        Load a linetype from a .lin file into the drawing.
        Default file is AutoCAD's standard acad.lin.
        """
        doc = get_active_doc()
        doc.Linetypes.Load(linetype_name, linetype_file)
        return f"Linetype '{linetype_name}' loaded from '{linetype_file}'"

    @mcp.tool()
    def add_linear_dimension(
        x1: float, y1: float,
        x2: float, y2: float,
        text_x: float, text_y: float,
        layer: str = ""
    ) -> str:
        """Add a horizontal/vertical aligned linear dimension between two points."""
        space = get_model_space()
        dim = space.AddDimAligned(
            point(x1, y1),
            point(x2, y2),
            point(text_x, text_y)
        )
        if layer:
            dim.Layer = layer
        return f"Aligned dimension added; handle={dim.Handle}"

    @mcp.tool()
    def add_radius_dimension(
        handle: str,
        leader_x: float, leader_y: float,
        layer: str = ""
    ) -> str:
        """Add a radius dimension to a circle or arc entity."""
        doc = get_active_doc()
        space = get_model_space()
        obj = doc.HandleToObject(handle)
        dim = space.AddDimRadial(
            list(obj.Center),
            [leader_x, leader_y, 0.0],
            abs(leader_x - obj.Center[0])
        )
        if layer:
            dim.Layer = layer
        return f"Radius dimension added; handle={dim.Handle}"
