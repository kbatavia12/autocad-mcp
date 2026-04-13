"""
tools/query.py
Tools for inspecting and querying AutoCAD drawings and their contents.
"""

import math
from autocad_helpers import get_acad, get_active_doc, get_model_space, point


def _region_objects(space, x1, y1, x2, y2, layer_filter=None, type_filter=None):
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
                if type_filter and obj.ObjectName not in type_filter:
                    continue
                result.append(obj)
        except Exception:
            pass
    return result


def _bbox_info(obj):
    """Return bounding box fields for an entity dict."""
    try:
        mn, mx = obj.GetBoundingBox()
        cx = (mn[0] + mx[0]) / 2
        cy = (mn[1] + mx[1]) / 2
        return {
            "center_x": round(cx, 3),
            "center_y": round(cy, 3),
            "width": round(mx[0] - mn[0], 3),
            "height": round(mx[1] - mn[1], 3),
        }
    except Exception:
        return {"center_x": None, "center_y": None, "width": None, "height": None}


def _describe_entity(obj):
    """Return a human-readable description string for an entity."""
    t = obj.ObjectName
    try:
        if t == "AcDbLine":
            sp = list(obj.StartPoint)
            ep = list(obj.EndPoint)
            length = round(obj.Length, 2)
            return (f"Line from ({round(sp[0],1)},{round(sp[1],1)}) "
                    f"to ({round(ep[0],1)},{round(ep[1],1)}), length={length}")
        if t == "AcDbCircle":
            c = list(obj.Center)
            return f"Circle, radius={round(obj.Radius,2)}, center=({round(c[0],1)},{round(c[1],1)})"
        if t == "AcDbArc":
            return f"Arc, radius={round(obj.Radius,2)}"
        if t == "AcDbLwPolyline":
            bb = _bbox_info(obj)
            return f"Polyline, {bb['width']}×{bb['height']}"
        if t in ("AcDbText", "AcDbMText"):
            return f"Text: '{obj.TextString[:60]}'"
        if t == "AcDbBlockReference":
            return f"Block: {obj.Name}"
        if t == "AcDbHatch":
            return f"Hatch: {obj.PatternName}"
        if t.startswith("AcDbDim"):
            return f"Dimension ({t})"
    except Exception:
        pass
    return t


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
        x1: float, y1: float, x2: float, y2: float,
        layer_filter: list[str] = None,
        type_filter: list[str] = None,
    ) -> list[dict]:
        """
        Return all entities whose bounding boxes overlap the given rectangular region.
        layer_filter: optional list of layer names to include (case-insensitive).
        type_filter: optional list of entity types to include (e.g. ['AcDbLine', 'AcDbCircle']).
        """
        space = get_model_space()
        return [
            {"handle": obj.Handle, "type": obj.ObjectName, "layer": obj.Layer}
            for obj in _region_objects(space, x1, y1, x2, y2, layer_filter, type_filter)
        ]

    @mcp.tool()
    def identify_entity(handle: str) -> dict:
        """
        Return type, layer, bounding box, centre, and a human-readable description
        for a single entity — all in one call.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        info = {
            "handle": handle,
            "type": obj.ObjectName,
            "layer": obj.Layer,
        }
        info.update(_bbox_info(obj))
        info["description"] = _describe_entity(obj)
        return info

    @mcp.tool()
    def batch_get_bounding_box(handles: list[str]) -> list[dict]:
        """
        Return bounding box info for multiple entities in one call.
        Each result includes: handle, min, max, width, height, center_x, center_y.
        Entities that fail (deleted, no bbox support) are silently skipped.
        """
        doc = get_active_doc()
        results = []
        for handle in handles:
            try:
                obj = doc.HandleToObject(handle)
                mn, mx = obj.GetBoundingBox()
                results.append({
                    "handle": handle,
                    "min": [round(mn[0], 3), round(mn[1], 3)],
                    "max": [round(mx[0], 3), round(mx[1], 3)],
                    "width": round(mx[0] - mn[0], 3),
                    "height": round(mx[1] - mn[1], 3),
                    "center_x": round((mn[0] + mx[0]) / 2, 3),
                    "center_y": round((mn[1] + mx[1]) / 2, 3),
                })
            except Exception:
                pass
        return results

    @mcp.tool()
    def get_room_summary(x1: float, y1: float, x2: float, y2: float) -> dict:
        """
        Return a categorised spatial overview of all entities within a region.
        Each entity is classified into walls / furniture / openings / annotations / other
        based on its layer name. Returns handle, type, layer, centre, and size for each.
        Useful for understanding the room layout without taking screenshots.
        """
        space = get_model_space()
        objs = _region_objects(space, x1, y1, x2, y2)

        walls = []
        furniture = []
        openings = []
        annotations = []
        other = []

        for obj in objs:
            layer_up = obj.Layer.upper()
            type_name = obj.ObjectName
            entry = {"handle": obj.Handle, "type": type_name, "layer": obj.Layer}
            entry.update(_bbox_info(obj))

            if "WALL" in layer_up:
                walls.append(entry)
            elif any(k in layer_up for k in ("FURN", "EQUIP", "CABIN", "FURNITURE")):
                furniture.append(entry)
            elif any(k in layer_up for k in ("DOOR", "GLAZ", "WINDOW")):
                openings.append(entry)
            elif (any(k in layer_up for k in ("DIM", "TEXT", "ANNO", "NOTE"))
                  or type_name in ("AcDbText", "AcDbMText")
                  or type_name.startswith("AcDbDim")):
                annotations.append(entry)
            else:
                other.append(entry)

        return {
            "walls": walls,
            "furniture": furniture,
            "openings": openings,
            "annotations": annotations,
            "other": other,
            "total": len(objs),
        }

    @mcp.tool()
    def get_drawing_context() -> dict:
        """
        Return everything needed to orient yourself at the start of any task:
        active layer, drawing units, all layers (name/color/state), all named
        block definitions, all dimension styles, and all text labels with their
        positions.  Replaces 10–15 individual orientation calls with 1.
        """
        doc = get_active_doc()
        space = get_model_space()

        # Layers
        layers = []
        for i in range(doc.Layers.Count):
            lyr = doc.Layers.Item(i)
            layers.append({
                "name": lyr.Name,
                "color": lyr.color,
                "linetype": lyr.Linetype,
                "on": lyr.LayerOn,
                "frozen": lyr.Freeze,
                "locked": lyr.Lock,
            })

        # Named block definitions (skip *Model_Space, *Paper_Space, etc.)
        blocks = []
        for blk in doc.Blocks:
            if not blk.Name.startswith("*"):
                blocks.append({"name": blk.Name, "entity_count": blk.Count})

        # Dimension styles
        dim_styles = [doc.DimStyles.Item(i).Name for i in range(doc.DimStyles.Count)]

        # Text labels (AcDbText + AcDbMText) with insertion points
        text_labels = []
        for i in range(space.Count):
            obj = space.Item(i)
            if obj.ObjectName not in ("AcDbText", "AcDbMText"):
                continue
            try:
                pt = list(obj.InsertionPoint)
                text_labels.append({
                    "text": obj.TextString[:120],
                    "x": round(pt[0], 2),
                    "y": round(pt[1], 2),
                    "layer": obj.Layer,
                    "type": obj.ObjectName,
                })
            except Exception:
                pass
            if len(text_labels) >= 300:
                break

        return {
            "active_layer": doc.ActiveLayer.Name,
            "units": doc.GetVariable("INSUNITS"),
            "entity_count": space.Count,
            "layers": layers,
            "blocks": blocks,
            "dim_styles": dim_styles,
            "text_labels": text_labels,
        }

    @mcp.tool()
    def identify_entities(handles: list[str]) -> list[dict]:
        """
        Return type, layer, bounding box, centre, rotation, block name, and a
        human-readable description for every handle in the list — all in one call.
        Entities that fail (deleted, unsupported) are returned with status='error'.
        Replaces N sequential identify_entity calls with 1.
        """
        doc = get_active_doc()
        results = []
        for handle in handles:
            entry: dict = {"handle": handle}
            try:
                obj = doc.HandleToObject(handle)
                entry["type"] = obj.ObjectName
                entry["layer"] = obj.Layer
                entry.update(_bbox_info(obj))
                entry["description"] = _describe_entity(obj)
                try:
                    entry["rotation_deg"] = round(math.degrees(obj.Rotation), 3)
                except Exception:
                    entry["rotation_deg"] = None
                try:
                    entry["block_name"] = obj.Name  # block references
                except Exception:
                    entry["block_name"] = None
                entry["status"] = "ok"
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)
            results.append(entry)
        return results

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
