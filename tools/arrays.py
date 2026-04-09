"""
tools/arrays.py
Tools for creating rectangular, polar, and path arrays in AutoCAD.
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_active_doc


def register_array_tools(mcp):

    @mcp.tool()
    def rectangular_array(
        handle: str,
        num_rows: int,
        num_cols: int,
        row_spacing: float,
        col_spacing: float,
        rotation_deg: float = 0.0
    ) -> dict:
        """
        Create a rectangular array of an entity.
        num_rows/num_cols: number of rows and columns (including original).
        row_spacing: distance between rows (can be negative to array downward).
        col_spacing: distance between columns (can be negative to array leftward).
        rotation_deg: rotate the entire array by this angle.
        Returns handles of all created copies.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        handles = []

        angle = math.radians(rotation_deg)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        for row in range(num_rows):
            for col in range(num_cols):
                if row == 0 and col == 0:
                    handles.append(handle)
                    continue
                dx_raw = col * col_spacing
                dy_raw = row * row_spacing
                dx = dx_raw * cos_a - dy_raw * sin_a
                dy = dx_raw * sin_a + dy_raw * cos_a

                copy = obj.Copy()
                origin = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0]
                )
                displacement = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8, [dx, dy, 0.0]
                )
                copy.Move(origin, displacement)
                handles.append(copy.Handle)

        total = num_rows * num_cols
        return {
            "total_objects": total,
            "rows": num_rows,
            "cols": num_cols,
            "handles": handles,
            "message": f"Rectangular array: {num_rows} rows × {num_cols} cols = {total} objects"
        }

    @mcp.tool()
    def polar_array(
        handle: str,
        center_x: float,
        center_y: float,
        num_items: int,
        total_angle_deg: float = 360.0,
        rotate_items: bool = True
    ) -> dict:
        """
        Create a polar (circular) array of an entity around a center point.
        num_items: total number of objects (including original).
        total_angle_deg: angular span of the array (360 = full circle).
        rotate_items: if True, each copy is also rotated to face the array direction.
        Returns handles of all created copies.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        handles = [handle]

        if num_items < 2:
            raise ValueError("num_items must be at least 2")

        step_angle = math.radians(total_angle_deg / num_items)

        for i in range(1, num_items):
            angle = step_angle * i
            copy = obj.Copy()

            if rotate_items:
                pivot = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8, [center_x, center_y, 0.0]
                )
                copy.Rotate(pivot, angle)
            else:
                # Move along the arc without rotating
                mn, mx = obj.GetBoundingBox()
                obj_cx = (mn[0] + mx[0]) / 2
                obj_cy = (mn[1] + mx[1]) / 2
                r = math.hypot(obj_cx - center_x, obj_cy - center_y)
                base_angle = math.atan2(obj_cy - center_y, obj_cx - center_x)
                new_angle = base_angle + angle
                dx = center_x + r * math.cos(new_angle) - obj_cx
                dy = center_y + r * math.sin(new_angle) - obj_cy
                origin = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0]
                )
                displacement = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8, [dx, dy, 0.0]
                )
                copy.Move(origin, displacement)

            handles.append(copy.Handle)

        return {
            "total_objects": num_items,
            "center": [center_x, center_y],
            "total_angle_deg": total_angle_deg,
            "step_angle_deg": math.degrees(step_angle),
            "handles": handles,
            "message": f"Polar array: {num_items} items over {total_angle_deg}°"
        }

    @mcp.tool()
    def path_array(
        handle: str,
        path_handle: str,
        num_items: int,
        align_to_path: bool = True,
        divide_evenly: bool = True
    ) -> dict:
        """
        Create a path array — distribute copies of an entity along a curve.
        handle: the entity to array.
        path_handle: the handle of the path curve (line, arc, polyline, spline, etc.).
        num_items: number of items to place along the path.
        align_to_path: rotate each item to align with the path tangent.
        divide_evenly: space items evenly; if False, uses measured distance.
        Returns handles of all created copies.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        path = doc.HandleToObject(path_handle)
        handles = [handle]

        # Get the total length of the path
        try:
            total_length = path.Length
        except Exception:
            try:
                total_length = path.Perimeter
            except Exception:
                raise ValueError("Path entity does not support length measurement")

        if num_items < 2:
            raise ValueError("num_items must be at least 2")

        spacing = total_length / (num_items - 1) if divide_evenly else total_length / num_items

        # Get the starting point for offset calculation
        try:
            mn, mx = obj.GetBoundingBox()
            obj_cx = (mn[0] + mx[0]) / 2
            obj_cy = (mn[1] + mx[1]) / 2
        except Exception:
            obj_cx, obj_cy = 0.0, 0.0

        for i in range(1, num_items):
            dist = spacing * i
            try:
                pt = path.GetPointAtDist(dist)
                dx = pt[0] - obj_cx
                dy = pt[1] - obj_cy

                copy = obj.Copy()
                origin = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0]
                )
                displacement = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8, [dx, dy, 0.0]
                )
                copy.Move(origin, displacement)

                if align_to_path:
                    # Get tangent direction at this point
                    try:
                        tangent = path.GetFirstDerivative(
                            path.GetParameterAtPoint(pt)
                        )
                        angle = math.atan2(tangent[1], tangent[0])
                        pivot = win32com.client.VARIANT(
                            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(pt[0]), float(pt[1]), 0.0]
                        )
                        copy.Rotate(pivot, angle)
                    except Exception:
                        pass  # tangent not available for all entity types

                handles.append(copy.Handle)
            except Exception as e:
                handles.append(f"error_at_{i}: {str(e)}")

        return {
            "total_objects": num_items,
            "path_length": total_length,
            "item_spacing": spacing,
            "handles": handles,
            "message": f"Path array: {num_items} items along path of length {total_length:.2f}"
        }

    @mcp.tool()
    def grid_array(
        handle: str,
        num_rows: int,
        num_cols: int,
        row_spacing: float,
        col_spacing: float,
        x_offset_per_row: float = 0.0
    ) -> dict:
        """
        Create a grid array with an optional staggered offset per row
        (useful for brick patterns, tile layouts, seating plans, etc.).
        x_offset_per_row: shifts every other row by this amount (e.g. half col_spacing for brick pattern).
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        handles = []

        for row in range(num_rows):
            stagger = x_offset_per_row if row % 2 != 0 else 0.0
            for col in range(num_cols):
                dx = col * col_spacing + stagger
                dy = row * row_spacing

                if row == 0 and col == 0:
                    handles.append(handle)
                    continue

                copy = obj.Copy()
                origin = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0]
                )
                displacement = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8, [dx, dy, 0.0]
                )
                copy.Move(origin, displacement)
                handles.append(copy.Handle)

        total = num_rows * num_cols
        return {
            "total_objects": total,
            "rows": num_rows,
            "cols": num_cols,
            "stagger": x_offset_per_row,
            "handles": handles,
            "message": f"Grid array: {total} objects ({num_rows}×{num_cols})"
                       + (f" with {x_offset_per_row} stagger offset" if x_offset_per_row else "")
        }
