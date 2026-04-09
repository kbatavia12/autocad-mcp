"""
server.py
AutoCAD MCP Server — entry point.
Tailored for interior design workflows.

Requires AutoCAD to be open on Windows with COM/ActiveX enabled.
Run with: python server.py
"""

from mcp.server.fastmcp import FastMCP

# Core CAD tools
from tools.drawing import register_drawing_tools
from tools.layers import register_layer_tools
from tools.objects import register_object_tools
from tools.files import register_file_tools
from tools.query import register_query_tools

# Advanced CAD tools
from tools.layouts import register_layout_tools
from tools.blocks_xrefs_styles import register_blocks_xrefs_styles_tools
from tools.arrays import register_array_tools

# Interior design specific tools
from tools.interior_spaces import register_interior_space_tools
from tools.furniture import register_furniture_tools
from tools.schedules import register_schedule_tools
from tools.id_annotations import register_id_annotation_tools
from tools.interior_advanced import register_interior_advanced_tools
from tools.match_properties import register_match_properties_tools
from tools.images import register_image_tools

# Curriculum-driven tools (B.Des Interior Design 2025 Pattern)
from tools.geometric_construction import register_geometric_construction_tools
from tools.anthropometry import register_anthropometry_tools
from tools.mep_services import register_mep_services_tools
from tools.tile_design import register_tile_design_tools

# ---------------------------------------------------------------------------
# Create the MCP server
# ---------------------------------------------------------------------------
mcp = FastMCP("autocad-id")

# ---------------------------------------------------------------------------
# Register all tool groups
# ---------------------------------------------------------------------------

# Core CAD
register_drawing_tools(mcp)
register_layer_tools(mcp)
register_object_tools(mcp)
register_file_tools(mcp)
register_query_tools(mcp)

# Advanced CAD
register_layout_tools(mcp)
register_blocks_xrefs_styles_tools(mcp)
register_array_tools(mcp)

# Interior Design
register_interior_space_tools(mcp)
register_furniture_tools(mcp)
register_schedule_tools(mcp)
register_id_annotation_tools(mcp)
register_interior_advanced_tools(mcp)
register_match_properties_tools(mcp)
register_image_tools(mcp)

# Curriculum-driven tools
register_geometric_construction_tools(mcp)
register_anthropometry_tools(mcp)
register_mep_services_tools(mcp)
register_tile_design_tools(mcp)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
