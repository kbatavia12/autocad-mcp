"""
tools/match_properties.py
Match Properties tools — mirrors AutoCAD's MATCHPROP command.
Copy any combination of properties (layer, color, linetype, lineweight,
text style, dim style, hatch, plot style) from a source entity to targets.
Also includes batch property propagation and style sweeping tools.
"""

from autocad_helpers import get_active_doc, get_model_space, color_index


# Property flags used internally
_PROP_LAYER       = "layer"
_PROP_COLOR       = "color"
_PROP_LINETYPE    = "linetype"
_PROP_LINEWEIGHT  = "lineweight"
_PROP_TRANSPARENCY = "transparency"
_PROP_THICKNESS   = "thickness"
_PROP_PLOT_STYLE  = "plot_style"
_PROP_TEXT_STYLE  = "text_style"
_PROP_DIM_STYLE   = "dim_style"
_PROP_HATCH       = "hatch"
_PROP_VIEWPORT    = "viewport"

ALL_BASIC = [_PROP_LAYER, _PROP_COLOR, _PROP_LINETYPE, _PROP_LINEWEIGHT]
ALL_PROPS = ALL_BASIC + [_PROP_TEXT_STYLE, _PROP_DIM_STYLE, _PROP_HATCH]


def _apply_props(source, target, props: list[str]):
    """Copy selected properties from source entity to target entity."""
    errors = []
    for prop in props:
        try:
            if prop == _PROP_LAYER:
                target.Layer = source.Layer
            elif prop == _PROP_COLOR:
                target.color = source.color
            elif prop == _PROP_LINETYPE:
                target.Linetype = source.Linetype
            elif prop == _PROP_LINEWEIGHT:
                target.Lineweight = source.Lineweight
            elif prop == _PROP_TEXT_STYLE:
                if hasattr(source, "StyleName") and hasattr(target, "StyleName"):
                    target.StyleName = source.StyleName
            elif prop == _PROP_DIM_STYLE:
                if hasattr(source, "StyleName") and hasattr(target, "StyleName"):
                    target.StyleName = source.StyleName
            elif prop == _PROP_HATCH:
                if source.ObjectName == "AcDbHatch" and target.ObjectName == "AcDbHatch":
                    target.PatternName = source.PatternName
                    target.PatternScale = source.PatternScale
                    target.PatternAngle = source.PatternAngle
                    target.HatchStyle = source.HatchStyle
            elif prop == _PROP_THICKNESS:
                if hasattr(source, "Thickness") and hasattr(target, "Thickness"):
                    target.Thickness = source.Thickness
        except Exception as e:
            errors.append(f"{prop}: {str(e)}")
    return errors


