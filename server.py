"""
server.py
AutoCAD MCP Server — entry point.
Tailored for interior design workflows.

Requires AutoCAD to be open on Windows with COM/ActiveX enabled.
Run with: python server.py
"""

from pathlib import Path

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
from tools.schedules import register_schedule_tools
from tools.id_annotations import register_id_annotation_tools
from tools.match_properties import register_match_properties_tools
from tools.images import register_image_tools

# Interior design domain tools
from tools.anthropometry import register_anthropometry_tools
from tools.mep_services import register_mep_services_tools
from tools.tile_design import register_tile_design_tools
from tools.knowledge import register_knowledge_tools

# Visual feedback
from tools.screenshots import register_screenshot_tools

# ---------------------------------------------------------------------------
# Create the MCP server
# ---------------------------------------------------------------------------
_system_prompt = (Path(__file__).parent / "system_prompt.md").read_text()
mcp = FastMCP("autocad-id", instructions=_system_prompt)

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
register_schedule_tools(mcp)
register_id_annotation_tools(mcp)
register_match_properties_tools(mcp)
register_image_tools(mcp)

# Interior design domain tools
register_anthropometry_tools(mcp)
register_mep_services_tools(mcp)
register_tile_design_tools(mcp)
register_knowledge_tools(mcp)

# Visual feedback
register_screenshot_tools(mcp)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AutoCAD MCP Server")
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Run as HTTP/SSE server so remote Claude Desktop clients can connect",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind when running remotely (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on when running remotely (default: 8000)",
    )
    args = parser.parse_args()

    if args.remote:
        print(f"Starting AutoCAD MCP in remote mode on {args.host}:{args.port}")
        print("Friend's Claude Desktop config URL:  http://YOUR_IP:{}/sse".format(args.port))
        print("Press Ctrl+C to stop.\n")
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run()
