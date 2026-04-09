# AutoCAD MCP Server

Control AutoCAD from Claude using the [Model Context Protocol](https://modelcontextprotocol.io).
Communicates with a running AutoCAD instance on Windows via COM/ActiveX automation.

---

## Requirements

- **Windows 10/11**
- **AutoCAD** (any recent version) — must be open before using the MCP
- **Python 3.10+**

---

## Installation

```bash
git clone https://github.com/your-username/autocad-mcp.git
cd autocad-mcp
pip install -r requirements.txt
```

> **Note:** After installing `pywin32`, you may need to run the post-install script:
> ```bash
> python Scripts/pywin32_postinstall.py -install
> ```

---

## Setup with Claude Desktop

Add the following to your `claude_desktop_config.json`
(typically at `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "autocad": {
      "command": "python",
      "args": ["C:/path/to/autocad-mcp/server.py"]
    }
  }
}
```

Restart Claude Desktop, open AutoCAD, and you're ready.

---

## Tools

### Drawing (`tools/drawing.py`)
| Tool | Description |
|---|---|
| `draw_line` | Draw a line between two points |
| `draw_circle` | Draw a circle from center + radius |
| `draw_arc` | Draw an arc with start/end angles |
| `draw_rectangle` | Draw an axis-aligned rectangle |
| `draw_polyline` | Draw a multi-vertex polyline |
| `draw_text` | Place single-line text |
| `draw_mtext` | Place multi-line text (MText) |
| `draw_ellipse` | Draw an ellipse |
| `draw_spline` | Draw a spline through fit points |
| `draw_hatch` | Apply a hatch pattern inside a rectangle |

### Layers (`tools/layers.py`)
| Tool | Description |
|---|---|
| `list_layers` | List all layers with properties |
| `create_layer` | Create a new layer |
| `set_active_layer` | Set the current drawing layer |
| `delete_layer` | Delete an empty layer |
| `set_layer_color` | Change a layer's color |
| `set_layer_visibility` | Turn a layer on/off |
| `freeze_layer` | Freeze/thaw a layer |
| `lock_layer` | Lock/unlock a layer |
| `rename_layer` | Rename a layer |
| `purge_unused_layers` | Remove empty layers |

### Object Manipulation (`tools/objects.py`)
| Tool | Description |
|---|---|
| `list_entities` | List entities, filter by layer/type |
| `get_entity_by_handle` | Get full properties of an entity |
| `move_entity` | Move by displacement vector |
| `copy_entity` | Copy and offset |
| `rotate_entity` | Rotate around a pivot |
| `scale_entity` | Scale from a base point |
| `mirror_entity` | Mirror across a line |
| `delete_entity` | Delete by handle |
| `set_entity_layer` | Move entity to a layer |
| `set_entity_color` | Change entity color |
| `set_entity_linetype` | Change entity linetype |
| `set_entity_lineweight` | Change entity lineweight |
| `explode_entity` | Explode compound entity |
| `offset_entity` | Offset a line/curve |

### Files & Views (`tools/files.py`)
| Tool | Description |
|---|---|
| `new_drawing` | Create a new drawing |
| `open_drawing` | Open a .dwg / .dxf file |
| `save_drawing` | Save the active drawing |
| `save_drawing_as` | Save to a new path |
| `close_drawing` | Close the active drawing |
| `list_open_drawings` | List all open drawings |
| `switch_active_drawing` | Bring a drawing to focus |
| `zoom_extents` | Zoom to fit all objects |
| `zoom_window` | Zoom to a rectangular region |
| `zoom_scale` | Zoom by scale factor |
| `set_view_center` | Set viewport center + height |
| `regen_drawing` | Regenerate all viewports |
| `undo` / `redo` | Undo/redo N steps |
| `purge_drawing` | Purge unused named objects |

### Query & Inspection (`tools/query.py`)
| Tool | Description |
|---|---|
| `get_drawing_info` | Metadata about the active drawing |
| `count_entities_by_type` | Entity count grouped by type |
| `get_bounding_box` | Bounding box of an entity |
| `get_drawing_extents` | Overall extents of all objects |
| `measure_distance` | Distance + angle between two points |
| `get_area` | Area (and perimeter) of a closed entity |
| `get_system_variable` | Read an AutoCAD system variable |
| `set_system_variable` | Write an AutoCAD system variable |
| `find_entities_in_region` | Find entities in a bounding box |
| `list_blocks` | List all block definitions |
| `insert_block` | Insert a block reference |
| `list_linetypes` | List loaded linetypes |
| `load_linetype` | Load a linetype from a .lin file |
| `add_linear_dimension` | Add an aligned linear dimension |
| `add_radius_dimension` | Add a radius dimension to a circle/arc |

---

## Architecture

```
autocad-mcp/
├── server.py            # MCP entry point, registers all tools
├── autocad_helpers.py   # Shared COM utilities (get_acad, point(), etc.)
├── tools/
│   ├── drawing.py       # Geometry creation tools
│   ├── layers.py        # Layer management tools
│   ├── objects.py       # Object selection & manipulation tools
│   ├── files.py         # File I/O and viewport tools
│   └── query.py         # Inspection, measurement, dimensions
├── requirements.txt
└── claude_desktop_config.example.json
```

**How it works:** The MCP server is a plain Python process. When Claude calls a tool, the server uses `pywin32` to reach into the running AutoCAD instance via COM and execute the operation. AutoCAD must be open — the server does not launch AutoCAD itself.

---

## Troubleshooting

**"AutoCAD is not running"** — Make sure AutoCAD is open before sending any commands.

**`pywin32` import error** — Run the post-install script:
```bash
python Scripts/pywin32_postinstall.py -install
```

**VARIANT / coordinate errors** — AutoCAD's COM API requires typed arrays for points. All coordinate handling is wrapped in `autocad_helpers.point()` to handle this.

**Commands not executing** — Some tools use `SendCommand()` which requires AutoCAD's command line to be idle. Avoid running commands while AutoCAD is mid-operation.

---

## Contributing

Pull requests welcome. To add a new tool group:
1. Create `tools/your_module.py` with a `register_your_tools(mcp)` function
2. Import and call it in `server.py`
