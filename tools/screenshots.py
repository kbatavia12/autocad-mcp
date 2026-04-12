"""
tools/screenshots.py
Screenshot tools — capture the current AutoCAD viewport and return the image
to Claude so it can see and reason about the current drawing state.
"""

import json
import os
import tempfile
import time

from mcp.server.fastmcp import Image

from autocad_helpers import get_acad, get_active_doc, point


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _wait_for_file(path: str, timeout: float = 10.0, poll_interval: float = 0.25) -> bool:
    """
    Poll until the file at *path* exists and its size has stabilised
    (two consecutive reads agree), indicating AutoCAD has finished writing.
    Returns True if the file is ready, False if the timeout expired.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(path):
            try:
                size1 = os.path.getsize(path)
                time.sleep(0.1)
                size2 = os.path.getsize(path)
                if size1 == size2 and size1 > 0:
                    return True
            except OSError:
                pass
        time.sleep(poll_interval)
    return False


def _capture_viewport(doc, timeout: float = 30.0) -> bytes:
    """
    Export the current model-space viewport as a PNG into a temp file,
    read the bytes, and clean up.  Returns raw PNG bytes.
    """
    temp_dir = tempfile.mkdtemp(prefix="acad_cap_")
    file_path = os.path.join(temp_dir, "capture.png")

    file_path_acad = file_path.replace("\\", "/")

    old_filedia = doc.GetVariable("FILEDIA")
    try:
        doc.SetVariable("FILEDIA", 0)   # suppress file-picker dialog
        # Cancel any leftover command, then PNGOUT
        # Prompt order: select objects (Enter=all), filename, viewport (Enter=current)
        doc.SendCommand("(command)\n")
        time.sleep(0.2)
        doc.SendCommand(f"_-PNGOUT\n\n{file_path_acad}\n\n")
        if not _wait_for_file(file_path, timeout):
            raise RuntimeError(
                f"Screenshot timed out after {timeout}s — "
                "AutoCAD may be busy or -PNGOUT is not available in this version."
            )
        with open(file_path, "rb") as fh:
            return fh.read()
    finally:
        doc.SetVariable("FILEDIA", old_filedia)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rmdir(temp_dir)
        except OSError:
            pass  # best-effort; OS will clean temp dirs eventually


def _save_view(doc) -> dict:
    """Return a snapshot of the active viewport's center and height."""
    center = tuple(doc.GetVariable("VIEWCTR"))
    height = float(doc.GetVariable("VIEWSIZE"))
    return {"center": center, "height": height}


def _restore_view(doc, state: dict) -> None:
    """Restore a viewport snapshot saved with _save_view()."""
    cx, cy = float(state["center"][0]), float(state["center"][1])
    height = float(state["height"])
    acad = get_acad()
    acad.ZoomCenter(point(cx, cy), height)


def _view_metadata(doc) -> dict:
    """Collect the current viewport's spatial state as a plain dict."""
    center = tuple(doc.GetVariable("VIEWCTR"))
    height = float(doc.GetVariable("VIEWSIZE"))
    screen = tuple(doc.GetVariable("SCREENSIZE"))
    width = height * (screen[0] / screen[1]) if screen[1] != 0 else height
    return {
        "view_center_x": round(center[0], 1),
        "view_center_y": round(center[1], 1),
        "view_height": round(height, 1),
        "view_width": round(width, 1),
    }


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def register_screenshot_tools(mcp):

    @mcp.tool()
    def screenshot_current_view() -> list:
        """
        Capture a PNG screenshot of whatever is currently visible in the
        AutoCAD model-space viewport and return it so you can see the
        drawing.  No view changes are made — what you get is exactly what
        AutoCAD is showing right now.

        Returns the image plus a JSON string with view-center coordinates
        and dimensions (in drawing units, typically mm) so you know the
        spatial context of what you see.
        """
        doc = get_active_doc()
        meta = _view_metadata(doc)
        meta["capture_type"] = "current_view"

        png_bytes = _capture_viewport(doc)
        return [Image(data=png_bytes, format="png"), json.dumps(meta, indent=2)]

    @mcp.tool()
    def screenshot_extents() -> list:
        """
        Zoom to fit ALL objects in the drawing, capture a PNG screenshot,
        then restore the original view.

        Use this to get a full overview of the drawing contents — ideal for
        checking overall layout, verifying that all elements are in the right
        positions, or inspecting a plan you did not draw yourself.

        Returns the image plus a JSON string with view metadata.
        """
        doc = get_active_doc()
        if doc.ModelSpace.Count == 0:
            raise RuntimeError("Model space is empty — nothing to zoom to.")

        saved = _save_view(doc)
        try:
            acad = get_acad()
            acad.ZoomExtents()
            meta = _view_metadata(doc)
            meta["capture_type"] = "extents"
            png_bytes = _capture_viewport(doc)
        finally:
            _restore_view(doc, saved)

        return [Image(data=png_bytes, format="png"), json.dumps(meta, indent=2)]

    @mcp.tool()
    def screenshot_region(
        x1: float, y1: float,
        x2: float, y2: float,
        padding_pct: float = 10.0
    ) -> list:
        """
        Zoom to a specific rectangular region of the drawing, capture a PNG
        screenshot, then restore the original view.

        Use this to inspect a particular area in detail — e.g. a single room,
        a kitchen layout, a staircase, or any group of objects.

        x1, y1: lower-left corner of the region (drawing units, typically mm).
        x2, y2: upper-right corner of the region.
        padding_pct: extra whitespace added around the region as a percentage
                     of its size (default 10 %).  Prevents objects at the edge
                     from being clipped.

        Returns the image plus a JSON string with view metadata.
        """
        if x2 <= x1 or y2 <= y1:
            raise ValueError(
                f"Invalid region: x2 ({x2}) must be > x1 ({x1}) and "
                f"y2 ({y2}) must be > y1 ({y1})."
            )

        doc = get_active_doc()

        # Apply padding
        pad_x = (x2 - x1) * padding_pct / 100.0
        pad_y = (y2 - y1) * padding_pct / 100.0
        px1, py1 = x1 - pad_x, y1 - pad_y
        px2, py2 = x2 + pad_x, y2 + pad_y

        saved = _save_view(doc)
        try:
            acad = get_acad()
            acad.ZoomWindow(point(px1, py1), point(px2, py2))
            meta = _view_metadata(doc)
            meta["capture_type"] = "region"
            meta["region"] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            png_bytes = _capture_viewport(doc)
        finally:
            _restore_view(doc, saved)

        return [Image(data=png_bytes, format="png"), json.dumps(meta, indent=2)]
