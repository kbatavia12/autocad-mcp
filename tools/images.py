"""
tools/images.py
External Image (XI) tools — IMAGEATTACH and raster image management.
Attach, manage, clip, adjust, and reference external raster images
in AutoCAD drawings. Particularly useful for interior designers
attaching material swatches, mood boards, site photos, and reference images.
"""

import math
import pythoncom
import win32com.client
from autocad_helpers import get_active_doc


def register_image_tools(mcp):

    # -----------------------------------------------------------------------
    # ATTACHING IMAGES
    # -----------------------------------------------------------------------

    @mcp.tool()
    def attach_image(
        file_path: str,
        x: float = 0.0, y: float = 0.0,
        width: float = 1000.0, height: float = 0.0,
        rotation_deg: float = 0.0,
        layer: str = "A-XREF"
    ) -> dict:
        """
        Attach a raster image (PNG, JPG, TIF, BMP) to model space.
        file_path: full Windows path to the image file.
        x, y: insertion point (bottom-left corner).
        width: display width in drawing units (mm). height: if 0, auto from aspect ratio.
        rotation_deg: rotation angle.

        Useful for: material reference boards, mood boards,
        site photographs, scanned survey drawings.
        """
        doc = get_active_doc()
        space = doc.ModelSpace

        insertion = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y), 0.0]
        )
        scale_x = float(width)
        img = space.AddRaster(
            file_path,
            insertion,
            scale_x,
            math.radians(rotation_deg)
        )
        img.Layer = layer

        if height > 0:
            # Attempt to set height separately if API supports it
            try:
                img.Height = float(height)
            except Exception:
                pass

        return {
            "handle": img.Handle,
            "name": img.Name if hasattr(img, "Name") else "image",
            "file_path": file_path,
            "insertion": [x, y],
            "width": width,
            "message": f"Image attached from '{file_path}' at ({x},{y}), width={width}mm"
        }

    @mcp.tool()
    def attach_reference_image(
        file_path: str,
        x: float, y: float,
        target_width_mm: float,
        real_world_width_mm: float = 0.0,
        label: str = "",
        rotation_deg: float = 0.0,
        layer: str = "A-XREF"
    ) -> dict:
        """
        Attach an image and optionally add a label below it.
        real_world_width_mm: if provided, scales the image to match real-world dimensions.
        Useful for attaching material sample images with product codes as callouts.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []

        insertion = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y), 0.0]
        )
        img = space.AddRaster(
            file_path, insertion,
            float(target_width_mm),
            math.radians(rotation_deg)
        )
        img.Layer = layer
        handles.append(img.Handle)

        if label:
            lbl_pt = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8,
                [x + target_width_mm / 2, y - target_width_mm * 0.1, 0.0]
            )
            txt = space.AddText(label, lbl_pt, target_width_mm * 0.06)
            txt.Layer = "A-ANNO-MATL"
            txt.Alignment = 4  # Middle center
            txt.TextAlignmentPoint = lbl_pt
            handles.append(txt.Handle)

        return {
            "handles": handles,
            "message": f"Reference image '{label}' attached at ({x},{y})"
        }

    # -----------------------------------------------------------------------
    # LISTING & INSPECTING IMAGES
    # -----------------------------------------------------------------------

    @mcp.tool()
    def list_images() -> list[dict]:
        """
        List all raster images attached to the active drawing.
        Returns file paths, handles, insertion points, and display state.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        images = []
        for i in range(space.Count):
            obj = space.Item(i)
            if obj.ObjectName == "AcDbRasterImage":
                info = {
                    "handle": obj.Handle,
                    "layer": obj.Layer,
                    "visible": obj.Visible,
                }
                try:
                    info["name"] = obj.Name
                except Exception:
                    pass
                try:
                    info["file_path"] = obj.ImageFile
                except Exception:
                    pass
                try:
                    info["width"] = obj.Width
                    info["height"] = obj.Height
                except Exception:
                    pass
                try:
                    info["brightness"] = obj.Brightness
                    info["contrast"] = obj.Contrast
                    info["fade"] = obj.Fade
                except Exception:
                    pass
                images.append(info)
        return images

    @mcp.tool()
    def get_image_info(handle: str) -> dict:
        """Get detailed properties of a raster image entity by handle."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        if obj.ObjectName != "AcDbRasterImage":
            raise ValueError(f"Entity {handle} is not a raster image")

        info = {"handle": handle, "type": "AcDbRasterImage", "layer": obj.Layer}
        for attr in ["Name", "ImageFile", "Width", "Height", "Brightness",
                     "Contrast", "Fade", "Clipping", "Transparency", "Visible"]:
            try:
                info[attr.lower()] = getattr(obj, attr)
            except Exception:
                pass
        return info

    # -----------------------------------------------------------------------
    # ADJUSTING IMAGES
    # -----------------------------------------------------------------------

    @mcp.tool()
    def set_image_brightness(handle: str, brightness: int) -> str:
        """
        Set image brightness. Value: 0–100 (50 = default/normal).
        Useful for fading reference images to the background.
        """
        if not (0 <= brightness <= 100):
            raise ValueError("brightness must be between 0 and 100")
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Brightness = int(brightness)
        return f"Image {handle} brightness set to {brightness}"

    @mcp.tool()
    def set_image_contrast(handle: str, contrast: int) -> str:
        """Set image contrast. Value: 0–100 (50 = default/normal)."""
        if not (0 <= contrast <= 100):
            raise ValueError("contrast must be between 0 and 100")
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Contrast = int(contrast)
        return f"Image {handle} contrast set to {contrast}"

    @mcp.tool()
    def set_image_fade(handle: str, fade: int) -> str:
        """
        Set image fade/transparency for display. Value: 0–100.
        0 = fully opaque, 100 = fully transparent.
        Useful for fading a reference image used as an underlay.
        """
        if not (0 <= fade <= 100):
            raise ValueError("fade must be between 0 and 100")
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Fade = int(fade)
        return f"Image {handle} fade set to {fade}"

    @mcp.tool()
    def set_image_transparency(handle: str, on: bool = True) -> str:
        """
        Toggle background transparency for images with transparent backgrounds (PNG).
        on=True makes the background colour transparent.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Transparency = on
        return f"Image {handle} transparency {'enabled' if on else 'disabled'}"

    @mcp.tool()
    def toggle_image_frame(handle: str, show: bool = True) -> str:
        """
        Show or hide the border frame around an image.
        Hiding frames is standard practice before plotting.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Clipping = show
        return f"Image {handle} frame {'shown' if show else 'hidden'}"

    @mcp.tool()
    def set_all_image_frames(show: bool = False) -> dict:
        """
        Show or hide frames on ALL images in model space at once.
        Typically called with show=False before exporting/plotting.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        updated = []
        for i in range(space.Count):
            obj = space.Item(i)
            if obj.ObjectName == "AcDbRasterImage":
                try:
                    obj.Clipping = show
                    updated.append(obj.Handle)
                except Exception:
                    pass
        return {
            "updated": updated,
            "message": f"Image frames {'shown' if show else 'hidden'} on {len(updated)} images"
        }

    # -----------------------------------------------------------------------
    # CLIPPING
    # -----------------------------------------------------------------------

    @mcp.tool()
    def clip_image_rectangular(
        handle: str,
        clip_x1: float, clip_y1: float,
        clip_x2: float, clip_y2: float
    ) -> str:
        """
        Clip a raster image to a rectangular boundary.
        Coordinates are in drawing (model space) units.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        clip_pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [clip_x1, clip_y1, clip_x2, clip_y1,
             clip_x2, clip_y2, clip_x1, clip_y2,
             clip_x1, clip_y1]
        )
        obj.ClipBoundary(clip_pts)
        obj.Clipping = True
        return f"Image {handle} clipped to ({clip_x1},{clip_y1})–({clip_x2},{clip_y2})"

    @mcp.tool()
    def clip_image_polygon(handle: str, clip_points: list[float]) -> str:
        """
        Clip a raster image to a polygonal boundary.
        clip_points: flat list of XY pairs [x1,y1, x2,y2, ...]. Minimum 3 points.
        """
        if len(clip_points) < 6 or len(clip_points) % 2 != 0:
            raise ValueError("clip_points must be an even list of at least 6 values (3 XY pairs)")
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        # Close the polygon
        if clip_points[:2] != clip_points[-2:]:
            clip_points = list(clip_points) + clip_points[:2]
        pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in clip_points]
        )
        obj.ClipBoundary(pts)
        obj.Clipping = True
        return f"Image {handle} clipped to {len(clip_points)//2}-point polygon"

    @mcp.tool()
    def remove_image_clip(handle: str) -> str:
        """Remove any clipping boundary from an image, restoring full display."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Clipping = False
        return f"Clip removed from image {handle}"

    # -----------------------------------------------------------------------
    # MANAGING / UNLOADING / REMOVING
    # -----------------------------------------------------------------------

    @mcp.tool()
    def reload_image(handle: str) -> str:
        """
        Reload an image from its source file.
        Use after the source image has been updated on disk.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Reload()
        return f"Image {handle} reloaded from disk"

    @mcp.tool()
    def unload_image(handle: str) -> str:
        """
        Unload an image (keeps the reference but removes it from display).
        Useful for reducing file size while preserving the image link.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Unload()
        return f"Image {handle} unloaded (link preserved)"

    @mcp.tool()
    def detach_image(handle: str) -> str:
        """Permanently remove (detach) a raster image from the drawing."""
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.Delete()
        return f"Image {handle} detached and removed"

    @mcp.tool()
    def update_image_path(handle: str, new_file_path: str) -> str:
        """
        Update the file path of an attached image.
        Use when the source file has been moved or renamed.
        """
        doc = get_active_doc()
        obj = doc.HandleToObject(handle)
        obj.ImageFile = new_file_path
        return f"Image {handle} path updated to '{new_file_path}'"

    # -----------------------------------------------------------------------
    # MOOD BOARD & MATERIAL BOARD TOOLS
    # -----------------------------------------------------------------------

    @mcp.tool()
    def create_material_image_board(
        x: float, y: float,
        images: list[dict],
        board_title: str = "MATERIAL BOARD",
        cols: int = 3,
        cell_width: float = 2000.0,
        cell_height: float = 2000.0,
        gap: float = 200.0,
        text_height: float = 120.0,
        layer: str = "A-XREF"
    ) -> dict:
        """
        Create a material/mood board grid by attaching multiple images with labels.

        images: list of dicts with keys:
          - file_path: full path to image file
          - label: material name (e.g. 'Calacatta Marble')
          - code: product code (optional)
          - supplier: supplier name (optional)
          - finish: finish description (optional)

        cols: number of images per row.
        cell_width/height: size of each image cell in mm.
        gap: spacing between cells.

        Example:
        [{"file_path": "C:/materials/marble.jpg", "label": "Calacatta Marble",
          "supplier": "Stone Import Co.", "code": "CAL-001"}]
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []
        rows = math.ceil(len(images) / cols)

        # Title
        title_pt = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x + (cols * (cell_width + gap)) / 2, y + text_height * 3, 0.0]
        )
        title = space.AddText(board_title, title_pt, text_height * 1.8)
        title.Layer = "A-ANNO"
        title.Alignment = 4
        title.TextAlignmentPoint = title_pt
        handles.append(title.Handle)

        for idx, img_info in enumerate(images):
            row = idx // cols
            col = idx % cols
            ix = x + col * (cell_width + gap)
            iy = y - row * (cell_height + gap + text_height * 3.5)

            # Attach image
            try:
                insertion = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(ix), float(iy), 0.0]
                )
                img = space.AddRaster(
                    img_info["file_path"],
                    insertion,
                    float(cell_width),
                    0.0
                )
                img.Layer = layer
                handles.append(img.Handle)
            except Exception:
                # Draw a placeholder box if image fails
                pts = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8,
                    [ix, iy, 0, ix + cell_width, iy, 0,
                     ix + cell_width, iy + cell_height, 0,
                     ix, iy + cell_height, 0, ix, iy, 0]
                )
                box = space.AddLightWeightPolyline(pts)
                box.Closed = True
                box.Layer = layer
                handles.append(box.Handle)
                err_pt = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8,
                    [ix + cell_width / 2, iy + cell_height / 2, 0.0]
                )
                err_txt = space.AddText("[Image not found]", err_pt, text_height)
                err_txt.Layer = layer
                err_txt.Alignment = 4
                err_txt.TextAlignmentPoint = err_pt
                handles.append(err_txt.Handle)

            # Label lines below image
            label_y = iy - text_height * 1.5
            label_lines = [
                (img_info.get("label", ""), text_height * 1.1),
                (img_info.get("supplier", "") + ("  " + img_info.get("code", "")
                 if img_info.get("code") else ""), text_height * 0.85),
                (img_info.get("finish", ""), text_height * 0.8),
            ]
            for i, (line_text, ht) in enumerate(label_lines):
                if not line_text.strip():
                    continue
                lpt = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8,
                    [ix + cell_width / 2, label_y - i * text_height * 1.4, 0.0]
                )
                lt = space.AddText(line_text, lpt, float(ht))
                lt.Layer = "A-ANNO-MATL"
                lt.Alignment = 4
                lt.TextAlignmentPoint = lpt
                handles.append(lt.Handle)

        doc.Regen(1)
        return {
            "handles": handles,
            "images_placed": len(images),
            "rows": rows,
            "cols": cols,
            "board_width": cols * (cell_width + gap),
            "message": f"Material board '{board_title}' created with {len(images)} images ({rows}×{cols})"
        }

    @mcp.tool()
    def create_mood_board_layout(
        x: float, y: float,
        title: str,
        hero_image_path: str,
        accent_images: list[dict],
        board_width: float = 10000.0,
        board_height: float = 7000.0,
        layer: str = "A-XREF"
    ) -> dict:
        """
        Create a professional mood board layout with one hero image and smaller accents.

        hero_image_path: path to the main large image.
        accent_images: list of dicts with 'file_path' and 'label'.
        Board is divided: hero takes 60% width, accents fill the right 40% in a grid.
        """
        doc = get_active_doc()
        space = doc.ModelSpace
        handles = []
        gap = board_width * 0.01

        # Board background border
        border_pts = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x, y, 0, x + board_width, y, 0,
             x + board_width, y + board_height, 0,
             x, y + board_height, 0, x, y, 0]
        )
        border = space.AddLightWeightPolyline(border_pts)
        border.Closed = True
        border.Layer = "A-ANNO"
        border.Lineweight = 50
        handles.append(border.Handle)

        # Title
        title_pt = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [x + board_width / 2, y + board_height + board_height * 0.05, 0.0]
        )
        t = space.AddText(title.upper(), title_pt, board_height * 0.04)
        t.Layer = "A-ANNO"
        t.Alignment = 4
        t.TextAlignmentPoint = title_pt
        handles.append(t.Handle)

        # Hero image (left 60%)
        hero_w = board_width * 0.58
        try:
            insertion = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8,
                [x + gap, y + gap, 0.0]
            )
            hero = space.AddRaster(hero_image_path, insertion, hero_w, 0.0)
            hero.Layer = layer
            handles.append(hero.Handle)
        except Exception:
            pass

        # Accent images (right 40%, in a grid)
        accent_x = x + hero_w + 2 * gap
        accent_area_w = board_width - hero_w - 3 * gap
        num_accents = len(accent_images)
        if num_accents > 0:
            accent_cols = 2 if num_accents > 2 else 1
            accent_rows = math.ceil(num_accents / accent_cols)
            cell_w = (accent_area_w - (accent_cols - 1) * gap) / accent_cols
            cell_h = (board_height - 2 * gap - accent_rows * board_height * 0.06) / accent_rows

            for i, acc in enumerate(accent_images):
                row = i // accent_cols
                col = i % accent_cols
                ax = accent_x + col * (cell_w + gap)
                ay = y + board_height - gap - (row + 1) * cell_h - row * gap

                try:
                    acc_pt = win32com.client.VARIANT(
                        pythoncom.VT_ARRAY | pythoncom.VT_R8, [ax, ay, 0.0]
                    )
                    acc_img = space.AddRaster(acc["file_path"], acc_pt, cell_w, 0.0)
                    acc_img.Layer = layer
                    handles.append(acc_img.Handle)
                except Exception:
                    pass

                # Accent label
                if acc.get("label"):
                    lpt = win32com.client.VARIANT(
                        pythoncom.VT_ARRAY | pythoncom.VT_R8,
                        [ax + cell_w / 2, ay - board_height * 0.04, 0.0]
                    )
                    lt = space.AddText(acc["label"], lpt, board_height * 0.025)
                    lt.Layer = "A-ANNO-MATL"
                    lt.Alignment = 4
                    lt.TextAlignmentPoint = lpt
                    handles.append(lt.Handle)

        doc.Regen(1)
        return {
            "handles": handles,
            "message": f"Mood board '{title}' created ({board_width}×{board_height}mm)"
        }
