"""
tools/drawing.py
Tools for creating geometry in AutoCAD model space.

Each _do_* function contains the core logic and returns a result dict.
Registered MCP tools are thin wrappers that call the _do_* functions.
All _do_* functions are batchable via batch_execute in objects.py.
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_model_space, get_active_doc, ensure_layer, point


def _make_variant(values):
    return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in values])


# ---------------------------------------------------------------------------
# Core _do_* functions — batchable, self-contained
# ---------------------------------------------------------------------------

def _do_draw_line(x1: float, y1: float, x2: float, y2: float, layer: str = "") -> dict:
    doc = get_active_doc()
    space = get_model_space()
    if layer:
        ensure_layer(doc, layer)
    line = space.AddLine(point(x1, y1), point(x2, y2))
    if layer:
        line.Layer = layer
    return {"status": "ok", "handle": line.Handle,
            "message": f"Line from ({x1},{y1}) to ({x2},{y2})"}


def _do_draw_circle(cx: float, cy: float, radius: float, layer: str = "") -> dict:
    doc = get_active_doc()
    space = get_model_space()
    if layer:
        ensure_layer(doc, layer)
    circle = space.AddCircle(point(cx, cy), float(radius))
    if layer:
        circle.Layer = layer
    return {"status": "ok", "handle": circle.Handle,
            "message": f"Circle at ({cx},{cy}) r={radius}"}


def _do_draw_arc(
    cx: float, cy: float, radius: float,
    start_angle_deg: float, end_angle_deg: float,
    layer: str = ""
) -> dict:
    doc = get_active_doc()
    space = get_model_space()
    if layer:
        ensure_layer(doc, layer)
    arc = space.AddArc(
        point(cx, cy), float(radius),
        math.radians(start_angle_deg), math.radians(end_angle_deg),
    )
    if layer:
        arc.Layer = layer
    return {"status": "ok", "handle": arc.Handle,
            "message": f"Arc at ({cx},{cy}) r={radius} {start_angle_deg}°–{end_angle_deg}°"}


def _do_draw_rectangle(x1: float, y1: float, x2: float, y2: float, layer: str = "") -> dict:
    doc = get_active_doc()
    space = get_model_space()
    if layer:
        ensure_layer(doc, layer)
    pts = _make_variant([x1, y1, x2, y1, x2, y2, x1, y2, x1, y1])
    pline = space.AddLightWeightPolyline(pts)
    pline.Closed = True
    if layer:
        pline.Layer = layer
    return {"status": "ok", "handle": pline.Handle,
            "message": f"Rectangle ({x1},{y1}) to ({x2},{y2})"}


def _do_draw_polyline(points_flat: list, closed: bool = False, layer: str = "") -> dict:
    if len(points_flat) < 4 or len(points_flat) % 2 != 0:
        raise ValueError("points_flat must be an even list of at least 4 values (x1,y1,x2,y2,...)")
    doc = get_active_doc()
    space = get_model_space()
    if layer:
        ensure_layer(doc, layer)
    pts = _make_variant([float(v) for v in points_flat])
    pline = space.AddLightWeightPolyline(pts)
    pline.Closed = closed
    if layer:
        pline.Layer = layer
    n = len(points_flat) // 2
    return {"status": "ok", "handle": pline.Handle,
            "message": f"Polyline {n} vertices (closed={closed})"}


def _do_draw_text(
    x: float, y: float, text: str,
    height: float = 2.5, rotation_deg: float = 0.0, layer: str = ""
) -> dict:
    doc = get_active_doc()
    space = get_model_space()
    if layer:
        ensure_layer(doc, layer)
    txt = space.AddText(text, point(x, y), float(height))
    txt.Rotation = math.radians(rotation_deg)
    if layer:
        txt.Layer = layer
    return {"status": "ok", "handle": txt.Handle,
            "message": f"Text '{text}' at ({x},{y})"}


def _do_draw_mtext(
    x: float, y: float, text: str,
    width: float = 100.0, height: float = 2.5, layer: str = ""
) -> dict:
    doc = get_active_doc()
    space = get_model_space()
    if layer:
        ensure_layer(doc, layer)
    mtext = space.AddMText(point(x, y), float(width), text)
    mtext.Height = float(height)
    if layer:
        mtext.Layer = layer
    return {"status": "ok", "handle": mtext.Handle,
            "message": f"MText at ({x},{y})"}


def _do_draw_ellipse(
    cx: float, cy: float,
    major_x: float, major_y: float,
    ratio: float, layer: str = ""
) -> dict:
    doc = get_active_doc()
    space = get_model_space()
    if layer:
        ensure_layer(doc, layer)
    major_axis = win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(major_x), float(major_y), 0.0]
    )
    ellipse = space.AddEllipse(point(cx, cy), major_axis, float(ratio))
    if layer:
        ellipse.Layer = layer
    return {"status": "ok", "handle": ellipse.Handle,
            "message": f"Ellipse at ({cx},{cy}) major=({major_x},{major_y}) ratio={ratio}"}


def _do_draw_spline(points_flat: list, layer: str = "") -> dict:
    if len(points_flat) < 9 or len(points_flat) % 3 != 0:
        raise ValueError("points_flat must be a multiple of 3 with at least 9 values (x,y,z per point)")
    doc = get_active_doc()
    space = get_model_space()
    if layer:
        ensure_layer(doc, layer)
    pts = win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in points_flat]
    )
    start_tan = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0])
    end_tan   = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0])
    spline = space.AddSpline(pts, start_tan, end_tan)
    if layer:
        spline.Layer = layer
    n = len(points_flat) // 3
    return {"status": "ok", "handle": spline.Handle,
            "message": f"Spline with {n} fit points"}


def _do_draw_hatch(
    boundary_x1: float, boundary_y1: float,
    boundary_x2: float, boundary_y2: float,
    pattern: str = "ANSI31", scale: float = 1.0, layer: str = ""
) -> dict:
    doc = get_active_doc()
    space = get_model_space()
    if layer:
        ensure_layer(doc, layer)
    pts = _make_variant([
        boundary_x1, boundary_y1,
        boundary_x2, boundary_y1,
        boundary_x2, boundary_y2,
        boundary_x1, boundary_y2,
        boundary_x1, boundary_y1,
    ])
    pline = space.AddLightWeightPolyline(pts)
    pline.Closed = True
    if layer:
        pline.Layer = layer
    hatch = space.AddHatch(0, pattern, True)
    outer_loop = win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [pline]
    )
    hatch.AppendOuterLoop(outer_loop)
    hatch.PatternScale = float(scale)
    hatch.Evaluate()
    if layer:
        hatch.Layer = layer
    doc.Regen(1)
    return {
        "status": "ok",
        "boundary_handle": pline.Handle,
        "hatch_handle": hatch.Handle,
        "message": f"Hatch '{pattern}' in ({boundary_x1},{boundary_y1})–({boundary_x2},{boundary_y2})",
    }


# ---------------------------------------------------------------------------
# MCP tool registration — thin wrappers only
# ---------------------------------------------------------------------------

def register_drawing_tools(mcp):

    @mcp.tool()
    def draw_line(x1: float, y1: float, x2: float, y2: float, layer: str = "") -> dict:
        """Draw a straight line between two points in model space."""
        return _do_draw_line(x1, y1, x2, y2, layer)

    @mcp.tool()
    def draw_circle(cx: float, cy: float, radius: float, layer: str = "") -> dict:
        """Draw a circle given a center point and radius."""
        return _do_draw_circle(cx, cy, radius, layer)

    @mcp.tool()
    def draw_arc(
        cx: float, cy: float, radius: float,
        start_angle_deg: float, end_angle_deg: float,
        layer: str = ""
    ) -> dict:
        """Draw an arc. Angles are in degrees, measured counter-clockwise from the X axis."""
        return _do_draw_arc(cx, cy, radius, start_angle_deg, end_angle_deg, layer)

    @mcp.tool()
    def draw_rectangle(x1: float, y1: float, x2: float, y2: float, layer: str = "") -> dict:
        """Draw an axis-aligned rectangle defined by two corner points."""
        return _do_draw_rectangle(x1, y1, x2, y2, layer)

    @mcp.tool()
    def draw_polyline(points_flat: list[float], closed: bool = False, layer: str = "") -> dict:
        """
        Draw a polyline from a flat list of XY coordinates [x1,y1, x2,y2, ...].
        Set closed=True to close the polyline back to the first point.
        """
        return _do_draw_polyline(points_flat, closed, layer)

    @mcp.tool()
    def draw_text(
        x: float, y: float, text: str,
        height: float = 2.5, rotation_deg: float = 0.0, layer: str = ""
    ) -> dict:
        """Add single-line text to model space at a given position."""
        return _do_draw_text(x, y, text, height, rotation_deg, layer)

    @mcp.tool()
    def draw_mtext(
        x: float, y: float, text: str,
        width: float = 100.0, height: float = 2.5, layer: str = ""
    ) -> dict:
        """Add multi-line text (MText) to model space at a given position."""
        return _do_draw_mtext(x, y, text, width, height, layer)

    @mcp.tool()
    def draw_ellipse(
        cx: float, cy: float,
        major_x: float, major_y: float,
        ratio: float, layer: str = ""
    ) -> dict:
        """
        Draw an ellipse. The major axis vector (major_x, major_y) defines
        the direction and half-length of the major axis. ratio is minor/major (0 < ratio <= 1).
        """
        return _do_draw_ellipse(cx, cy, major_x, major_y, ratio, layer)

    @mcp.tool()
    def draw_spline(points_flat: list[float], layer: str = "") -> dict:
        """
        Draw a spline through fit points. points_flat is a flat list of XYZ coordinates
        [x1,y1,z1, x2,y2,z2, ...]. Minimum 3 points.
        """
        return _do_draw_spline(points_flat, layer)

    @mcp.tool()
    def draw_hatch(
        boundary_x1: float, boundary_y1: float,
        boundary_x2: float, boundary_y2: float,
        pattern: str = "ANSI31", scale: float = 1.0, layer: str = ""
    ) -> dict:
        """
        Draw a hatch inside a rectangular boundary using the given pattern name
        (e.g. ANSI31, ANSI32, SOLID, CROSS). Scale adjusts pattern spacing.
        """
        return _do_draw_hatch(boundary_x1, boundary_y1, boundary_x2, boundary_y2,
                              pattern, scale, layer)