def register_match_properties_tools(mcp):

    @mcp.tool()
    def match_properties(
        source_handle: str,
        target_handles: list[str],
        properties: list[str] = None
    ) -> dict:
        """
        Copy properties from a source entity to one or more target entities.
        Mirrors AutoCAD's MATCHPROP command.

        source_handle: handle of the entity whose properties to copy FROM.
        target_handles: list of handles to copy TO.
        properties: list of properties to match. If omitted, all basic properties
                    are matched. Options: 'layer', 'color', 'linetype', 'lineweight',
                    'text_style', 'dim_style', 'hatch', 'thickness'.
        """
        doc = get_active_doc()
        props = properties if properties else ALL_BASIC
        source = doc.HandleToObject(source_handle)

        results = {}
        for handle in target_handles:
            try:
                target = doc.HandleToObject(handle)
                errors = _apply_props(source, target, props)
                results[handle] = "ok" if not errors else f"partial ({'; '.join(errors)})"
            except Exception as e:
                results[handle] = f"error: {str(e)}"

        ok_count = sum(1 for v in results.values() if v == "ok")
        return {
            "source": source_handle,
            "properties_matched": props,
            "results": results,
            "message": f"Matched properties from {source_handle} to {ok_count}/{len(target_handles)} targets"
        }

    @mcp.tool()
    def match_properties_by_type(
        source_handle: str,
        entity_type: str = "",
        layer_filter: str = "",
        properties: list[str] = None
    ) -> dict:
        """
        Match properties from a source entity to ALL entities of a given type
        and/or layer. Useful for bulk restyling.

        source_handle: the entity to copy properties FROM.
        entity_type: optional filter e.g. 'AcDbText', 'AcDbLine', 'AcDbHatch'.
        layer_filter: optional layer name to restrict targets.
        properties: see match_properties for options.
        """
        doc = get_active_doc()
        space = get_model_space()
        props = properties if properties else ALL_BASIC
        source = doc.HandleToObject(source_handle)

        targets = []
        for i in range(space.Count):
            obj = space.Item(i)
            if obj.Handle == source_handle:
                continue
            if entity_type and obj.ObjectName != entity_type:
                continue
            if layer_filter and obj.Layer != layer_filter:
                continue
            targets.append(obj)

        applied = 0
        for target in targets:
            errors = _apply_props(source, target, props)
            if not errors:
                applied += 1

        return {
            "source": source_handle,
            "targets_found": len(targets),
            "targets_updated": applied,
            "filters": {"type": entity_type, "layer": layer_filter},
            "message": f"Properties from {source_handle} applied to {applied} entities"
        }

    @mcp.tool()
    def match_layer_only(source_handle: str, target_handles: list[str]) -> dict:
        """Quick shortcut: copy only the layer from source to targets."""
        doc = get_active_doc()
        source = doc.HandleToObject(source_handle)
        updated = []
        for h in target_handles:
            try:
                doc.HandleToObject(h).Layer = source.Layer
                updated.append(h)
            except Exception:
                pass
        return {
            "layer": source.Layer,
            "updated": updated,
            "message": f"Layer '{source.Layer}' applied to {len(updated)} entities"
        }

    @mcp.tool()
    def match_color_only(source_handle: str, target_handles: list[str]) -> dict:
        """Quick shortcut: copy only the color from source to targets."""
        doc = get_active_doc()
        source = doc.HandleToObject(source_handle)
        color = source.color
        updated = []
        for h in target_handles:
            try:
                doc.HandleToObject(h).color = color
                updated.append(h)
            except Exception:
                pass
        return {
            "color": color,
            "updated": updated,
            "message": f"Color {color} applied to {len(updated)} entities"
        }

    @mcp.tool()
    def match_hatch_properties(source_handle: str, target_handles: list[str]) -> dict:
        """
        Copy hatch pattern, scale, and angle from one hatch to other hatches.
        Source and all targets must be AcDbHatch entities.
        """
        doc = get_active_doc()
        source = doc.HandleToObject(source_handle)
        if source.ObjectName != "AcDbHatch":
            raise ValueError(f"Source {source_handle} is not a hatch entity")

        updated = []
        errors = []
        for h in target_handles:
            try:
                target = doc.HandleToObject(h)
                if target.ObjectName != "AcDbHatch":
                    errors.append(f"{h}: not a hatch")
                    continue
                target.PatternName = source.PatternName
                target.PatternScale = source.PatternScale
                target.PatternAngle = source.PatternAngle
                target.HatchStyle = source.HatchStyle
                target.color = source.color
                target.Layer = source.Layer
                updated.append(h)
            except Exception as e:
                errors.append(f"{h}: {str(e)}")

        return {
            "source_pattern": source.PatternName,
            "source_scale": source.PatternScale,
            "source_angle": source.PatternAngle,
            "updated": updated,
            "errors": errors,
            "message": f"Hatch properties copied to {len(updated)} hatches"
        }

    @mcp.tool()
    def match_text_style_across_drawing(
        source_handle: str,
        target_entity_types: list[str] = None
    ) -> dict:
        """
        Apply the text style (and height if non-zero) of a source text entity
        to all text/mtext/dimension objects in model space.
        target_entity_types: defaults to ['AcDbText', 'AcDbMText'].
        """
        doc = get_active_doc()
        space = get_model_space()
        source = doc.HandleToObject(source_handle)
        types = target_entity_types or ["AcDbText", "AcDbMText"]

        style_name = None
        try:
            style_name = source.StyleName
        except Exception:
            raise ValueError("Source entity has no StyleName property")

        updated = []
        for i in range(space.Count):
            obj = space.Item(i)
            if obj.Handle == source_handle:
                continue
            if obj.ObjectName not in types:
                continue
            try:
                obj.StyleName = style_name
                updated.append(obj.Handle)
            except Exception:
                pass

        return {
            "style_applied": style_name,
            "updated_count": len(updated),
            "message": f"Text style '{style_name}' applied to {len(updated)} text entities"
        }

    @mcp.tool()
    def match_dim_style_across_drawing(source_handle: str) -> dict:
        """
        Apply the dimension style of a source dimension entity to all
        dimension objects in model space.
        """
        doc = get_active_doc()
        space = get_model_space()
        source = doc.HandleToObject(source_handle)

        try:
            style_name = source.StyleName
        except Exception:
            raise ValueError("Source entity has no dimension StyleName property")

        dim_types = {
            "AcDbAlignedDimension", "AcDbRotatedDimension",
            "AcDbRadialDimension", "AcDbDiametricDimension",
            "AcDbAngularDimension", "AcDb3PointAngularDimension",
            "AcDbOrdinateDimension", "AcDbArcDimension"
        }
        updated = []
        for i in range(space.Count):
            obj = space.Item(i)
            if obj.Handle == source_handle:
                continue
            if obj.ObjectName not in dim_types:
                continue
            try:
                obj.StyleName = style_name
                updated.append(obj.Handle)
            except Exception:
                pass

        return {
            "style_applied": style_name,
            "updated_count": len(updated),
            "message": f"Dim style '{style_name}' applied to {len(updated)} dimension entities"
        }

    @mcp.tool()
    def set_properties_by_layer(
        layer_name: str,
        color: str = "",
        linetype: str = "",
        lineweight: int = -1
    ) -> dict:
        """
        Set color, linetype, and/or lineweight for ALL entities on a given layer.
        Useful for bulk restyling of a layer's objects without changing the layer itself.
        Pass empty string to skip a property.
        """
        space = get_model_space()
        updated = 0

        for i in range(space.Count):
            obj = space.Item(i)
            if obj.Layer != layer_name:
                continue
            try:
                if color:
                    try:
                        obj.color = int(color)
                    except ValueError:
                        obj.color = color_index(color)
                if linetype:
                    obj.Linetype = linetype
                if lineweight >= 0:
                    obj.Lineweight = lineweight
                updated += 1
            except Exception:
                pass

        return {
            "layer": layer_name,
            "entities_updated": updated,
            "message": f"{updated} entities on layer '{layer_name}' updated"
        }

    @mcp.tool()
    def copy_entity_properties_to_new(
        source_handle: str,
        copies: int = 1,
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ) -> dict:
        """
        Create copies of an entity that inherit all source properties,
        offset by (offset_x, offset_y) per copy. Useful for repeating
        styled elements (e.g. identical room tags, repeated callouts).
        """
        import pythoncom
        import win32com.client
        doc = get_active_doc()
        source = doc.HandleToObject(source_handle)
        handles = []

        for i in range(1, copies + 1):
            copy = source.Copy()
            dx = offset_x * i
            dy = offset_y * i
            origin = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0]
            )
            displacement = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(dx), float(dy), 0.0]
            )
            copy.Move(origin, displacement)
            handles.append(copy.Handle)

        return {
            "source": source_handle,
            "copies_created": len(handles),
            "handles": handles,
            "message": f"{copies} styled copies of {source_handle} created"
        }

    @mcp.tool()
    def audit_property_consistency(layer_name: str = "") -> dict:
        """
        Audit model space for property inconsistencies — entities with colors,
        linetypes, or lineweights set to 'ByLayer' vs explicit overrides.
        Optionally filter to a specific layer.
        Returns a summary of how many objects have overrides vs ByLayer settings.
        """
        space = get_model_space()

        by_layer = 0
        overridden = 0
        override_details: dict[str, list] = {
            "color": [], "linetype": [], "lineweight": []
        }

        for i in range(space.Count):
            obj = space.Item(i)
            if layer_name and obj.Layer != layer_name:
                continue
            is_override = False
            try:
                if obj.color not in (256, 0):  # 256=ByLayer, 0=ByBlock
                    override_details["color"].append(obj.Handle)
                    is_override = True
            except Exception:
                pass
            try:
                if obj.Linetype not in ("ByLayer", "BYLAYER"):
                    override_details["linetype"].append(obj.Handle)
                    is_override = True
            except Exception:
                pass
            try:
                if obj.Lineweight not in (-1, -2):  # -1=ByLayer, -2=ByBlock
                    override_details["lineweight"].append(obj.Handle)
                    is_override = True
            except Exception:
                pass

            if is_override:
                overridden += 1
            else:
                by_layer += 1

        total = by_layer + overridden
        return {
            "total_checked": total,
            "by_layer": by_layer,
            "with_overrides": overridden,
            "color_overrides": len(override_details["color"]),
            "linetype_overrides": len(override_details["linetype"]),
            "lineweight_overrides": len(override_details["lineweight"]),
            "sample_override_handles": {
                k: v[:5] for k, v in override_details.items() if v
            },
            "message": f"{overridden}/{total} entities have property overrides"
        }

    @mcp.tool()
    def reset_entity_properties_to_bylayer(
        handles: list[str] = None,
        layer_filter: str = ""
    ) -> dict:
        """
        Reset color, linetype, and lineweight to ByLayer for specified entities
        (or all entities on a layer). Equivalent to selecting all and setting
        properties back to ByLayer in the Properties palette.
        """
        doc = get_active_doc()
        space = get_model_space()
        updated = []

        if handles:
            targets = []
            for h in handles:
                try:
                    targets.append(doc.HandleToObject(h))
                except Exception:
                    pass
        else:
            targets = [
                space.Item(i) for i in range(space.Count)
                if not layer_filter or space.Item(i).Layer == layer_filter
            ]

        for obj in targets:
            try:
                obj.color = 256        # ByLayer
                obj.Linetype = "ByLayer"
                obj.Lineweight = -1    # ByLayer
                updated.append(obj.Handle)
            except Exception:
                pass

        return {
            "reset_count": len(updated),
            "message": f"{len(updated)} entities reset to ByLayer properties"
        }
