"""
tools/blocks_xrefs_styles.py
Tools for block definitions & attributes, external references (XRefs),
text styles, dimension styles, multileaders, and tables.
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_active_doc, get_model_space, point


# ---------------------------------------------------------------------------
# Batchable _do_* functions
# ---------------------------------------------------------------------------

def _do_set_block_attribute_value(handle: str, tag: str, value: str) -> dict:
    doc = get_active_doc()
    obj = doc.HandleToObject(handle)
    for attr in obj.GetAttributes():
        if attr.TagString.upper() == tag.upper():
            attr.TextString = value
            obj.Update()
            return {"status": "ok", "message": f"Attribute '{tag}' on {handle} set to '{value}'"}
    raise ValueError(f"Attribute tag '{tag}' not found on block {handle}")


def _do_add_angular_dimension(
    arc_x: float, arc_y: float,
    x1: float, y1: float,
    x2: float, y2: float,
    text_x: float, text_y: float,
    layer: str = "",
) -> dict:
    space = get_model_space()
    dim = space.AddDimAngular(
        [arc_x, arc_y, 0.0], [x1, y1, 0.0],
        [x2, y2, 0.0], [text_x, text_y, 0.0],
    )
    if layer:
        dim.Layer = layer
    return {"status": "ok", "handle": dim.Handle, "message": "Angular dimension added"}


def _do_add_diameter_dimension(
    handle: str,
    leader_x: float, leader_y: float,
    layer: str = "",
) -> dict:
    doc = get_active_doc()
    space = get_model_space()
    obj = doc.HandleToObject(handle)
    dim = space.AddDimDiametric(
        list(obj.Center), [leader_x, leader_y, 0.0],
        abs(leader_x - obj.Center[0]),
    )
    if layer:
        dim.Layer = layer
    return {"status": "ok", "handle": dim.Handle, "message": f"Diameter dimension on {handle}"}


def _do_add_ordinate_dimension(
    feature_x: float, feature_y: float,
    leader_x: float, leader_y: float,
    use_x_axis: bool = False,
    layer: str = "",
) -> dict:
    space = get_model_space()
    dim = space.AddDimOrdinate(
        [feature_x, feature_y, 0.0], [leader_x, leader_y, 0.0], use_x_axis,
    )
    if layer:
        dim.Layer = layer
    return {"status": "ok", "handle": dim.Handle, "message": "Ordinate dimension added"}


def _do_add_leader(points_flat: list, annotation: str, layer: str = "") -> dict:
    space = get_model_space()
    pts = win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in points_flat]
    )
    leader = space.AddLeader(pts, None, 1)
    mtext = space.AddMText(
        [float(points_flat[-3]), float(points_flat[-2]), 0.0], 50.0, annotation,
    )
    leader.Annotation = mtext
    if layer:
        leader.Layer = layer
        mtext.Layer = layer
    return {"status": "ok", "handle": leader.Handle,
            "message": f"Leader with annotation '{annotation}'"}


def _do_create_table(
    x: float, y: float,
    num_rows: int, num_cols: int,
    row_height: float = 8.0, col_width: float = 40.0,
    title: str = "", layer: str = "",
) -> dict:
    space = get_model_space()
    table = space.AddTable(
        point(x, y), int(num_rows), int(num_cols),
        float(row_height), float(col_width),
    )
    if title:
        table.SetText(0, 0, title)
        table.SetRowHeight(0, row_height * 1.5)
    if layer:
        table.Layer = layer
    return {"status": "ok", "handle": table.Handle,
            "message": f"Table {num_rows}×{num_cols} at ({x},{y})"}


def _do_set_table_cell(handle: str, row: int, col: int, value: str) -> dict:
    doc = get_active_doc()
    doc.HandleToObject(handle).SetText(int(row), int(col), value)
    return {"status": "ok", "message": f"Table {handle} cell ({row},{col}) = '{value}'"}


def _do_set_table_column_width(handle: str, col: int, width: float) -> dict:
    doc = get_active_doc()
    doc.HandleToObject(handle).SetColumnWidth(int(col), float(width))
    return {"status": "ok", "message": f"Table {handle} col {col} width={width}"}


def _do_set_table_row_height(handle: str, row: int, height: float) -> dict:
    doc = get_active_doc()
    doc.HandleToObject(handle).SetRowHeight(int(row), float(height))
    return {"status": "ok", "message": f"Table {handle} row {row} height={height}"}


def register_blocks_xrefs_styles_tools(mcp):

    # -----------------------------------------------------------------------
    # BLOCK DEFINITIONS & ATTRIBUTES
    # -----------------------------------------------------------------------

    @mcp.tool()
    def create_block_definition(
        name: str,
        base_x: float = 0.0, base_y: float = 0.0
    ) -> str:
        """
        Create a new empty block definition with a given name and base point.
        Once created, add geometry to it using draw_* tools with the block's
        model space, then insert it with insert_block.
        """
        doc = get_active_doc()
        base = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(base_x), float(base_y), 0.0]
        )
        doc.Blocks.Add(base, name)
        return f"Block definition '{name}' created with base point ({base_x}, {base_y})"

    @mcp.tool()
    def add_attribute_to_block(
        block_name: str,
        tag: str,
        prompt: str,
        default_value: str,
        x: float, y: float,
        height: float = 2.5,
        invisible: bool = False
    ) -> str:
        """
        Add an attribute definition to an existing block definition.
        tag: the attribute tag (e.g. 'ROOM_NAME')
        prompt: the prompt shown when inserting (e.g. 'Enter room name:')
        default_value: the default attribute value
        invisible: if True, the attribute is not displayed in the drawing
        """
        doc = get_active_doc()
        block = doc.Blocks.Item(block_name)
        insertion = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y), 0.0]
        )
        block.AddAttribute(
            float(height),
            1 if invisible else 0,  # acAttributeModeInvisible or acAttributeModeNormal
            prompt,
            insertion,
            tag,
            default_value
        )
        return f"Attribute '{tag}' added to block '{block_name}'"

    @mcp.tool()
    def list_block_attributes(handle: str) -> list[dict]:
        """
        List all attributes of a block reference entity (by handle).
        Returns tag names and current values.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        result = []
        for attr in obj.GetAttributes():
            result.append({
                "tag": attr.TagString,
                "value": attr.TextString,
                "prompt": attr.PromptString,
                "invisible": attr.Invisible,
                "handle": attr.Handle,
            })
        return result

    @mcp.tool()
    def set_block_attribute_value(handle: str, tag: str, value: str) -> dict:
        """
        Set the value of a specific attribute on a block reference.
        handle: the block reference entity handle
        tag: the attribute tag name to update
        value: the new value to set
        """
        return _do_set_block_attribute_value(handle, tag, value)

    @mcp.tool()
    def sync_block_attributes(block_name: str) -> str:
        """
        Synchronize attribute definitions across all instances of a block.
        Useful after modifying the block definition's attributes.
        """
        doc = get_active_doc()
        doc.SendCommand(f"-ATTSYNC\nN\n{block_name}\n")
        return f"Attributes synchronized for all instances of block '{block_name}'"

    @mcp.tool()
    def rename_block(old_name: str, new_name: str) -> str:
        """Rename an existing block definition."""
        doc = get_active_doc()
        doc.SendCommand(f"-RENAME\nB\n{old_name}\n{new_name}\n")
        return f"Block '{old_name}' renamed to '{new_name}'"

    @mcp.tool()
    def purge_block(name: str) -> str:
        """Remove an unused block definition from the drawing."""
        doc = get_active_doc()
        block = doc.Blocks.Item(name)
        block.Delete()
        return f"Block definition '{name}' purged"

    # -----------------------------------------------------------------------
    # XREFS (External References)
    # -----------------------------------------------------------------------

    @mcp.tool()
    def list_xrefs() -> list[dict]:
        """List all external references (XRefs) in the active drawing."""
        doc = get_active_doc()
        result = []
        for block in doc.Blocks:
            if block.IsXRef:
                result.append({
                    "name": block.Name,
                    "path": block.Path,
                    "is_loaded": not block.IsUnloaded if hasattr(block, "IsUnloaded") else "unknown",
                })
        return result

    @mcp.tool()
    def attach_xref(
        file_path: str,
        x: float = 0.0, y: float = 0.0,
        x_scale: float = 1.0, y_scale: float = 1.0,
        rotation_deg: float = 0.0,
        overlay: bool = False
    ) -> str:
        """
        Attach an external drawing (.dwg) as an XRef.
        overlay=True attaches as an overlay (not nested when this drawing is itself xref'd).
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        insertion = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y), 0.0]
        )
        xref = space.AttachExternalReference(
            file_path,
            file_path.split("/")[-1].split("\\")[-1].replace(".dwg", ""),
            insertion,
            float(x_scale), float(y_scale), 1.0,
            math.radians(float(rotation_deg)),
            overlay,
            None
        )
        return f"XRef '{xref.Name}' attached from '{file_path}'"

    @mcp.tool()
    def detach_xref(name: str) -> str:
        """Detach (remove) an XRef from the drawing. All instances are erased."""
        doc = get_active_doc()
        doc.SendCommand(f"-XREF\nD\n{name}\n")
        return f"XRef '{name}' detached"

    @mcp.tool()
    def reload_xref(name: str) -> str:
        """Reload an XRef to reflect changes made to the source file."""
        doc = get_active_doc()
        doc.SendCommand(f"-XREF\nR\n{name}\n")
        return f"XRef '{name}' reloaded"

    @mcp.tool()
    def unload_xref(name: str) -> str:
        """Unload an XRef (keeps the reference but removes it from display)."""
        doc = get_active_doc()
        doc.SendCommand(f"-XREF\nU\n{name}\n")
        return f"XRef '{name}' unloaded"

    @mcp.tool()
    def bind_xref(name: str, insert_mode: bool = False) -> str:
        """
        Bind an XRef into the drawing, making it a permanent block.
        insert_mode=True uses INSERT bind (strips xref prefix from layer names).
        insert_mode=False uses BIND (preserves xref prefix on layer names).
        """
        mode = "I" if insert_mode else "B"
        doc = get_active_doc()
        doc.SendCommand(f"-XREF\n{mode}\n{name}\n")
        return f"XRef '{name}' bound (insert_mode={insert_mode})"

    @mcp.tool()
    def xref_clip(handle: str, clip_points: list[float]) -> str:
        """
        Clip an XRef to a polygonal boundary.
        clip_points is a flat list of XY pairs defining the clip polygon.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in clip_points]
        )
        obj.ClipBoundary(pts)
        return f"XRef {handle} clipped to {len(clip_points)//2}-point polygon"

    # -----------------------------------------------------------------------
    # TEXT STYLES
    # -----------------------------------------------------------------------

    @mcp.tool()
    def list_text_styles() -> list[dict]:
        """List all text styles in the active drawing."""
        doc = get_active_doc()
        return [
            {
                "name": s.Name,
                "font": s.fontFile,
                "height": s.Height,
                "width_factor": s.Width,
                "oblique_angle": s.ObliqueAngle,
            }
            for s in doc.TextStyles
        ]

    @mcp.tool()
    def create_text_style(
        name: str,
        font_file: str = "arial.ttf",
        height: float = 0.0,
        width_factor: float = 1.0,
        oblique_angle: float = 0.0,
        bold: bool = False,
        italic: bool = False
    ) -> str:
        """
        Create a new text style. height=0 means variable height (set per object).
        font_file can be a .ttf font name (e.g. 'arial.ttf') or .shx (e.g. 'romans.shx').
        """
        doc = get_active_doc()
        style = doc.TextStyles.Add(name)
        style.fontFile = font_file
        style.Height = float(height)
        style.Width = float(width_factor)
        style.ObliqueAngle = float(oblique_angle)
        if bold or italic:
            style.SetFont(font_file.replace(".ttf", ""), bold, italic, 0, 0)
        return f"Text style '{name}' created (font={font_file}, height={height})"

    @mcp.tool()
    def set_active_text_style(name: str) -> str:
        """Set the active text style by name."""
        doc = get_active_doc()
        doc.ActiveTextStyle = doc.TextStyles.Item(name)
        return f"Active text style set to '{name}'"

    # -----------------------------------------------------------------------
    # DIMENSION STYLES
    # -----------------------------------------------------------------------

    @mcp.tool()
    def list_dim_styles() -> list[dict]:
        """List all dimension styles in the active drawing."""
        doc = get_active_doc()
        saved = doc.ActiveDimStyle
        result = []
        for s in doc.DimStyles:
            try:
                doc.ActiveDimStyle = s
                result.append({
                    "name": s.Name,
                    "scale": doc.GetVariable("DIMSCALE"),
                    "text_height": doc.GetVariable("DIMTXT"),
                    "arrow_size": doc.GetVariable("DIMASZ"),
                    "units": doc.GetVariable("DIMLUNIT"),
                })
            except Exception:
                result.append({"name": s.Name})
        doc.ActiveDimStyle = saved
        return result

    @mcp.tool()
    def create_dim_style(
        name: str,
        scale: float = 1.0,
        text_height: float = 2.5,
        arrow_size: float = 2.5,
        linear_units: int = 2
    ) -> str:
        """
        Create a new dimension style.
        linear_units: 1=Scientific, 2=Decimal, 3=Engineering, 4=Architectural, 5=Fractional
        """
        doc = get_active_doc()
        style = doc.DimStyles.Add(name)
        doc.ActiveDimStyle = style
        doc.SetVariable("DIMSCALE", float(scale))
        doc.SetVariable("DIMTXT", float(text_height))
        doc.SetVariable("DIMASZ", float(arrow_size))
        doc.SetVariable("DIMLUNIT", int(linear_units))
        return f"Dimension style '{name}' created"

    @mcp.tool()
    def set_active_dim_style(name: str) -> str:
        """Set the active dimension style by name."""
        doc = get_active_doc()
        doc.ActiveDimStyle = doc.DimStyles.Item(name)
        return f"Active dimension style set to '{name}'"

    @mcp.tool()
    def add_angular_dimension(
        arc_x: float, arc_y: float,
        x1: float, y1: float,
        x2: float, y2: float,
        text_x: float, text_y: float,
        layer: str = ""
    ) -> dict:
        """Add an angular dimension. arc point is the vertex of the angle."""
        return _do_add_angular_dimension(arc_x, arc_y, x1, y1, x2, y2, text_x, text_y, layer)

    @mcp.tool()
    def add_diameter_dimension(
        handle: str,
        leader_x: float, leader_y: float,
        layer: str = ""
    ) -> dict:
        """Add a diameter dimension to a circle or arc."""
        return _do_add_diameter_dimension(handle, leader_x, leader_y, layer)

    @mcp.tool()
    def add_ordinate_dimension(
        feature_x: float, feature_y: float,
        leader_x: float, leader_y: float,
        use_x_axis: bool = False,
        layer: str = ""
    ) -> dict:
        """
        Add an ordinate dimension (measures distance from origin along X or Y axis).
        use_x_axis=True measures the X coordinate; False measures Y coordinate.
        """
        return _do_add_ordinate_dimension(feature_x, feature_y, leader_x, leader_y,
                                          use_x_axis, layer)

    # -----------------------------------------------------------------------
    # MULTILEADERS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def add_leader(
        points_flat: list[float],
        annotation: str,
        layer: str = ""
    ) -> dict:
        """
        Add a leader with annotation text.
        points_flat: flat list of XYZ coords for the leader line [x1,y1,z1, x2,y2,z2, ...]
        annotation: the text to display at the end of the leader
        """
        return _do_add_leader(points_flat, annotation, layer)

    # -----------------------------------------------------------------------
    # TABLES
    # -----------------------------------------------------------------------

    @mcp.tool()
    def create_table(
        x: float, y: float,
        num_rows: int, num_cols: int,
        row_height: float = 8.0,
        col_width: float = 40.0,
        title: str = "",
        layer: str = ""
    ) -> dict:
        """
        Create a table in model space.
        Returns the table handle for further cell editing.
        """
        return _do_create_table(x, y, num_rows, num_cols, row_height, col_width, title, layer)

    @mcp.tool()
    def set_table_cell(handle: str, row: int, col: int, value: str) -> dict:
        """Set the text value of a specific cell in a table (0-based row/col)."""
        return _do_set_table_cell(handle, row, col, value)

    @mcp.tool()
    def get_table_cell(handle: str, row: int, col: int) -> str:
        """Get the text value of a specific cell in a table (0-based row/col)."""
        doc = get_active_doc()
        table = doc.HandleToObject(handle)
        return table.GetText(int(row), int(col))

    @mcp.tool()
    def set_table_column_width(handle: str, col: int, width: float) -> dict:
        """Set the width of a specific column in a table (0-based col index)."""
        return _do_set_table_column_width(handle, col, width)

    @mcp.tool()
    def set_table_row_height(handle: str, row: int, height: float) -> dict:
        """Set the height of a specific row in a table (0-based row index)."""
        return _do_set_table_row_height(handle, row, height)
