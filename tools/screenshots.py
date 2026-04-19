"""
tools/screenshots.py
Screenshot tools — capture the current AutoCAD viewport and return the image
to Claude so it can see and reason about the current drawing state.

All screenshot tools accept annotate=True (default). When enabled, a temporary
layer _ANNOT-TEMP is created, MText labels are drawn directly in model space
at world coordinates, the screenshot is taken, and the layer is deleted in a
try/finally block — so the drawing is never left in a dirty state.

Label strategy:
  Block references  — block name at insertion point (+ attribute TYPE if present)
  LwPolylines       — each segment's length at its midpoint, offset from the line
  Dimensions        — skipped (already carry their own text)
  Text/MText        — skipped
  Everything else   — entity handle at bbox centre (for follow-up querying)
"""

import json
import math
import os
import tempfile
import time

from mcp.server.fastmcp import Image

from autocad_helpers import get_acad, get_active_doc, point, wait_for_idle


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ANNOT_LAYER = "_ANNOT-TEMP"


# ---------------------------------------------------------------------------
# Viewport capture
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

    try:
        wait_for_idle(doc)
        lisp = (
            '(progn'
            ' (setvar "FILEDIA" 0)'
            f' (command "_.PNGOUT" "{file_path_acad}")'
            ' (while (> (getvar "CMDACTIVE") 0) (command ""))'
            ' (setvar "FILEDIA" 1)'
            ' (princ))'
            '\n'
        )
        doc.SendCommand(lisp)
        if not _wait_for_file(file_path, timeout):
            raise RuntimeError(
                f"Screenshot timed out after {timeout}s — "
                "AutoCAD may be busy or PNGOUT is not available in this version."
            )
        with open(file_path, "rb") as fh:
            return fh.read()
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rmdir(temp_dir)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# View state
# ---------------------------------------------------------------------------

def _save_view(doc) -> dict:
    """Return a snapshot of the active viewport's center and height."""
    center = tuple(doc.GetVariable("VIEWCTR"))
    height = float(doc.GetVariable("VIEWSIZE"))
    return {"center": center, "height": height}


def _restore_view(doc, state: dict) -> None:
    """Restore a viewport snapshot saved with _save_view()."""
    cx, cy = float(state["center"][0]), float(state["center"][1])
    height = float(state["height"])
    get_acad().ZoomCenter(point(cx, cy), height)


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


def _drawing_extents(doc):
    """Return (x1, y1, x2, y2) world bbox of all entities, or None if empty."""
    space = doc.ModelSpace
    if space.Count == 0:
        return None
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
    if min_x == float("inf"):
        return None
    return min_x, min_y, max_x, max_y


# ---------------------------------------------------------------------------
# Entity list helper (used by screenshot_with_context)
# ---------------------------------------------------------------------------

def _entities_in_region(doc, x1, y1, x2, y2):
    """Return a lightweight entity list for all objects overlapping the region."""
    space = doc.ModelSpace
    result = []
    for i in range(space.Count):
        obj = space.Item(i)
        if obj.Layer == ANNOT_LAYER:
            continue
        try:
            mn, mx = obj.GetBoundingBox()
            if mx[0] >= x1 and mn[0] <= x2 and mx[1] >= y1 and mn[1] <= y2:
                result.append({
                    "handle": obj.Handle,
                    "type": obj.ObjectName,
                    "layer": obj.Layer,
                    "center_x": round((mn[0] + mx[0]) / 2, 2),
                    "center_y": round((mn[1] + mx[1]) / 2, 2),
                    "width": round(mx[0] - mn[0], 2),
                    "height": round(mx[1] - mn[1], 2),
                })
        except Exception:
            pass
    return result


# ---------------------------------------------------------------------------
# Annotation layer
# ---------------------------------------------------------------------------

def _ensure_annot_layer(doc):
    """Create _ANNOT-TEMP if it doesn't already exist."""
    try:
        doc.Layers.Item(ANNOT_LAYER)
    except Exception:
        layer = doc.Layers.Add(ANNOT_LAYER)
        layer.color = 3  # green — visually distinct, easy to spot if cleanup fails


