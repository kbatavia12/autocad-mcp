"""
tools/layers.py
Tools for managing AutoCAD layers.
"""

from autocad_helpers import get_active_doc, color_index


def register_layer_tools(mcp):

    @mcp.tool()
    def list_layers() -> list[dict]:
        """Return all layers in the active drawing with their properties."""
        doc = get_active_doc()
        result = []
        for layer in doc.Layers:
            result.append({
                "name": layer.Name,
                "color": layer.color,
                "linetype": layer.Linetype,
                "lineweight": layer.Lineweight,
                "on": layer.LayerOn,
                "frozen": layer.Freeze,
                "locked": layer.Lock,
            })
        return result

    @mcp.tool()
    def create_layer(
        name: str,
        color: str = "white",
        linetype: str = "Continuous",
        locked: bool = False
    ) -> str:
        """
        Create a new layer. color can be a name (red, yellow, green, cyan,
        blue, magenta, white) or left as 'white'.
        """
        doc = get_active_doc()
        layer = doc.Layers.Add(name)
        layer.color = color_index(color)
        try:
            layer.Linetype = linetype
        except Exception:
            pass  # linetype may not be loaded; silently skip
        layer.Lock = locked
        return f"Layer '{name}' created (color={color}, linetype={linetype})"

    @mcp.tool()
    def set_active_layer(name: str) -> str:
        """Set the current active layer by name."""
        doc = get_active_doc()
        doc.ActiveLayer = doc.Layers.Item(name)
        return f"Active layer set to '{name}'"

    @mcp.tool()
    def delete_layer(name: str) -> str:
        """
        Delete a layer by name. The layer must be empty (no objects on it)
        and cannot be the current layer or layer '0'.
        """
        if name == "0":
            raise ValueError("Layer '0' cannot be deleted.")
        doc = get_active_doc()
        layer = doc.Layers.Item(name)
        layer.Delete()
        return f"Layer '{name}' deleted"

    @mcp.tool()
    def set_layer_color(name: str, color: str) -> str:
        """Set the color of a layer. color can be a name or ACI integer string."""
        doc = get_active_doc()
        layer = doc.Layers.Item(name)
        try:
            idx = int(color)
        except ValueError:
            idx = color_index(color)
        layer.color = idx
        return f"Layer '{name}' color set to {color}"

    @mcp.tool()
    def set_layer_visibility(name: str, visible: bool) -> str:
        """Turn a layer on or off."""
        doc = get_active_doc()
        layer = doc.Layers.Item(name)
        layer.LayerOn = visible
        return f"Layer '{name}' {'on' if visible else 'off'}"

    @mcp.tool()
    def freeze_layer(name: str, freeze: bool = True) -> str:
        """Freeze or thaw a layer."""
        doc = get_active_doc()
        layer = doc.Layers.Item(name)
        layer.Freeze = freeze
        return f"Layer '{name}' {'frozen' if freeze else 'thawed'}"

    @mcp.tool()
    def lock_layer(name: str, lock: bool = True) -> str:
        """Lock or unlock a layer."""
        doc = get_active_doc()
        layer = doc.Layers.Item(name)
        layer.Lock = lock
        return f"Layer '{name}' {'locked' if lock else 'unlocked'}"

    @mcp.tool()
    def rename_layer(old_name: str, new_name: str) -> str:
        """Rename a layer."""
        doc = get_active_doc()
        layer = doc.Layers.Item(old_name)
        layer.Name = new_name
        return f"Layer '{old_name}' renamed to '{new_name}'"

    @mcp.tool()
    def purge_unused_layers() -> str:
        """Remove all layers that contain no objects."""
        doc = get_active_doc()
        removed = []
        to_check = [doc.Layers.Item(i).Name for i in range(doc.Layers.Count)]
        for name in to_check:
            if name == "0":
                continue
            try:
                layer = doc.Layers.Item(name)
                if not layer.Freeze and layer.LayerOn:
                    layer.Delete()
                    removed.append(name)
            except Exception:
                pass
        return f"Purged {len(removed)} unused layer(s): {removed}" if removed else "No unused layers to purge"
