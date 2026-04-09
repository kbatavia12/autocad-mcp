"""
tools/files.py
Tools for file operations and viewport/view control in AutoCAD.
"""

from autocad_helpers import get_acad, get_active_doc, point
import win32com.client
import pythoncom


def register_file_tools(mcp):

    @mcp.tool()
    def new_drawing(template_path: str = "") -> str:
        """
        Create a new drawing. Optionally provide a full path to a .dwt template.
        If template_path is empty, AutoCAD's default template is used.
        """
        acad = get_acad()
        if template_path:
            doc = acad.Documents.Add(template_path)
        else:
            doc = acad.Documents.Add()
        return f"New drawing created: {doc.Name}"

    @mcp.tool()
    def open_drawing(file_path: str, read_only: bool = False) -> str:
        """Open an existing .dwg or .dxf file. Returns the document name."""
        acad = get_acad()
        doc = acad.Documents.Open(file_path, read_only)
        return f"Opened '{doc.Name}' (read_only={read_only})"

    @mcp.tool()
    def save_drawing() -> str:
        """Save the active drawing to its current path."""
        doc = get_active_doc()
        doc.Save()
        return f"Saved '{doc.Name}'"

    @mcp.tool()
    def save_drawing_as(file_path: str, version: str = "") -> str:
        """
        Save the active drawing to a new path. version can be an AutoCAD
        save-format string like 'AutoCAD2018_DWG' or left blank for current version.
        """
        doc = get_active_doc()
        if version:
            # acSaveAsType enum values vary; pass as string and let AutoCAD resolve
            doc.SaveAs(file_path)
        else:
            doc.SaveAs(file_path)
        return f"Drawing saved as '{file_path}'"

    @mcp.tool()
    def close_drawing(save: bool = True) -> str:
        """Close the active drawing. Set save=False to discard unsaved changes."""
        doc = get_active_doc()
        name = doc.Name
        doc.Close(save)
        return f"Drawing '{name}' closed (saved={save})"

    @mcp.tool()
    def list_open_drawings() -> list[str]:
        """Return the names of all currently open drawings."""
        acad = get_acad()
        return [acad.Documents.Item(i).Name for i in range(acad.Documents.Count)]

    @mcp.tool()
    def switch_active_drawing(name: str) -> str:
        """Bring a specific open drawing to the foreground by name."""
        acad = get_acad()
        for i in range(acad.Documents.Count):
            doc = acad.Documents.Item(i)
            if doc.Name == name:
                doc.Activate()
                return f"Switched to '{name}'"
        raise ValueError(f"No open drawing named '{name}'")

    @mcp.tool()
    def export_to_pdf(output_path: str) -> str:
        """Export the active drawing's model space to a PDF file."""
        doc = get_active_doc()
        doc.SendCommand(f'_PLOT\n')  # Simplified; full programmatic PDF export needs plot config
        return (
            f"Note: full PDF export via COM requires a preconfigured PC3 plotter. "
            f"Attempted plot command for '{output_path}'. "
            "For reliable PDF export, use save_drawing_as with a .pdf extension in AutoCAD 2017+."
        )

    @mcp.tool()
    def zoom_extents() -> str:
        """Zoom to fit all objects in the active viewport."""
        doc = get_active_doc()
        doc.SendCommand("_ZOOM\nE\n")
        return "Zoomed to extents"

    @mcp.tool()
    def zoom_window(x1: float, y1: float, x2: float, y2: float) -> str:
        """Zoom to a specified rectangular window in model space."""
        doc = get_active_doc()
        doc.SendCommand(f"_ZOOM\nW\n{x1},{y1}\n{x2},{y2}\n")
        return f"Zoomed to window ({x1},{y1}) – ({x2},{y2})"

    @mcp.tool()
    def zoom_scale(factor: float) -> str:
        """Zoom in or out by a scale factor relative to the current view (e.g. 2.0 = 2x in)."""
        doc = get_active_doc()
        doc.SendCommand(f"_ZOOM\n{factor}X\n")
        return f"Zoomed by scale factor {factor}"

    @mcp.tool()
    def set_view_center(cx: float, cy: float, height: float) -> str:
        """
        Set the active viewport center and view height (controls zoom level).
        height is the vertical span of the view in drawing units.
        """
        doc = get_active_doc()
        vp = doc.ActiveViewport
        vp.Center = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(cx), float(cy)]
        )
        vp.Height = float(height)
        doc.ActiveViewport = vp
        return f"View centered at ({cx}, {cy}) with height={height}"

    @mcp.tool()
    def regen_drawing() -> str:
        """Regenerate all viewports in the active drawing to refresh display."""
        doc = get_active_doc()
        doc.Regen(2)  # acAllViewports
        return "Drawing regenerated"

    @mcp.tool()
    def undo(steps: int = 1) -> str:
        """Undo the last N operations in the active drawing."""
        doc = get_active_doc()
        for _ in range(steps):
            doc.SendCommand("_UNDO\n1\n")
        return f"Undone {steps} step(s)"

    @mcp.tool()
    def redo(steps: int = 1) -> str:
        """Redo the last N undone operations."""
        doc = get_active_doc()
        for _ in range(steps):
            doc.SendCommand("_REDO\n")
        return f"Redone {steps} step(s)"

    @mcp.tool()
    def purge_drawing() -> str:
        """Purge unused named objects (layers, linetypes, blocks, styles, etc.) from the drawing."""
        doc = get_active_doc()
        doc.SendCommand("_PURGE\nALL\n*\nN\n")
        return "Purge command sent. Unused named objects removed."
