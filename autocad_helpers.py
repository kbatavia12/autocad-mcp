"""
autocad_helpers.py
Shared utilities for COM/ActiveX interaction with AutoCAD.
"""

import pythoncom
import win32com.client
from typing import Tuple


def get_acad() -> win32com.client.CDispatch:
    """Get a reference to the running AutoCAD application. Raises if not open."""
    try:
        return win32com.client.GetActiveObject("AutoCAD.Application")
    except Exception:
        raise RuntimeError(
            "AutoCAD is not running. Please open AutoCAD before using this MCP."
        )


def get_model_space():
    """Return the ModelSpace collection of the active document."""
    return get_acad().ActiveDocument.ModelSpace


def get_active_doc():
    """Return the active document."""
    return get_acad().ActiveDocument


def point(x: float, y: float, z: float = 0.0):
    """Create a COM VARIANT point array for AutoCAD."""
    return win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y), float(z)]
    )


def apoint(coords: Tuple[float, float, float]):
    """Create a COM VARIANT point array from a tuple."""
    return point(*coords)


def color_index(name: str) -> int:
    """Map a color name to AutoCAD ACI color index."""
    colors = {
        "red": 1, "yellow": 2, "green": 3, "cyan": 4,
        "blue": 5, "magenta": 6, "white": 7, "black": 0,
        "gray": 8, "grey": 8,
    }
    return colors.get(name.lower(), 7)


def ensure_layer(doc, name: str, color: int = 7) -> str:
    """Create layer if it doesn't exist; return the layer name."""
    try:
        doc.Layers.Item(name)
    except Exception:
        layer = doc.Layers.Add(name)
        layer.color = color
    return name