def _cleanup_annot_layer(doc, handles: list) -> None:
    """
    Delete all annotation entities by handle, then delete the layer.
    Runs as a best-effort sweep: if handle deletion fails for any entity
    (e.g. already gone), a second pass sweeps model space by layer name
    before attempting to delete the layer itself.
    """
    # Pass 1 — delete by collected handles
    for handle in handles:
        try:
            doc.HandleToObject(handle).Delete()
        except Exception:
            pass

    # Pass 2 — safety sweep in case any entity slipped through
    space = doc.ModelSpace
    to_delete = []
    for i in range(space.Count):
        try:
            obj = space.Item(i)
            if obj.Layer == ANNOT_LAYER:
                to_delete.append(obj)
        except Exception:
            pass
    for obj in to_delete:
        try:
            obj.Delete()
        except Exception:
            pass

    # Delete the layer (only succeeds if empty)
    try:
        doc.Layers.Item(ANNOT_LAYER).Delete()
    except Exception:
        pass


def _add_mtext(space, x, y, text, height, attachment=7) -> object:
    """
    Add an MText entity and set its attachment point.
    Attachment points (AutoCAD convention):
      1=top-left  2=top-centre  3=top-right
      4=mid-left  5=mid-centre  6=mid-right
      7=bot-left  8=bot-centre  9=bot-right
    Default 7 (bottom-left) means the insertion point sits at the
    lower-left corner of the text — natural for labelling a point.
    """
    mt = space.AddMText(point(x, y), 0, text)
    mt.Height = height
    try:
        mt.AttachmentPoint = attachment
    except Exception:
        pass
    return mt


def _draw_bbox_lines(space, mn, mx) -> list:
    """
    Draw the four sides of a bounding box as lines on the current layer.
    Returns the four line objects.
    """
    corners = [
        (point(mn[0], mn[1]), point(mx[0], mn[1])),  # bottom
        (point(mx[0], mn[1]), point(mx[0], mx[1])),  # right
        (point(mx[0], mx[1]), point(mn[0], mx[1])),  # top
        (point(mn[0], mx[1]), point(mn[0], mn[1])),  # left
    ]
    lines = []
    for p1, p2 in corners:
        lines.append(space.AddLine(p1, p2))
    return lines


