"""
server.py
AutoCAD MCP Server — entry point.

Requires AutoCAD to be open on Windows with COM/ActiveX enabled.
Run with: python server.py
"""

from mcp.server.fastmcp import FastMCP

from tools.drawing import register_drawing_tools
from tools.layers import register_layer_tools
from tools.objects import register_object_tools
from tools.files import register_file_tools
from tools.query import register_query_tools

# ---------------------------------------------------------------------------
# Create the MCP server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "autocad",
    description=(
        "Control AutoCAD on Windows via COM/ActiveX automation. "
        "Supports drawing, layer management, object manipulation, "
        "file operations, and drawing inspection."
    ),
)

# ---------------------------------------------------------------------------
# Register all tool groups
# ---------------------------------------------------------------------------
register_drawing_tools(mcp)
register_layer_tools(mcp)
register_object_tools(mcp)
register_file_tools(mcp)
register_query_tools(mcp)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
