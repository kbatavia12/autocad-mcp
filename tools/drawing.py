"""
tools/drawing.py
Tools for creating geometry in AutoCAD model space.
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_model_space, get_active_doc, point


def register_drawing_tools(mcp):

    @mcp.tool()
    def draw_line(x1: float, y1: float, x2: float, y2: float, layer: str = "") -> str:
        """Draw a straight line between two points in model space."""
        space = get_model_space()
        line = space.AddLine(point(x1, y1), point(x2, y2))
        if layer:
            line.Layer = layer
        return f"Line drawn from ({x1}, {y1}) to ({x2}, {y2})"

    @mcp.tool()
    def draw_circle(cx: float, cy: float, radius: float, layer: str = "") -> str:
        """Draw a circle given a center point and radius."""
        space = get_model_space()
        circle = space.AddCircle(point(cx, cy), float(radius))
        if layer:
            circle.Layer = layer
        return f"Circle drawn at ({cx}, {cy}) with radius {radius}"

    @mcp.tool()
    def draw_arc(
        cx: float, cy: float, radius: float,
        start_angle_deg: float, end_angle_deg: float,
        layer: str = ""
    ) -> str:
        """Draw an arc. Angles are in degrees, measured counter-clockwise from the X axis."""
        space = get_model_space()
        arc = space.AddArc(
            point(cx, cy),
            float(radius),
            math.radians(start_angle_deg),
            math.radians(end_angle_deg),
        )
        if layer:
            arc.Layer = layer
        return f"Arc drawn at ({cx}, {cy}), r={radius}, {start_angle_deg}° to {end_angle_deg}°"

    @mcp.tool()
    def draw_rectangle(
        x1: float, y1: float, x2: float, y2: float, layer: str = ""
    ) -> str:
        """Draw an axis-aligned rectangle defined by two corner points."""
        space = get_model_space()
        pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x1, y1, x2, y1, x2, y2, x1, y2, x1, y1],
        )
        pline = space.AddLightWeightPolyline(pts)
        pline.Closed = True
        if layer:
            pline.Layer = layer
        return f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"

    @mcp.tool()
    def draw_polyline(
        points_flat: list[float], closed: bool = False, layer: str = ""
    ) -> str:
        """
        Draw a polyline from a flat list of XY coordinates [x1,y1, x2,y2, ...].
        Set closed=True to close the polyline back to the first point.
        """
        if len(points_flat) < 4 or len(points_flat) % 2 != 0:
            raise ValueError("points_flat must be an even list of at least 4 values (x1,y1,x2,y2,...)")
        pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in points_flat]
        )
        space = get_model_space()
        pline = space.AddLightWeightPolyline(pts)
        pline.Closed = closed
        if layer:
            pline.Layer = layer
        n = len(points_flat) // 2
        return f"Polyline with {n} vertices drawn (closed={closed})"

    @mcp.tool()
    def draw_text(
        x: float, y: float, text: str,
        height: float = 2.5, rotation_deg: float = 0.0, layer: str = ""
    ) -> str:
        """Add single-line text to model space at a given position."""
        space = get_model_space()
        txt = space.AddText(text, point(x, y), float(height))
        txt.Rotation = math.radians(rotation_deg)
        if layer:
            txt.Layer = layer
        return f"Text '{text}' placed at ({x}, {y})"

    @mcp.tool()
    def draw_mtext(
        x: float, y: float, text: str,
        width: float = 100.0, height: float = 2.5, layer: str = ""
    ) -> str:
        """Add multi-line text (MText) to model space at a given position."""
        space = get_model_space()
        mtext = space.AddMText(point(x, y), float(width), text)
        mtext.Height = float(height)
        if layer:
            mtext.Layer = layer
        return f"MText placed at ({x}, {y})"

    @mcp.tool()
    def draw_ellipse(
        cx: float, cy: float,
        major_x: float, major_y: float,
        ratio: float, layer: str = ""
    ) -> str:
        """
        Draw an ellipse. The major axis vector (major_x, major_y) defines
        the direction and half-length of the major axis. ratio is minor/major (0 < ratio <= 1).
        """
        space = get_model_space()
        major_axis = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(major_x), float(major_y), 0.0]
        )
        ellipse = space.AddEllipse(point(cx, cy), major_axis, float(ratio))
        if layer:
            ellipse.Layer = layer
        return f"Ellipse drawn at ({cx}, {cy}), major=({major_x},{major_y}), ratio={ratio}"

    @mcp.tool()
    def draw_spline(points_flat: list[float], layer: str = "") -> str:
        """
        Draw a spline through fit points. points_flat is a flat list of XYZ coordinates
        [x1,y1,z1, x2,y2,z2, ...]. Minimum 3 points.
        """
        if len(points_flat) < 9 or len(points_flat) % 3 != 0:
            raise ValueError("points_flat must be a multiple of 3 with at least 9 values (x,y,z per point)")
        pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in points_flat]
        )
        start_tan = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0])
        end_tan = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0])
        space = get_model_space()
        spline = space.AddSpline(pts, start_tan, end_tan)
        if layer:
            spline.Layer = layer
        n = len(points_flat) // 3
        return f"Spline with {n} fit points drawn"

    @mcp.tool()
    def draw_hatch(
        boundary_x1: float, boundary_y1: float,
        boundary_x2: float, boundary_y2: float,
        pattern: str = "ANSI31", scale: float = 1.0, layer: str = ""
    ) -> str:
        """
        Draw a hatch inside a rectangular boundary using the given pattern name
        (e.g. ANSI31, ANSI32, SOLID, CROSS). Scale adjusts pattern spacing.
        """
        doc = get_active_doc()
        space = doc.ModelSpace

        # Create a bounding rectangle first
        pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [boundary_x1, boundary_y1,
             boundary_x2, boundary_y1,
             boundary_x2, boundary_y2,
             boundary_x1, boundary_y2,
             boundary_x1, boundary_y1],
        )
        pline = space.AddLightWeightPolyline(pts)
        pline.Closed = True
        if layer:
            pline.Layer = layer

        # Create hatch
        hatch = space.AddHatch(0, pattern, True)  # 0 = AcHatchPatternTypePreDefined
        outer_loop = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [pline]
        )
        hatch.AppendOuterLoop(outer_loop)
        hatch.PatternScale = float(scale)
        hatch.Evaluate()
        if layer:
            hatch.Layer = layer
        doc.Regen(1)  # acActiveViewport
        return f"Hatch '{pattern}' applied inside ({boundary_x1},{boundary_y1}) to ({boundary_x2},{boundary_y2})"