def _draw_annotations(doc, x1: float, y1: float, x2: float, y2: float) -> list:
    """
    Write annotation entities on _ANNOT-TEMP for every entity in the region.

    Block references get:
      - A bbox rectangle (4 lines) showing the physical envelope
      - Block name (+ TYPE attribute) centred inside the bbox
      - Bottom-left corner coordinate (x_min, y_min) at the bbox corner
      - Top-right corner coordinate (x_max, y_max) at the bbox corner
    Together these let the agent read exact edge positions directly from the
    image without any arithmetic — right edge = x_max, left edge = x_min, etc.

    LwPolylines (walls, counters) get:
      - Segment length at each segment midpoint, offset from the line
      - Vertex coordinate (x, y) at each corner vertex

    Dimensions, text, and MText are skipped — they carry their own content.
    All other entity types get their handle at bbox centre for follow-up querying.

    Text height is ~2 % of viewport height so labels are readable at any scale.
    Returns a list of created entity handles for cleanup.
    """
    _ensure_annot_layer(doc)
    space = doc.ModelSpace
    handles = []
    text_height = (y2 - y1) / 50.0
    coord_height = text_height * 0.6   # smaller text for coordinate labels
    small_height  = text_height * 0.55  # smallest text for vertex coords on walls

    for i in range(space.Count):
        obj = space.Item(i)
        if obj.Layer == ANNOT_LAYER:
            continue
        try:
            mn, mx = obj.GetBoundingBox()
            if not (mx[0] >= x1 and mn[0] <= x2 and mx[1] >= y1 and mn[1] <= y2):
                continue
        except Exception:
            continue

        t = obj.ObjectName

        try:
            if t == "AcDbBlockReference":
                # --- bbox rectangle ---
                for line in _draw_bbox_lines(space, mn, mx):
                    line.Layer = ANNOT_LAYER
                    handles.append(line.Handle)

                # --- block name at bbox centre ---
                cx = (mn[0] + mx[0]) / 2
                cy = (mn[1] + mx[1]) / 2
                label = obj.Name
                try:
                    attrs = obj.GetAttributes()
                    for a in attrs:
                        if a.TagString.upper() in ("TYPE", "ITEM", "NAME"):
                            label = f"{obj.Name}\\P{a.TextString}"
                            break
                except Exception:
                    pass
                mt = _add_mtext(space, cx, cy, label, text_height, attachment=5)
                mt.Layer = ANNOT_LAYER
                handles.append(mt.Handle)

                # --- bottom-left corner coordinate ---
                # attachment=7 (bottom-left): text grows right and up from (x_min, y_min)
                bl = _add_mtext(
                    space, mn[0], mn[1],
                    f"({round(mn[0])}, {round(mn[1])})",
                    coord_height, attachment=7,
                )
                bl.Layer = ANNOT_LAYER
                handles.append(bl.Handle)

                # --- top-right corner coordinate ---
                # attachment=3 (top-right): text grows left and down from (x_max, y_max)
                tr = _add_mtext(
                    space, mx[0], mx[1],
                    f"({round(mx[0])}, {round(mx[1])})",
                    coord_height, attachment=3,
                )
                tr.Layer = ANNOT_LAYER
                handles.append(tr.Handle)

            elif t == "AcDbLwPolyline":
                coords = list(obj.Coordinates)
                n = obj.NumberOfVertices
                vertices = [(coords[j * 2], coords[j * 2 + 1]) for j in range(n)]
                closed_verts = vertices + [vertices[0]] if obj.Closed else vertices

                # --- segment lengths ---
                for j in range(len(closed_verts) - 1):
                    v1, v2 = closed_verts[j], closed_verts[j + 1]
                    dx = v2[0] - v1[0]
                    dy = v2[1] - v1[1]
                    seg_len = math.hypot(dx, dy)
                    if seg_len < text_height * 3:
                        continue
                    mid_x = (v1[0] + v2[0]) / 2
                    mid_y = (v1[1] + v2[1]) / 2
                    perp_x = (-dy / seg_len) * text_height * 1.5
                    perp_y = (dx / seg_len) * text_height * 1.5
                    mt = _add_mtext(
                        space, mid_x + perp_x, mid_y + perp_y,
                        str(round(seg_len)), text_height * 0.8,
                    )
                    mt.Layer = ANNOT_LAYER
                    handles.append(mt.Handle)

                # --- vertex coordinates ---
                for vx, vy in vertices:  # original list, no repeated closing vertex
                    vt = _add_mtext(
                        space, vx, vy,
                        f"({round(vx)},{round(vy)})",
                        small_height, attachment=7,
                    )
                    vt.Layer = ANNOT_LAYER
                    handles.append(vt.Handle)

            elif t in ("AcDbText", "AcDbMText"):
                pass  # already carry their own content

            elif t.startswith("AcDbDim"):
                pass  # AutoCAD renders dimension text natively — no annotation needed

            else:
                cx = (mn[0] + mx[0]) / 2
                cy = (mn[1] + mx[1]) / 2
                mt = _add_mtext(space, cx, cy, obj.Handle, text_height * 0.6, attachment=5)
                mt.Layer = ANNOT_LAYER
                handles.append(mt.Handle)

        except Exception:
            pass

    return handles


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def register_screenshot_tools(mcp):

    @mcp.tool()
    def screenshot_current_view(annotate: bool = True) -> list:
        """
        Capture a PNG screenshot of whatever is currently visible in the
        AutoCAD model-space viewport. No zoom or view change is made — what
        you get is exactly what AutoCAD is showing right now.

        WHEN TO USE
        Use this after executing drawing operations to verify the result at
        the current zoom level. Also useful mid-task when you have already
        zoomed to the right area and just need a fresh look without
        repositioning the view.

        Do NOT use this for initial orientation — the viewport may be zoomed
        into an arbitrary area that tells you nothing about the overall drawing.
        Use screenshot_extents for orientation and screenshot_region or
        screenshot_with_context when you know which area to inspect.

        ANNOTATIONS (annotate=True, default)
        Before the screenshot, labels are written as MText entities on a
        temporary layer (_ANNOT-TEMP) directly in model space at world
        coordinates, so they scale correctly with the drawing:
          - Block references: block name at the insertion point. If the block
            carries a TYPE attribute, it appears on a second line beneath the
            name (e.g. "CHAIR-DINING / ARMCHAIR"). This lets you identify
            furniture without cross-referencing the entity list.
          - LwPolylines: the length of each segment in drawing units, placed
            at the segment midpoint and offset perpendicular to the line so
            the number does not overlap the geometry. Wall lengths, counter
            runs, and partition spans are immediately readable.
          - Dimensions, text, and MText: skipped — they already carry their
            own readable content.
          - All other entity types: the entity handle in small text at the
            bbox centre. Use this handle to call get_entity_by_handle or
            identify_entity for further inspection.
        The annotation layer and all its entities are deleted in a try/finally
        block immediately after the screenshot — the drawing is always left
        clean regardless of whether the capture succeeds or fails.

        Pass annotate=False when you want a raw uncluttered view — for
        example, when verifying the visual result of a drawing operation
        before presenting it to the user, or when the annotation labels would
        obscure the detail you are trying to inspect at close zoom.

        RETURNS
        [Image (PNG), JSON string] — the image and a metadata dict containing
        view_center_x, view_center_y, view_width, view_height in drawing units.
        """
        doc = get_active_doc()
        meta = _view_metadata(doc)
        meta["capture_type"] = "current_view"

        annot_handles = []
        if annotate:
            hw = meta["view_width"] / 2
            hh = meta["view_height"] / 2
            cx, cy = meta["view_center_x"], meta["view_center_y"]
            annot_handles = _draw_annotations(doc, cx - hw, cy - hh, cx + hw, cy + hh)

        try:
            png_bytes = _capture_viewport(doc)
        finally:
            if annotate:
                _cleanup_annot_layer(doc, annot_handles)

        return [Image(data=png_bytes, format="png"), json.dumps(meta, indent=2)]

    @mcp.tool()
    def screenshot_extents(annotate: bool = True) -> list:
        """
        Zoom to fit ALL objects in the drawing, capture a PNG screenshot,
        then restore the original view.

        WHEN TO USE
        Use this at the very start of any task to orient yourself before
        proposing or executing anything. It gives you the full drawing in one
        shot — room boundaries, existing furniture, dimensions, annotations —
        without needing to know coordinates in advance. Also use it after a
        major operation (placing a furniture group, laying out a whole room)
        to confirm the overall result looks correct before moving on.

        Do NOT use this for detailed inspection of a specific area — at full
        extents, small elements like text labels and furniture detail are
        unreadable. Use screenshot_region or screenshot_with_context to zoom
        into the area you need to examine.

        ANNOTATIONS (annotate=True, default)
        Labels cover the entire drawing extent. At full zoom, text height is
        derived from the total drawing height so labels remain legible
        regardless of drawing scale. The same label rules apply as
        screenshot_current_view:
          - Block references: name (+ TYPE attribute) at insertion point.
          - LwPolylines: segment lengths at midpoints, offset from the line.
          - Dimensions/text: skipped.
          - Other entities: handle at bbox centre.
        On a large drawing with many entities, annotations at extents can be
        dense. If the overview is too cluttered to read, call this tool with
        annotate=False to get the raw plan, then use screenshot_with_context
        on the specific region you want annotated detail on.

        The original view is restored after the screenshot regardless of
        whether the capture succeeds, and the annotation layer is cleaned up
        in the same try/finally block.

        RETURNS
        [Image (PNG), JSON string] — the image and a metadata dict containing
        view_center_x, view_center_y, view_width, view_height in drawing units.
        """
        doc = get_active_doc()
        wait_for_idle(doc)
        if doc.ModelSpace.Count == 0:
            raise RuntimeError("Model space is empty — nothing to zoom to.")

        extents = _drawing_extents(doc)
        annot_handles = []
        if annotate and extents:
            annot_handles = _draw_annotations(doc, *extents)

        saved = _save_view(doc)
        try:
            get_acad().ZoomExtents()
            meta = _view_metadata(doc)
            meta["capture_type"] = "extents"
            png_bytes = _capture_viewport(doc)
        finally:
            _restore_view(doc, saved)
            if annotate:
                _cleanup_annot_layer(doc, annot_handles)

        return [Image(data=png_bytes, format="png"), json.dumps(meta, indent=2)]

    @mcp.tool()
    def screenshot_region(
        x1: float, y1: float,
        x2: float, y2: float,
        padding_pct: float = 10.0,
        annotate: bool = True,
    ) -> list:
        """
        Zoom to a specific rectangular region of the drawing, capture a PNG
        screenshot, then restore the original view.

        WHEN TO USE
        Use this when you know the area you want to inspect and need only
        the visual — you already have the entity data from a previous call
        (e.g. get_room_summary or find_entities_in_region) and just want
        to see what it looks like. Also use it to verify a specific area
        after making changes without needing the entity list again.

        If you need both the visual and structured entity data for an area
        you haven't inspected yet, use screenshot_with_context instead —
        it returns both in one call and saves a round trip.

        COORDINATES
        x1, y1: lower-left corner of the region in drawing units (mm).
        x2, y2: upper-right corner of the region in drawing units (mm).
        Coordinates are in model space world units — the same coordinate
        system used by all other tools. Use get_drawing_extents or
        get_room_summary to find the coordinates of an area before calling
        this if you don't know them.

        padding_pct (default 10): extra whitespace added around all four
        sides of the region as a percentage of its size. Prevents objects
        at the edges from being clipped by the viewport. Increase to 20–30
        when inspecting areas near the edge of the drawing or when you want
        more spatial context around a tight group of elements.

        ANNOTATIONS (annotate=True, default)
        Labels cover only the entities within the specified region. Text
        height is derived from the region height — at room scale (3–6 m),
        labels are large enough to read without being overwhelming.
          - Block references: name (+ TYPE attribute) at insertion point.
          - LwPolylines: segment lengths at midpoints, offset from the line.
          - Dimensions/text: skipped.
          - Other entities: handle at bbox centre.
        Pass annotate=False when checking a finished drawing for presentation
        or when label density would obscure fine detail at close zoom.

        The original view is restored and the annotation layer is cleaned up
        in a try/finally block after the capture.

        RETURNS
        [Image (PNG), JSON string] — the image and a metadata dict containing
        view_center_x, view_center_y, view_width, view_height, and the
        region bounds (x1, y1, x2, y2) in drawing units.
        """
        if x2 <= x1 or y2 <= y1:
            raise ValueError(
                f"Invalid region: x2 ({x2}) must be > x1 ({x1}) and "
                f"y2 ({y2}) must be > y1 ({y1})."
            )

        doc = get_active_doc()
        wait_for_idle(doc)

        annot_handles = []
        if annotate:
            annot_handles = _draw_annotations(doc, x1, y1, x2, y2)

        pad_x = (x2 - x1) * padding_pct / 100.0
        pad_y = (y2 - y1) * padding_pct / 100.0
        px1, py1 = x1 - pad_x, y1 - pad_y
        px2, py2 = x2 + pad_x, y2 + pad_y

        saved = _save_view(doc)
        try:
            get_acad().ZoomWindow(point(px1, py1), point(px2, py2))
            meta = _view_metadata(doc)
            meta["capture_type"] = "region"
            meta["region"] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            png_bytes = _capture_viewport(doc)
        finally:
            _restore_view(doc, saved)
            if annotate:
                _cleanup_annot_layer(doc, annot_handles)

        return [Image(data=png_bytes, format="png"), json.dumps(meta, indent=2)]

    @mcp.tool()
    def screenshot_with_context(
        x1: float, y1: float,
        x2: float, y2: float,
        padding_pct: float = 10.0,
        annotate: bool = True,
    ) -> list:
        """
        Zoom to a region, capture an annotated PNG screenshot, AND return a
        structured entity list for that region — all in a single call.

        WHEN TO USE
        This is the primary inspection tool. Use it whenever you need to
        understand an area you have not seen yet: at the start of a task
        when reading an existing room, before proposing furniture placement,
        after completing a furniture group to verify position and clearances,
        or any time you need to know both what is in an area and what it
        looks like.

        Prefer this over separate screenshot_region + find_entities_in_region
        + identify_entities calls — those three round trips are replaced by
        one call here.

        Use screenshot_region (without context) only when you already have
        the entity data and just want a fresh visual. Use screenshot_extents
        for full-drawing overview without a known region.

        COORDINATES
        x1, y1: lower-left corner of the region in drawing units (mm).
        x2, y2: upper-right corner of the region in drawing units (mm).
        Same world coordinate system as all other tools.

        padding_pct (default 10): extra whitespace around the region.
        Increase when inspecting areas near drawing edges or tight groups.

        ANNOTATIONS (annotate=True, default)
        Labels are drawn as native AutoCAD MText on _ANNOT-TEMP before the
        screenshot and deleted immediately after. Because they are real model
        space entities at world coordinates, they scale with the drawing and
        are always positioned correctly relative to what they describe.

        The visual labels and the structured JSON entity list describe the
        same entities. The JSON gives you handles, types, layers, and bbox
        data for programmatic use. The labels let you visually confirm which
        entity in the image is which without cross-referencing coordinates.
        Together they eliminate the "what am I looking at" disambiguation
        phase that would otherwise require multiple follow-up calls.

        Label rules:
          - Block references: a bbox rectangle is drawn over the physical
            envelope, the block name (+ TYPE attribute if set) is centred
            inside it, and the bottom-left corner coordinate (x_min, y_min)
            and top-right corner coordinate (x_max, y_max) are labelled at
            their respective corners. The agent can read any edge directly
            from the image: left edge = x_min, right edge = x_max, bottom =
            y_min, top = y_max — no arithmetic needed.
          - LwPolylines: segment length at each midpoint (offset from the
            line) and the world coordinate (x, y) at every vertex. Wall
            extents, room corners, and counter runs are all readable without
            a separate data call.
          - Dimensions, text, MText: skipped — they already show their content.
          - All other entity types: entity handle at bbox centre. Pass this
            handle to get_entity_by_handle for further detail.

        Pass annotate=False when presenting a finished result to the user
        (clean drawing, no annotation clutter) or when label density at the
        current zoom would obscure the geometry you are trying to verify.

        CLEANUP GUARANTEE
        The annotation layer and all its entities are deleted in a try/finally
        block. Whether the screenshot succeeds, fails, or throws, the drawing
        is always returned to its original state — no temporary entities, no
        extra layer.

        RETURNS
        [Image (PNG), JSON string] — the annotated image and a metadata dict
        containing view_center_x, view_center_y, view_width, view_height,
        region bounds, and an "entities" list. Each entity in the list has:
        handle, type, layer, center_x, center_y, width, height.
        """
        if x2 <= x1 or y2 <= y1:
            raise ValueError(
                f"Invalid region: x2 ({x2}) must be > x1 ({x1}) and "
                f"y2 ({y2}) must be > y1 ({y1})."
            )

        doc = get_active_doc()
        wait_for_idle(doc)

        entities = _entities_in_region(doc, x1, y1, x2, y2)

        annot_handles = []
        if annotate:
            annot_handles = _draw_annotations(doc, x1, y1, x2, y2)

        pad_x = (x2 - x1) * padding_pct / 100.0
        pad_y = (y2 - y1) * padding_pct / 100.0
        px1, py1 = x1 - pad_x, y1 - pad_y
        px2, py2 = x2 + pad_x, y2 + pad_y

        saved = _save_view(doc)
        try:
            get_acad().ZoomWindow(point(px1, py1), point(px2, py2))
            meta = _view_metadata(doc)
            meta["capture_type"] = "region_with_context"
            meta["region"] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            meta["entities"] = entities
            meta["entity_count"] = len(entities)
            png_bytes = _capture_viewport(doc)
        finally:
            _restore_view(doc, saved)
            if annotate:
                _cleanup_annot_layer(doc, annot_handles)

        return [Image(data=png_bytes, format="png"), json.dumps(meta, indent=2)]
