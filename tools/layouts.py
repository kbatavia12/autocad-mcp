"""
tools/layouts.py
Tools for managing paper space layouts, viewports, and plotting in AutoCAD.
"""

import pythoncom
import win32com.client
from autocad_helpers import get_active_doc


def register_layout_tools(mcp):

    @mcp.tool()
    def list_layouts() -> list[dict]:
        """List all layouts in the active drawing (Model space + all paper space layouts)."""
        doc = get_active_doc()
        result = []
        for layout in doc.Layouts:
            result.append({
                "name": layout.Name,
                "tab_order": layout.TabOrder,
                "is_model_space": layout.ModelType,
                "block_name": layout.Block.Name,
            })
        return sorted(result, key=lambda x: x["tab_order"])

    @mcp.tool()
    def create_layout(name: str) -> str:
        """Create a new paper space layout with the given name."""
        doc = get_active_doc()
        layout = doc.Layouts.Add(name)
        return f"Layout '{name}' created (tab order: {layout.TabOrder})"

    @mcp.tool()
    def delete_layout(name: str) -> str:
        """Delete a paper space layout by name. Cannot delete Model space."""
        if name.upper() == "MODEL":
            raise ValueError("Cannot delete Model space layout.")
        doc = get_active_doc()
        layout = doc.Layouts.Item(name)
        layout.Delete()
        return f"Layout '{name}' deleted"

    @mcp.tool()
    def rename_layout(old_name: str, new_name: str) -> str:
        """Rename a paper space layout."""
        doc = get_active_doc()
        layout = doc.Layouts.Item(old_name)
        layout.Name = new_name
        return f"Layout '{old_name}' renamed to '{new_name}'"

    @mcp.tool()
    def set_active_layout(name: str) -> str:
        """Switch the active layout (e.g. 'Model', 'Layout1', or a custom layout name)."""
        doc = get_active_doc()
        doc.ActiveLayout = doc.Layouts.Item(name)
        return f"Active layout set to '{name}'"

    @mcp.tool()
    def get_layout_info(name: str) -> dict:
        """Get detailed info about a specific layout including paper size and viewport count."""
        doc = get_active_doc()
        layout = doc.Layouts.Item(name)
        return {
            "name": layout.Name,
            "tab_order": layout.TabOrder,
            "is_model_space": layout.ModelType,
            "paper_units": layout.PaperUnits,
            "plot_rotation": layout.PlotRotation,
            "use_standard_scale": layout.UseStandardScale,
            "viewport_count": layout.Block.Count,
        }

    @mcp.tool()
    def add_viewport(
        layout_name: str,
        center_x: float, center_y: float,
        width: float, height: float,
        scale: float = 1.0
    ) -> str:
        """
        Add a rectangular viewport to a paper space layout.
        center_x/y is the viewport center in paper space units.
        width/height define the viewport size. scale is the viewport scale (e.g. 0.02 = 1:50).
        """
        doc = get_active_doc()
        layout = doc.Layouts.Item(layout_name)
        block = layout.Block

        center = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(center_x), float(center_y), 0.0]
        )
        vp = block.AddPViewport(center, float(width), float(height))
        vp.CustomScale = float(scale)
        vp.Display(True)
        doc.Regen(2)  # acAllViewports
        return f"Viewport added to '{layout_name}' at ({center_x},{center_y}), {width}x{height}, scale={scale}"

    @mcp.tool()
    def set_viewport_scale(layout_name: str, viewport_index: int, scale: float) -> str:
        """
        Set the display scale of a viewport on a layout.
        viewport_index is 0-based among viewports on that layout.
        scale: e.g. 0.02 = 1:50, 0.01 = 1:100, 1.0 = 1:1
        """
        doc = get_active_doc()
        layout = doc.Layouts.Item(layout_name)
        vps = [
            layout.Block.Item(i)
            for i in range(layout.Block.Count)
            if layout.Block.Item(i).ObjectName == "AcDbViewport"
               and layout.Block.Item(i).Handle != "1"  # exclude overall paper viewport
        ]
        if viewport_index >= len(vps):
            raise IndexError(f"Only {len(vps)} viewport(s) on layout '{layout_name}'")
        vp = vps[viewport_index]
        vp.CustomScale = float(scale)
        vp.StandardScale = 0  # acVpCustomScale
        return f"Viewport {viewport_index} on '{layout_name}' scale set to {scale}"

    @mcp.tool()
    def freeze_layer_in_viewport(
        layout_name: str, viewport_index: int, layer_name: str, freeze: bool = True
    ) -> str:
        """
        Freeze or thaw a layer within a specific viewport without affecting other viewports.
        viewport_index is 0-based among viewports on that layout.
        """
        doc = get_active_doc()
        layout = doc.Layouts.Item(layout_name)
        vps = [
            layout.Block.Item(i)
            for i in range(layout.Block.Count)
            if layout.Block.Item(i).ObjectName == "AcDbViewport"
               and layout.Block.Item(i).Handle != "1"
        ]
        if viewport_index >= len(vps):
            raise IndexError(f"Only {len(vps)} viewport(s) on layout '{layout_name}'")
        vp = vps[viewport_index]
        layer = doc.Layers.Item(layer_name)
        if freeze:
            layer.FreezedInViewport(vp)
        else:
            layer.ThawedInViewport(vp)
        action = "frozen" if freeze else "thawed"
        return f"Layer '{layer_name}' {action} in viewport {viewport_index} of '{layout_name}'"

    @mcp.tool()
    def set_layout_paper_size(
        layout_name: str, width_mm: float, height_mm: float
    ) -> str:
        """
        Set the paper size for a layout in millimetres.
        Note: the plotter/printer must support custom paper sizes for this to take effect.
        """
        doc = get_active_doc()
        layout = doc.Layouts.Item(layout_name)
        layout.PaperUnits = 1  # acMillimeters
        layout.SetCustomScale(1.0, 1.0)
        # Use SetPlotConfigForLayout and custom paper via SendCommand as fallback
        doc.SendCommand(
            f"-LAYOUTWIZARD\n{layout_name}\n"
        )
        return (
            f"Paper size set attempt for '{layout_name}': {width_mm}x{height_mm}mm. "
            "For precise paper size control, use the Page Setup Manager in AutoCAD directly."
        )

    @mcp.tool()
    def plot_layout_to_pdf(layout_name: str, output_path: str) -> str:
        """
        Plot a layout to a PDF file using AutoCAD's built-in DWG to PDF.pc3 plotter.
        output_path should be a full Windows path e.g. C:/output/drawing.pdf
        AutoCAD 2017+ required.
        """
        doc = get_active_doc()
        layout = doc.Layouts.Item(layout_name)

        plot = doc.Plot
        plot.SetLayoutsToPlot(
            win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_BSTR, [layout_name])
        )
        plot_info = win32com.client.Dispatch("AutoCAD.PlotInfo")
        plot_info.Layout = layout

        plot_cfg = win32com.client.Dispatch("AutoCAD.PlotConfiguration")
        plot_cfg.CopyFrom(layout)
        plot_cfg.PlotToFile = True
        plot_cfg.PlotFileName = output_path
        plot_cfg.StyleSheet = ""
        # "DWG To PDF.pc3" must be installed (standard with AutoCAD)
        plot_cfg.SetPlotConfigurationName("DWG To PDF.pc3", "ANSI_A_(8.50_x_11.00_Inches)")

        plot_info.OverrideWith(plot_cfg)
        plot.PlotToFile(plot_info, output_path)
        return f"Layout '{layout_name}' plotted to '{output_path}'"

    @mcp.tool()
    def copy_layout(source_name: str, new_name: str) -> str:
        """Copy an existing layout (including its viewport setup) to a new layout."""
        doc = get_active_doc()
        doc.SendCommand(f"-LAYOUT\nCOPY\n{source_name}\n{new_name}\n")
        return f"Layout '{source_name}' copied to '{new_name}'"

    @mcp.tool()
    def reorder_layout(name: str, new_tab_order: int) -> str:
        """Move a layout tab to a specific position (1-based tab order)."""
        doc = get_active_doc()
        layout = doc.Layouts.Item(name)
        layout.TabOrder = new_tab_order
        return f"Layout '{name}' moved to tab position {new_tab_order}"
