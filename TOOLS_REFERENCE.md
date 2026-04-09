# AutoCAD MCP — Complete Tools Reference
### Interior Design Workflow · 226 Tools · 19 Modules

> All prompts below are written as you would say them to Claude with this MCP active.
> Coordinates are in **millimetres** unless otherwise noted.

---

## Table of Contents
1. [Drawing](#1-drawing)
2. [Layers](#2-layers)
3. [Objects](#3-objects)
4. [Files](#4-files)
5. [Query](#5-query)
6. [Layouts](#6-layouts)
7. [Blocks, Xrefs & Styles](#7-blocks-xrefs--styles)
8. [Arrays](#8-arrays)
9. [Interior Spaces](#9-interior-spaces)
10. [Furniture](#10-furniture)
11. [Schedules](#11-schedules)
12. [ID Annotations](#12-id-annotations)
13. [Interior Advanced](#13-interior-advanced)
14. [Match Properties](#14-match-properties)
15. [Images](#15-images)
16. [Geometric Construction](#16-geometric-construction)
17. [Anthropometry](#17-anthropometry)
18. [MEP Services](#18-mep-services)
19. [Tile Design](#19-tile-design)

---

## 1. Drawing

### `draw_line`
Draw a straight line between two points.

**Example prompts:**
- *"Draw a line from (0,0) to (3000,0)"*
- *"Draw a 4500mm horizontal line starting at coordinate 500, 1200"*
- *"Draw a diagonal construction line from (0,0) to (2000,2000) on layer A-CONST"*

---

### `draw_circle`
Draw a circle by centre point and radius.

**Example prompts:**
- *"Draw a circle at the centre of the room (3000,2000) with radius 500"*
- *"Place a 1200mm diameter circle at (0,0)"*
- *"Draw a 75mm radius circle at (1500,1500) on layer A-FURN"*

---

### `draw_arc`
Draw an arc by centre, radius, start angle, and end angle.

**Example prompts:**
- *"Draw a quarter circle arc centred at (1000,1000), radius 800, from 0° to 90°"*
- *"Draw a door swing arc: centre (0,0), radius 900, from 0° to 90°"*
- *"Add a 180° arc at the end of the corridor to show the turning radius"*

---

### `draw_rectangle`
Draw a rectangle by corner point, width, and height.

**Example prompts:**
- *"Draw a 4800 × 3600mm rectangle starting at (0,0)"*
- *"Place a 600×600mm square at coordinate (1200,1200)"*
- *"Draw a 2400×900mm rectangle on layer A-FURN to represent a countertop"*

---

### `draw_polyline`
Draw a multi-point open or closed polyline.

**Example prompts:**
- *"Draw a closed polyline through points (0,0), (5000,0), (5000,3000), (2000,4500), (0,3000)"*
- *"Draw an L-shaped polyline from (0,0) → (3000,0) → (3000,1500) → (1500,1500) → (1500,3000) → (0,3000)"*
- *"Draw an open polyline representing a circulation path through these waypoints"*

---

### `draw_text`
Place single-line text (DTEXT).

**Example prompts:**
- *"Add the text 'LIVING ROOM' at coordinate (2000,1500), height 200mm"*
- *"Place the label 'NOT TO SCALE' at (0,-500), text height 150"*
- *"Write 'PROPOSED KITCHEN LAYOUT' centred at the top of the drawing"*

---

### `draw_mtext`
Place multi-line text with word wrap (MTEXT).

**Example prompts:**
- *"Add a notes box at (0,-1000) with text: 'All dimensions in mm. Verify on site before construction. Do not scale from drawing.' Width 2000mm, height 150"*
- *"Place a general notes paragraph at the bottom of the sheet"*
- *"Add a 3-line spec note for the kitchen joinery at (5000,0)"*

---

### `draw_ellipse`
Draw an ellipse by centre, semi-major axis, and ratio.

**Example prompts:**
- *"Draw an elliptical coffee table at (2000,1500), semi-major 900mm, ratio 0.6"*
- *"Place an oval rug outline: centre (3000,2000), semi-major 1500, ratio 0.65"*
- *"Draw an ellipse on the ceiling for a feature plaster oval, semi-major 2000, ratio 0.5"*

---

### `draw_spline`
Draw a smooth spline curve through control points.

**Example prompts:**
- *"Draw a spline through (0,0), (1000,500), (2000,200), (3000,800), (4000,0) to show the curved sofa profile"*
- *"Create a smooth organic wall curve using a spline through these 6 points"*
- *"Draw a curved pathway on the landscaping plan as a spline"*

---

### `draw_hatch`
Fill a closed boundary with a hatch pattern.

**Example prompts:**
- *"Hatch the floor area using ANSI37 pattern, scale 1.0"*
- *"Fill the timber deck area with AR-RROOF hatch at 45° angle"*
- *"Apply a concrete hatch (AR-CONC) to the structural slab boundary, handle ABC123"*

---

## 2. Layers

### `list_layers`
List all layers with their current state.

**Example prompts:**
- *"Show me all the layers in this drawing"*
- *"List every layer and tell me which ones are frozen or locked"*
- *"What layers do I currently have set up?"*

---

### `create_layer`
Create a new layer with colour and linetype.

**Example prompts:**
- *"Create a layer called A-FURN-SOFA, colour red, linetype CONTINUOUS"*
- *"Add a new layer named E-LITE for lighting, colour 3 (green)"*
- *"Create a magenta dashed layer called A-CONS for construction lines"*

---

### `set_active_layer`
Make a layer the current drawing layer.

**Example prompts:**
- *"Set the active layer to A-WALL"*
- *"Switch to layer A-FURN before I place furniture"*
- *"Make E-POWR the current layer"*

---

### `delete_layer`
Delete a layer (must be empty).

**Example prompts:**
- *"Delete the layer called TEMP"*
- *"Remove layer A-OLD-WALLS from the drawing"*

---

### `set_layer_color`
Change the colour of a layer.

**Example prompts:**
- *"Change layer A-WALL to colour 8 (grey)"*
- *"Set the A-FURN layer colour to yellow (2)"*
- *"Make the electrical layer (E-POWR) red"*

---

### `set_layer_visibility`
Turn a layer on or off.

**Example prompts:**
- *"Turn off the furniture layer so I can see the floor plan clearly"*
- *"Hide layer A-ANNO-DIMS"*
- *"Turn on all layers"*

---

### `freeze_layer`
Freeze or thaw a layer.

**Example prompts:**
- *"Freeze the A-CONS construction line layer"*
- *"Thaw all frozen layers"*
- *"Freeze the existing conditions layer before printing"*

---

### `lock_layer`
Lock or unlock a layer.

**Example prompts:**
- *"Lock the A-WALL layer so nothing gets accidentally moved"*
- *"Unlock layer A-FURN"*
- *"Lock all annotation layers"*

---

### `rename_layer`
Rename a layer.

**Example prompts:**
- *"Rename the layer WALLS to A-WALL"*
- *"Rename FURNITURE to A-FURN to match AIA naming conventions"*

---

### `purge_unused_layers`
Delete all empty/unused layers.

**Example prompts:**
- *"Purge all unused layers to clean up the drawing"*
- *"Remove any layers that have no objects on them"*

---

## 3. Objects

### `list_entities`
List all entities with type, layer, and handle.

**Example prompts:**
- *"List all the entities in the drawing"*
- *"Show me everything on layer A-FURN"*
- *"How many objects are in this drawing?"*

---

### `get_entity_by_handle`
Get full properties of a single entity.

**Example prompts:**
- *"Get the properties of entity with handle 2A3F"*
- *"What layer and colour is entity ABC1?"*
- *"Tell me everything about object handle 1B2C"*

---

### `move_entity`
Move an entity by a delta offset.

**Example prompts:**
- *"Move entity 2A3F by 500mm to the right and 200mm up"*
- *"Shift the dining table (handle XY12) 300mm north"*
- *"Move that sofa 1000mm towards the window"*

---

### `copy_entity`
Copy an entity to a new position.

**Example prompts:**
- *"Copy the chair (handle 1A2B) 600mm to the right to create a second chair"*
- *"Duplicate the door symbol and place it at the bedroom entrance"*
- *"Copy the room tag from bedroom 1 and place it at (8000,3000)"*

---

### `rotate_entity`
Rotate an entity about a base point.

**Example prompts:**
- *"Rotate the bed (handle 3C4D) 90° clockwise about its centre (5000,3000)"*
- *"Turn the dining table 45° around point (2000,2000)"*
- *"Rotate that door symbol 180°"*

---

### `scale_entity`
Scale an entity uniformly from a base point.

**Example prompts:**
- *"Scale the sofa symbol by factor 1.2 from its base point (1000,500)"*
- *"Reduce the kitchen unit to 0.8× its current size"*
- *"Scale up the title block to 1.5× from the bottom-left corner"*

---

### `mirror_entity`
Mirror an entity across a line.

**Example prompts:**
- *"Mirror the kitchen layout about the vertical centre line of the room"*
- *"Mirror the left door handle to create the right one"*
- *"Reflect the bathroom layout horizontally about x=3000"*

---

### `delete_entity`
Delete an entity by handle.

**Example prompts:**
- *"Delete entity with handle 4E5F"*
- *"Remove the construction lines (handles AA1, AA2, AA3)"*
- *"Erase that temporary line I drew"*

---

### `set_entity_layer`
Move an entity to a different layer.

**Example prompts:**
- *"Move entity 2A3F to layer A-FURN"*
- *"Put all the furniture handles on the correct A-FURN layer"*
- *"Move the toilet symbol to the P-FIXT layer"*

---

### `set_entity_color`
Override an entity's colour.

**Example prompts:**
- *"Change entity 5G6H to colour blue (5)"*
- *"Make that highlighted wall red for the presentation"*
- *"Set entity ABC1 colour to ByLayer (256)"*

---

### `set_entity_linetype`
Override an entity's linetype.

**Example prompts:**
- *"Change entity 2A3F to a DASHED linetype"*
- *"Make the hidden line entity use HIDDEN2 linetype"*
- *"Set that boundary line to CENTER linetype"*

---

### `set_entity_lineweight`
Override an entity's lineweight.

**Example prompts:**
- *"Set entity 3B4C to 0.5mm lineweight"*
- *"Make the wall outline 0.7mm thick"*
- *"Change entity XY12 lineweight to ByLayer"*

---

### `explode_entity`
Explode a block, polyline, or hatch into primitives.

**Example prompts:**
- *"Explode the sofa block (handle 7D8E) so I can edit individual lines"*
- *"Break apart the dimension (handle 2A3F) into its components"*
- *"Explode the hatch on the floor and delete just the border"*

---

### `offset_entity`
Offset a curve by a distance.

**Example prompts:**
- *"Offset the wall polyline (handle 1A2B) by 150mm to create the inner wall face"*
- *"Offset the room boundary 600mm inward for the skirting line"*
- *"Create a 50mm offset of the counter edge for the splashback line"*

---

## 4. Files

### `new_drawing`
Create a new DWG file.

**Example prompts:**
- *"Create a new drawing"*
- *"Start a new DWG for the master bedroom design"*

---

### `open_drawing`
Open an existing DWG file.

**Example prompts:**
- *"Open the file at C:\Projects\Client\FloorPlan.dwg"*
- *"Open the existing kitchen drawing from my desktop"*

---

### `save_drawing`
Save the current drawing.

**Example prompts:**
- *"Save the drawing"*
- *"Save everything now before we continue"*

---

### `save_drawing_as`
Save to a new file path.

**Example prompts:**
- *"Save a copy of this drawing as FloorPlan_v2.dwg in the same folder"*
- *"Save as C:\Projects\Client\Bedroom_Rev01.dwg"*

---

### `close_drawing`
Close the current drawing.

**Example prompts:**
- *"Close this drawing and save it first"*
- *"Close without saving"*

---

### `list_open_drawings`
List all currently open DWGs.

**Example prompts:**
- *"What drawings do I have open right now?"*
- *"List all open AutoCAD files"*

---

### `switch_active_drawing`
Switch focus to a different open drawing.

**Example prompts:**
- *"Switch to the kitchen drawing"*
- *"Make FloorPlan.dwg the active drawing"*

---

### `export_to_pdf`
Export the current layout to PDF.

**Example prompts:**
- *"Export the A1 layout to PDF and save it in the project folder"*
- *"Print Layout 1 to a PDF file"*
- *"Export all layouts to PDF for client review"*

---

### `zoom_extents`
Zoom to fit all drawing content.

**Example prompts:**
- *"Zoom to extents so I can see the whole drawing"*
- *"Zoom out to show everything"*

---

### `zoom_window`
Zoom to a specific window area.

**Example prompts:**
- *"Zoom into the kitchen area, roughly (4000,2000) to (8000,5000)"*
- *"Zoom window to the bathroom corner"*

---

### `zoom_scale`
Zoom to an absolute scale factor.

**Example prompts:**
- *"Zoom to 1:50 scale"*
- *"Set the view scale to 1:100"*

---

### `set_view_center`
Pan the view to a coordinate.

**Example prompts:**
- *"Centre the view on the living room at (5000,3000)"*
- *"Pan to coordinate (0,0)"*

---

### `regen_drawing`
Regenerate the drawing display.

**Example prompts:**
- *"Regen the drawing — the arcs look blocky"*
- *"Regenerate to fix the display"*

---

### `undo`
Undo the last N operations.

**Example prompts:**
- *"Undo the last action"*
- *"Undo the last 5 steps"*

---

### `redo`
Redo the last N undone operations.

**Example prompts:**
- *"Redo that last action"*
- *"Redo 3 steps"*

---

### `purge_drawing`
Purge all unused blocks, linetypes, styles.

**Example prompts:**
- *"Purge the drawing to remove all unused definitions"*
- *"Clean up the drawing file — purge everything unused"*

---

## 5. Query

### `get_drawing_info`
Get filename, units, extents, and metadata.

**Example prompts:**
- *"What are the drawing units and extents?"*
- *"Tell me about this drawing — filename, path, scale"*

---

### `count_entities_by_type`
Get a count of every entity type.

**Example prompts:**
- *"How many lines, arcs, and blocks are in this drawing?"*
- *"Give me a breakdown of all entity types"*

---

### `get_bounding_box`
Get the bounding box of an entity.

**Example prompts:**
- *"What are the extents of entity 2A3F?"*
- *"How wide and tall is the kitchen block?"*

---

### `get_drawing_extents`
Get the min/max extents of the whole drawing.

**Example prompts:**
- *"What are the overall drawing extents?"*
- *"How big is the overall drawing boundary?"*

---

### `measure_distance`
Measure distance between two points.

**Example prompts:**
- *"What is the distance from (0,0) to (4500,3200)?"*
- *"Measure between these two points for me"*

---

### `get_area`
Calculate area of a closed entity.

**Example prompts:**
- *"What is the area of the closed polyline with handle 1A2B?"*
- *"Calculate the floor area of the living room boundary"*

---

### `get_system_variable`
Read any AutoCAD system variable.

**Example prompts:**
- *"What is the current INSUNITS setting?"*
- *"What is LTSCALE set to?"*
- *"Read the DIMSCALE variable"*

---

### `set_system_variable`
Write any AutoCAD system variable.

**Example prompts:**
- *"Set LTSCALE to 50"*
- *"Change INSUNITS to 4 (millimetres)"*
- *"Set DIMSCALE to 50 for a 1:50 drawing"*

---

### `find_entities_in_region`
Find all entities within a bounding box.

**Example prompts:**
- *"Find everything inside the area (0,0) to (5000,4000)"*
- *"What objects are in the kitchen zone?"*

---

### `list_blocks`
List all block definitions.

**Example prompts:**
- *"What blocks are defined in this drawing?"*
- *"List all the furniture block symbols"*

---

### `insert_block`
Insert a block by name at a position.

**Example prompts:**
- *"Insert block 'CHAIR-01' at position (3000,2000), scale 1, rotation 0°"*
- *"Place the WC block at the bathroom corner"*

---

### `list_linetypes`
List all loaded linetypes.

**Example prompts:**
- *"What linetypes are loaded in this drawing?"*
- *"Show me all available linetypes"*

---

### `load_linetype`
Load a linetype from a .lin file.

**Example prompts:**
- *"Load the HIDDEN2 linetype from acad.lin"*
- *"Load all standard linetypes from the ISO linetype file"*

---

### `add_linear_dimension`
Add a horizontal or vertical dimension.

**Example prompts:**
- *"Add a horizontal dimension from (0,0) to (4800,0), text position at (2400,-300)"*
- *"Dimension the room width — from (0,0) to (6000,0)"*

---

### `add_radius_dimension`
Add a radius dimension to a circle or arc.

**Example prompts:**
- *"Add a radius dimension to the arc with handle 3C4D"*
- *"Dimension the turning radius of that arc"*

---

## 6. Layouts

### `list_layouts`
List all paper space layouts.

**Example prompts:**
- *"What layouts do I have in this drawing?"*
- *"List all the sheets set up in paper space"*

---

### `create_layout`
Create a new paper space layout.

**Example prompts:**
- *"Create a new layout called 'A1 FLOOR PLAN'"*
- *"Add a layout named 'KITCHEN ELEVATIONS'"*

---

### `delete_layout`
Delete a layout.

**Example prompts:**
- *"Delete the layout called 'DRAFT'"*
- *"Remove the unused Sheet 3 layout"*

---

### `rename_layout`
Rename a layout.

**Example prompts:**
- *"Rename Layout1 to 'GROUND FLOOR PLAN'"*
- *"Change the sheet name from 'A' to 'FLOOR PLAN - GF'"*

---

### `set_active_layout`
Switch to a layout.

**Example prompts:**
- *"Switch to the 'ELEVATIONS' layout"*
- *"Go to paper space layout A1"*

---

### `get_layout_info`
Get layout paper size, scale, and viewport info.

**Example prompts:**
- *"What paper size and scale is the current layout?"*
- *"Tell me about the 'FLOOR PLAN' layout settings"*

---

### `add_viewport`
Add a viewport to a layout.

**Example prompts:**
- *"Add a viewport to the A1 layout, positioned at (50,50), size 800×580"*
- *"Create a new viewport on the current layout for the kitchen detail"*

---

### `set_viewport_scale`
Set the display scale of a viewport.

**Example prompts:**
- *"Set the active viewport to 1:50 scale"*
- *"Change viewport scale to 1:100"*

---

### `freeze_layer_in_viewport`
Freeze a layer only in the current viewport.

**Example prompts:**
- *"Freeze the furniture layer in just this viewport"*
- *"Hide the MEP layer in the floor plan viewport but keep it visible in the services viewport"*

---

### `set_layout_paper_size`
Set the paper size of a layout.

**Example prompts:**
- *"Set the current layout to A1 paper size"*
- *"Change the sheet size to A3 landscape"*

---

### `plot_layout_to_pdf`
Plot a single layout to PDF.

**Example prompts:**
- *"Plot the 'FLOOR PLAN' layout to PDF"*
- *"Save the current layout as a PDF in the project folder"*

---

### `copy_layout`
Duplicate a layout.

**Example prompts:**
- *"Copy the 'FLOOR PLAN' layout and name it 'FLOOR PLAN - FURNITURE'"*
- *"Duplicate Sheet 01 to create Sheet 02"*

---

### `reorder_layout`
Reorder a layout tab position.

**Example prompts:**
- *"Move the 'ELEVATIONS' layout to position 3"*
- *"Reorder the sheets so 'COVER SHEET' is first"*

---

## 7. Blocks, Xrefs & Styles

### `create_block_definition`
Create a named block from existing entities.

**Example prompts:**
- *"Create a block called 'DOOR-900' from entities with handles 1A, 2B, 3C, using (0,0) as insertion point"*
- *"Group the toilet symbol entities into a block named 'WC-STANDARD'"*

---

### `add_attribute_to_block`
Add an attribute definition to a block.

**Example prompts:**
- *"Add a 'ROOM_NAME' attribute to the ROOM-TAG block"*
- *"Add attributes ITEM, QTY, SUPPLIER to the FF&E block"*

---

### `list_block_attributes`
List all attribute definitions for a block.

**Example prompts:**
- *"What attributes does the ROOM-TAG block have?"*
- *"List the ATTDEFs for the DOOR-SCHEDULE block"*

---

### `set_block_attribute_value`
Edit a live attribute value in a block instance.

**Example prompts:**
- *"Set the ROOM_NAME attribute on block handle 5D6E to 'MASTER BEDROOM'"*
- *"Change the room number tag for the lounge to '101'"*

---

### `sync_block_attributes`
Synchronise attributes after a block definition change.

**Example prompts:**
- *"Sync attributes for the ROOM-TAG block across the whole drawing"*
- *"Run ATTSYNC on the DOOR block after I updated the definition"*

---

### `rename_block`
Rename a block definition.

**Example prompts:**
- *"Rename block 'CHAIR' to 'CHAIR-DINING-450'"*
- *"Rename the OLD-DOOR block to DOOR-900-SINGLE"*

---

### `purge_block`
Delete an unused block definition.

**Example prompts:**
- *"Purge the unused TEMP-BLOCK definition"*
- *"Delete the block definition 'IMPORT-01' that I no longer use"*

---

### `list_xrefs`
List all attached XRefs and their status.

**Example prompts:**
- *"Show me all the XRefs attached to this drawing"*
- *"Which XRefs are currently unloaded?"*

---

### `attach_xref`
Attach an external reference DWG.

**Example prompts:**
- *"Attach the structural grid drawing as an XRef at (0,0)"*
- *"XRef the base building plan from C:\Projects\Base.dwg"*

---

### `detach_xref`
Detach an XRef.

**Example prompts:**
- *"Detach the 'STRUCTURE' XRef"*
- *"Remove the base plan XRef from this drawing"*

---

### `reload_xref`
Reload all or one XRef from disk.

**Example prompts:**
- *"Reload all XRefs to pick up the latest changes"*
- *"Reload just the 'ELECTRICAL' XRef"*

---

### `unload_xref`
Unload an XRef without detaching.

**Example prompts:**
- *"Unload the structural XRef to speed up the drawing"*
- *"Turn off the services XRef without removing it"*

---

### `bind_xref`
Bind an XRef into the drawing permanently.

**Example prompts:**
- *"Bind the base plan XRef so I can send a self-contained file to the client"*
- *"Merge the 'SURVEY' XRef into this drawing"*

---

### `xref_clip`
Clip an XRef to a rectangular boundary.

**Example prompts:**
- *"Clip the base plan XRef to show only the apartment area"*
- *"Apply a rectangular clip to the structural XRef from (0,0) to (15000,10000)"*

---

### `list_text_styles`
List all text styles.

**Example prompts:**
- *"What text styles are loaded in this drawing?"*
- *"List all available fonts and text styles"*

---

### `create_text_style`
Create a new text style.

**Example prompts:**
- *"Create a text style called 'ID-STANDARD' using Arial font, height 0, width factor 0.85"*
- *"Add an Isocpeur text style for dimensions"*

---

### `set_active_text_style`
Set the current text style.

**Example prompts:**
- *"Make 'ID-STANDARD' the active text style"*
- *"Switch to the Arial text style"*

---

### `list_dim_styles`
List all dimension styles.

**Example prompts:**
- *"What dim styles are in this drawing?"*
- *"List available dimension styles"*

---

### `create_dim_style`
Create a new dimension style.

**Example prompts:**
- *"Create a dim style 'ID-1:50' with text height 2.5, arrow size 2.5, overall scale 50"*
- *"Set up a dimension style for a 1:100 drawing"*

---

### `set_active_dim_style`
Set the current dimension style.

**Example prompts:**
- *"Switch to dim style 'ID-1:50'"*
- *"Make the 1:100 dimension style current"*

---

### `add_angular_dimension`
Add an angular dimension.

**Example prompts:**
- *"Add an angular dimension between these two lines showing the corner angle"*
- *"Dimension the 45° wall angle"*

---

### `add_diameter_dimension`
Add a diameter dimension.

**Example prompts:**
- *"Add a diameter dimension to the circular column"*
- *"Dimension the ⌀600 table circle"*

---

### `add_ordinate_dimension`
Add an ordinate (datum) dimension.

**Example prompts:**
- *"Add ordinate dimensions from the datum at (0,0) to all wall corners"*
- *"Place ordinate Y-dimensions for the kitchen layout"*

---

### `add_leader`
Add a leader annotation line.

**Example prompts:**
- *"Add a leader from the timber flooring to label it 'ENGINEERED OAK FLOORING'"*
- *"Place an arrow leader pointing to the coffer edge, text: 'RECESSED LED STRIP'"*

---

### `create_table`
Draw an AutoCAD TABLE entity.

**Example prompts:**
- *"Create a 5-column, 10-row table at (0,-2000) for the door schedule"*
- *"Add a materials table with 3 columns and 8 rows"*

---

### `set_table_cell`
Set cell text/value in a table.

**Example prompts:**
- *"Set row 2, column 1 of the table to 'D01'"*
- *"Fill in the header row of the schedule table"*

---

### `get_table_cell`
Read a table cell's value.

**Example prompts:**
- *"What does cell (row 3, col 2) say in the door schedule table?"*
- *"Read the value in the first column, third row"*

---

### `set_table_column_width`
Resize a table column.

**Example prompts:**
- *"Make column 3 of the table 250mm wide"*
- *"Widen the description column to 400mm"*

---

### `set_table_row_height`
Resize a table row.

**Example prompts:**
- *"Set row height to 80mm for all rows in the schedule"*
- *"Make the header row 120mm tall"*

---

## 8. Arrays

### `rectangular_array`
Create a rows × columns array of an entity.

**Example prompts:**
- *"Array the ceiling tile (handle 2A3F) in a 5×8 grid, 600mm spacing each way"*
- *"Copy the downlight symbol in a 4×3 array, 900mm apart"*
- *"Create a 10×10 grid of 600×600mm floor tiles starting at (0,0)"*

---

### `polar_array`
Create a circular/angular array.

**Example prompts:**
- *"Array the dining chair 6 times in a full circle around the table centre at (3000,2000)"*
- *"Place 8 columns in a circular arrangement, radius 3000mm, centred at (0,0)"*
- *"Create a polar array of 12 spotlights around the circular feature ceiling"*

---

### `path_array`
Array objects along a path curve.

**Example prompts:**
- *"Place pendant lights evenly along the curved island bench path"*
- *"Array the balustrade post symbol every 100mm along the staircase path polyline"*
- *"Distribute 6 downlights equally along the corridor centreline"*

---

### `grid_array`
Create a staggered/offset grid array (brick/tile).

**Example prompts:**
- *"Create a staggered brick array of the tile symbol — 4 rows × 10 columns, 50% offset"*
- *"Array the 300×150mm brick tile in a running bond pattern across the feature wall area"*

---

## 9. Interior Spaces

### `setup_id_layers`
Create all 23 AIA standard interior design layers.

**Example prompts:**
- *"Set up all the standard AIA layers for an interior design project"*
- *"Create the full ID layer standard (A-WALL, A-FURN, A-DOOR, etc.)"*
- *"Initialise the drawing with a complete professional layer structure"*

---

### `draw_wall`
Draw a double-line wall with solid hatch.

**Example prompts:**
- *"Draw a 150mm thick wall from (0,0) to (6000,0)"*
- *"Draw a 200mm structural wall along the north boundary"*
- *"Add a 100mm partition wall from (3000,0) to (3000,4000)"*

---

### `draw_room`
Draw a complete 4-wall rectangular room shell.

**Example prompts:**
- *"Draw a 4800×3600mm bedroom starting at (0,0), wall thickness 150mm"*
- *"Create a 3600×2400mm bathroom shell at (5000,0)"*
- *"Draw a living room 6000×4500mm with 150mm walls"*

---

### `add_door`
Add a single-swing door to a wall.

**Example prompts:**
- *"Add a 900mm single door at position (1500,0) on the south wall, opening inward to the left"*
- *"Place a 760mm bedroom door at the wall midpoint, swinging right"*
- *"Add an 800mm door to the bathroom wall"*

---

### `add_double_door`
Add a double leaf door.

**Example prompts:**
- *"Add a 1800mm double door at (3000,0) opening into the living room"*
- *"Place double entry doors 1200mm wide at the front of the apartment"*

---

### `add_sliding_door`
Add a sliding door.

**Example prompts:**
- *"Add a 1800mm sliding door to the wardrobe at (1000,4500)"*
- *"Place a 2400mm sliding glass door to the balcony"*

---

### `add_window`
Add a window in a wall.

**Example prompts:**
- *"Add a 1500mm window centred at (2500,0) on the south wall, sill height 900mm"*
- *"Place a 600×900mm bathroom window at (5500,0)"*
- *"Add floor-to-ceiling glazing 2400mm wide at (1000,6000)"*

---

### `add_opening`
Add a plain opening with no door or frame.

**Example prompts:**
- *"Add a 1200mm opening between the kitchen and dining area at (4000,3000)"*
- *"Create an archway opening 1000mm wide in the living room wall"*

---

### `calculate_room_area`
Calculate area and perimeter from a boundary.

**Example prompts:**
- *"Calculate the floor area of the room with boundary handle 1A2B"*
- *"What is the area and perimeter of this room?"*

---

### `calculate_flooring`
Calculate flooring quantity and wastage.

**Example prompts:**
- *"Calculate how many square metres of timber flooring I need for a 4800×3600mm room with 10% waste"*
- *"How many boxes of 600×600mm tiles do I need for the kitchen floor (3200×2800mm)?"*

---

### `calculate_paint`
Calculate paint quantity for walls and ceiling.

**Example prompts:**
- *"How many litres of paint do I need for a 4800×3600mm room with 2700mm ceiling height?"*
- *"Calculate paint quantity for the master bedroom, 2 coats, spreading rate 12m²/L"*

---

### `tag_room`
Place a room tag with name and number.

**Example prompts:**
- *"Tag the living room at (3000,2000) with name 'LIVING ROOM' and number '101'"*
- *"Add a room tag for the master bathroom at (8500,3000)"*

---

## 10. Furniture

### `place_sofa`
Place a sofa symbol (2- or 3-seat).

**Example prompts:**
- *"Place a 3-seat sofa at (1000,1000), facing north"*
- *"Add a 2200mm wide 3-seater sofa against the south wall"*
- *"Place a 2-seat sofa at (3000,2000) rotated 90°"*

---

### `place_chair`
Place a dining or occasional chair.

**Example prompts:**
- *"Place a chair at (2000,1500) facing the dining table"*
- *"Add 4 dining chairs around the table"*

---

### `place_armchair`
Place an armchair with side tables.

**Example prompts:**
- *"Place an armchair at (500,500) with side table, facing the TV"*
- *"Add two armchairs flanking the fireplace at (2000,100)"*

---

### `place_dining_table`
Place a dining table with chairs auto-placed.

**Example prompts:**
- *"Place a 1600×900mm dining table at (4000,2000) with 6 chairs"*
- *"Add an 8-seat 2400×1000mm dining table in the dining zone"*
- *"Place a round 1200mm diameter dining table with 4 chairs at the bay window"*

---

### `place_coffee_table`
Place a coffee table (round or rectangular).

**Example prompts:**
- *"Place a 1200×600mm rectangular coffee table in front of the sofa at (1500,1800)"*
- *"Add a round 800mm coffee table at (2000,1500)"*

---

### `place_desk`
Place a desk (straight or L-shape).

**Example prompts:**
- *"Place a 1500×750mm straight desk at (500,500) in the study"*
- *"Add an L-shaped 1800×1800mm desk in the home office corner at (0,0)"*

---

### `place_bed`
Place a bed (all standard sizes).

**Example prompts:**
- *"Place a king-size bed centred in the master bedroom against the north wall"*
- *"Add a queen bed at (500,500) with headboard against the wall, rotated 90°"*
- *"Place a single bed in the guest room at (200,200)"*

---

### `place_wardrobe`
Place a wardrobe with doors.

**Example prompts:**
- *"Place a 2400×600mm built-in wardrobe at (0,0) with sliding doors"*
- *"Add a 1800mm walk-in wardrobe opening on the east wall"*

---

### `place_bookshelf`
Place a bookshelf.

**Example prompts:**
- *"Place a 1200×300mm bookshelf at (4500,0) against the wall"*
- *"Add floor-to-ceiling shelving 1800mm wide in the study"*

---

### `place_kitchen_unit`
Place a kitchen unit (base, sink, hob, or corner).

**Example prompts:**
- *"Place a 600mm base unit at (0,0)"*
- *"Add a 1000mm sink unit to the kitchen run at (600,0)"*
- *"Place an induction hob unit at (1200,0)"*
- *"Add a corner unit at the kitchen junction point (3000,0)"*

---

### `place_toilet`
Place a WC symbol.

**Example prompts:**
- *"Place a toilet at (300,200) in the bathroom, facing south"*
- *"Add a WC to the en-suite at (500,100)"*

---

### `place_bath`
Place a bathtub.

**Example prompts:**
- *"Place a 1700mm freestanding bath centred in the bathroom"*
- *"Add a built-in 1800×800mm bath at (0,0) in the main bathroom"*

---

### `place_sink`
Place a basin/sink.

**Example prompts:**
- *"Place a 600mm vanity basin at (1000,0) in the bathroom"*
- *"Add a round vessel sink at (800,0)"*

---

### `place_shower`
Place a shower tray/enclosure.

**Example prompts:**
- *"Place a 900×900mm shower at (0,1500) in the corner of the ensuite"*
- *"Add a 1200×800mm shower tray to the wet room"*

---

### `place_light_downlight`
Place a downlight ceiling symbol.

**Example prompts:**
- *"Place a downlight symbol at (1500,1500) on the RCP layer"*
- *"Add 6 downlights in a 2×3 grid across the living room ceiling"*

---

### `place_light_pendant`
Place a pendant light symbol.

**Example prompts:**
- *"Place a pendant light symbol above the dining table at (4000,2500)"*
- *"Add 3 pendant lights in a row over the kitchen island"*

---

### `place_power_outlet`
Place a basic power outlet symbol (furniture module).

**Example prompts:**
- *"Add a power outlet near the bedside at (1800,300)"*
- *"Place a double outlet on each side of the desk"*

---

## 11. Schedules

### `create_room_schedule`
Create a room schedule table.

**Example prompts:**
- *"Create a room schedule listing all rooms with their floor area, floor finish, and ceiling finish"*
- *"Generate a room data table for the apartment showing room names, areas, and paint references"*

---

### `create_door_schedule`
Create a door schedule table.

**Example prompts:**
- *"Create a door schedule for this drawing with columns for mark, width, height, type, and finish"*
- *"Generate a door schedule showing all D01–D08 entries"*

---

### `create_window_schedule`
Create a window schedule table.

**Example prompts:**
- *"Generate a window schedule with size, glazing type, and frame material columns"*
- *"Create a window schedule for the apartment at (0,-3000) below the plan"*

---

### `create_ffe_schedule`
Create an FF&E (furniture, fixtures, equipment) schedule.

**Example prompts:**
- *"Create an FF&E schedule table listing all furniture items with quantity, supplier, and product code"*
- *"Generate an FF&E schedule for the living and dining areas"*

---

### `create_material_legend`
Create a material legend with hatch swatches.

**Example prompts:**
- *"Create a materials legend with hatch swatches for: timber flooring, polished concrete, carpet, marble tiles"*
- *"Add a finish legend at the bottom of the drawing with colour codes and descriptions"*

---

### `create_revision_table`
Create a revision history table.

**Example prompts:**
- *"Create a revision table in the title block area"*
- *"Add a revision schedule showing Rev A, Rev B, Rev C with dates and descriptions"*

---

## 12. ID Annotations

### `add_elevation_marker`
Place an elevation marker with direction indicator.

**Example prompts:**
- *"Add an elevation marker at (3000,3000), pointing north, labelled 'ELEVATION A'"*
- *"Place elevation markers on all 4 walls of the living room"*
- *"Add an interior elevation tag at the feature wall, reference 'E-01'"*

---

### `add_section_marker`
Add a section cut reference bubble.

**Example prompts:**
- *"Place a section marker at (0,3000) cutting through the kitchen, labelled 'SECTION A-A' on sheet 3"*
- *"Add a longitudinal section marker across the full apartment"*

---

### `add_detail_bubble`
Add a detail reference bubble.

**Example prompts:**
- *"Add a detail bubble at the door frame junction, reference 'DET-01/A3'"*
- *"Place a detail callout at the coffer edge condition"*

---

### `add_material_callout`
Add a material callout with leader arrow.

**Example prompts:**
- *"Add a material callout pointing to the kitchen countertop: 'CAESARSTONE CALACATTA NUVO 40mm'"*
- *"Label the timber flooring with a leader: 'ENGINEERED OAK, HERRINGBONE PATTERN'"*
- *"Add callouts for all wall finishes in the bathroom elevation"*

---

### `add_north_arrow`
Place a north arrow symbol.

**Example prompts:**
- *"Place a north arrow at the top-right of the drawing, pointing true north at 15° from vertical"*
- *"Add a north arrow symbol to the floor plan"*

---

### `add_scale_bar`
Place a graphic scale bar.

**Example prompts:**
- *"Add a 5000mm scale bar below the floor plan, subdivided into 5×1000mm segments"*
- *"Place a scale bar for a 1:50 drawing showing 0–2500mm"*

---

### `add_revision_cloud`
Draw a revision cloud around an area.

**Example prompts:**
- *"Add a revision cloud around the kitchen area showing the latest changes, tag it 'Rev B'"*
- *"Draw a revision cloud around the bathroom layout revision"*

---

### `add_grid_lines`
Add structural grid lines with bubble labels.

**Example prompts:**
- *"Add a structural grid: 4 vertical lines at 3000mm spacing (A–D) and 3 horizontal lines at 4000mm spacing (1–3)"*
- *"Place grid bubbles A through F horizontally and 1 through 4 vertically"*

---

### `add_dimension_chain`
Add a chained string of linear dimensions.

**Example prompts:**
- *"Add a dimension chain along the south wall showing all door and window positions"*
- *"Create a dimension string for the kitchen run: 600 + 600 + 1000 + 600 = 2800mm"*
- *"Dimension all room widths in a single chain along the bottom of the floor plan"*

---

## 13. Interior Advanced

### `draw_l_shaped_room`
Draw an L-shaped room.

**Example prompts:**
- *"Draw an L-shaped living/dining room: main area 6000×5000, notch cut-out 2000×2000 from the top-right corner"*
- *"Create an L-shaped open plan space with an alcove for the study"*

---

### `draw_custom_room`
Draw any polygon-shaped room.

**Example prompts:**
- *"Draw a custom 5-sided room through points (0,0), (5000,0), (6000,2000), (5000,4000), (0,4000)"*
- *"Create a hexagonal dining room, 3000mm radius"*
- *"Draw the irregular-shaped boutique floor plan from these boundary coordinates"*

---

### `draw_rcp_room`
Draw a Reflected Ceiling Plan base.

**Example prompts:**
- *"Draw the RCP for a 4800×3600mm bedroom, ceiling height 2700mm"*
- *"Set up the reflected ceiling plan base for the open plan living area"*

---

### `draw_coffer`
Draw a coffered ceiling rectangle.

**Example prompts:**
- *"Add a 3000×2000mm coffered ceiling inset 300mm from the room edges in the master bedroom"*
- *"Draw a series of 3 coffered panels across the dining room ceiling"*

---

### `draw_bulkhead`
Draw a ceiling bulkhead.

**Example prompts:**
- *"Add a 400mm deep bulkhead along the kitchen side of the open plan area"*
- *"Draw a perimeter bulkhead 350mm wide and 400mm drop around the living room"*

---

### `calculate_downlight_layout`
Calculate optimal downlight grid spacing.

**Example prompts:**
- *"Calculate the best downlight layout for a 4800×3600mm room, aiming for 400 lux"*
- *"How should I space downlights in a 6000×4000mm living room with 2800mm ceiling height?"*

---

### `draw_downlight_layout`
Place downlight symbols on an RCP.

**Example prompts:**
- *"Draw the downlight layout for the 4800×3600mm living room with 6 lights in a 2×3 grid"*
- *"Place 8 downlights automatically across the kitchen ceiling"*

---

### `draw_wall_elevation`
Draw an interior wall elevation.

**Example prompts:**
- *"Draw the north wall elevation of the master bedroom, 4800mm wide, 2700mm high"*
- *"Create the kitchen east elevation showing all wall units and splashback"*

---

### `add_window_to_elevation`
Add a window opening to an elevation.

**Example prompts:**
- *"Add a 1500×1200mm window at 900mm sill height to the bedroom elevation, centred at 2400mm from the left"*
- *"Place a floor-to-ceiling glazed opening in the living room elevation"*

---

### `draw_tile_layout` *(interior_advanced version)*
Draw a basic grid/offset/diagonal tile pattern.

**Example prompts:**
- *"Draw a 600×600mm tile grid on the bathroom floor area"*
- *"Show a 300×150mm brick bond tile layout on the kitchen splashback"*

---

### `draw_skirting_boards`
Draw skirting boards with door deductions.

**Example prompts:**
- *"Draw 100mm skirting boards around the perimeter of the living room, with deductions for the 3 doorways"*
- *"Add skirting to the bedroom boundary, leaving gaps at the door positions"*

---

### `draw_staircase`
Draw a stair flight with break line and arrow.

**Example prompts:**
- *"Draw a 1000mm wide staircase from (0,0) going up north, 13 treads at 250mm going, 175mm rise"*
- *"Add an up-stair from the ground floor hallway to the first floor"*

---

### `draw_kitchen_layout`
Draw a complete kitchen in one of 5 layouts.

**Example prompts:**
- *"Draw a galley kitchen 3600mm long in the 2400×3600mm kitchen zone"*
- *"Create an L-shaped kitchen in the 4000×3500mm space"*
- *"Design a U-shaped kitchen with island for the 6000×5000mm open plan"*
- *"Draw a peninsula kitchen layout — open plan with breakfast bar"*

---

### `draw_bathroom_layout`
Draw a complete bathroom layout.

**Example prompts:**
- *"Draw a standard bathroom layout (bath + WC + basin) in a 2400×1800mm space"*
- *"Create an ensuite layout (shower + WC + vanity) in 1800×2400mm"*
- *"Design a wet-room bathroom for the 2000×2000mm space"*

---

### `analyse_circulation_space`
Analyse minimum clearance circulation paths.

**Example prompts:**
- *"Check if there's adequate circulation space in the bedroom layout — minimum 600mm around the bed"*
- *"Analyse the kitchen corridor width between the island and base units"*

---

### `generate_room_data_tag`
Generate a comprehensive room data tag.

**Example prompts:**
- *"Generate a full room data tag for the master bedroom: floor timber, ceiling white, walls paint, area 18m²"*
- *"Create a room data tag for the kitchen showing all finishes and services"*

---

## 14. Match Properties

### `match_properties`
Copy all properties from one entity to another (MATCHPROP).

**Example prompts:**
- *"Match the properties of entity 2A3F (source) to entities 3B4C, 4C5D, 5D6E"*
- *"Copy the layer, colour, and linetype from the wall entity to all these new lines"*
- *"Match the door symbol's properties to all instances in the drawing"*

---

### `match_properties_by_type`
Match properties across all entities of a given type.

**Example prompts:**
- *"Make all text entities in the drawing match the properties of entity 1A2B"*
- *"Apply the source hatch entity's properties to every hatch in the drawing"*

---

### `match_layer_only`
Copy only the layer from source to target entities.

**Example prompts:**
- *"Move entity 5D6E to the same layer as entity 1A2B without changing other properties"*
- *"Match just the layer from the source entity to these 5 wall lines"*

---

### `match_color_only`
Copy only the colour from source to targets.

**Example prompts:**
- *"Make all these entities the same colour as entity 2A3F"*
- *"Copy just the colour from the reference entity"*

---

### `match_hatch_properties`
Copy hatch pattern, scale, and angle between hatches.

**Example prompts:**
- *"Make the floor hatch (handle 7G8H) match the pattern and scale of the reference hatch (handle 1A2B)"*
- *"Copy the timber hatch settings to all other floor areas"*

---

### `match_text_style_across_drawing`
Apply a text style to all text in the drawing.

**Example prompts:**
- *"Set all text in the drawing to match the text style of entity ABC1"*
- *"Standardise all text to use the ID-STANDARD style"*

---

### `match_dim_style_across_drawing`
Apply a dimension style to all dimensions.

**Example prompts:**
- *"Apply the ID-1:50 dim style to every dimension in the drawing"*
- *"Standardise all dimensions to use the correct style for this scale"*

---

### `set_properties_by_layer`
Force entities to use ByLayer properties.

**Example prompts:**
- *"Reset all entities on layer A-FURN to use ByLayer colour and linetype"*
- *"Clean up the drawing — set everything to ByLayer on all annotation layers"*

---

### `copy_entity_properties_to_new`
Create a copy of an entity with identical properties.

**Example prompts:**
- *"Clone entity 2A3F with exactly the same layer, colour, and linetype"*
- *"Copy this wall segment and maintain all its properties"*

---

### `audit_property_consistency`
Find entities with non-standard property overrides.

**Example prompts:**
- *"Check which entities have colour overrides instead of ByLayer"*
- *"Audit the drawing for any non-standard linetype assignments"*
- *"Find all entities where colour or lineweight is not set to ByLayer"*

---

### `reset_entity_properties_to_bylayer`
Reset colour, linetype, and lineweight to ByLayer.

**Example prompts:**
- *"Reset entity 5D6E back to ByLayer for all properties"*
- *"Clean up these imported entities — reset everything to ByLayer"*

---

## 15. Images

### `attach_image`
Attach a raster image (PNG/JPG/TIF) to the drawing.

**Example prompts:**
- *"Attach the site photo from C:\Photos\site_01.jpg at position (0,0), scale 1:1"*
- *"Import the client's reference image into the drawing"*

---

### `attach_reference_image`
Attach an image as a scaled reference overlay.

**Example prompts:**
- *"Attach the scanned survey as a background reference, scaled so 1px = 1mm"*
- *"Overlay the client's hand-drawn sketch at position (0,0) for tracing"*

---

### `list_images`
List all attached images in the drawing.

**Example prompts:**
- *"What images are attached to this drawing?"*
- *"Show me all raster images with their paths and positions"*

---

### `get_image_info`
Get path, scale, position, and clip state of an image.

**Example prompts:**
- *"Tell me about the image with handle 3C4D — where is it and what's its scale?"*
- *"Is the main reference image still linked to the correct file path?"*

---

### `set_image_brightness`
Adjust image brightness.

**Example prompts:**
- *"Make the reference image brighter (brightness 70) so it doesn't compete with linework"*
- *"Reduce the background photo brightness to 30%"*

---

### `set_image_contrast`
Adjust image contrast.

**Example prompts:**
- *"Increase the contrast on the mood board image"*
- *"Set image handle 3C4D contrast to 60"*

---

### `set_image_fade`
Adjust image fade (transparency blend).

**Example prompts:**
- *"Fade the reference image to 70% so the drawing lines are clearer"*
- *"Set all background images to 50% fade"*

---

### `set_image_transparency`
Toggle transparency on/off for images with white background.

**Example prompts:**
- *"Turn on transparency for the PNG material sample so the white background disappears"*
- *"Enable transparency on all attached images"*

---

### `toggle_image_frame`
Show or hide a specific image frame.

**Example prompts:**
- *"Hide the frame around the mood board image"*
- *"Show the border frame for the reference image"*

---

### `set_all_image_frames`
Batch show/hide frames for all images.

**Example prompts:**
- *"Hide all image frames before printing"*
- *"Turn on frames for all attached images so I can see their boundaries"*

---

### `clip_image_rectangular`
Clip an image to a rectangular boundary.

**Example prompts:**
- *"Clip the site photo to show only the area from (500,500) to (3000,2500)"*
- *"Crop the reference image to just the kitchen zone"*

---

### `clip_image_polygon`
Clip an image to a polygon boundary.

**Example prompts:**
- *"Clip the aerial photo to the irregular site boundary shape"*
- *"Trim the material image to the L-shaped splashback outline"*

---

### `remove_image_clip`
Remove the clipping boundary from an image.

**Example prompts:**
- *"Remove the clip from image handle 5E6F to show the full image again"*
- *"Unclip the background reference image"*

---

### `reload_image`
Reload an image from disk.

**Example prompts:**
- *"Reload the mood board image — I've updated the source file"*
- *"Refresh all images from their source files"*

---

### `unload_image`
Unload an image (keep reference, hide display).

**Example prompts:**
- *"Unload the large site photo to speed up the drawing"*
- *"Temporarily hide the background images without detaching them"*

---

### `detach_image`
Fully remove an image from the drawing.

**Example prompts:**
- *"Detach and remove the draft reference image"*
- *"Delete all attached images before sending the drawing to the contractor"*

---

### `update_image_path`
Relink an image to a new file path.

**Example prompts:**
- *"The project has moved — relink the site photo to D:\NewProject\Photos\site_01.jpg"*
- *"Fix the broken image link for the mood board JPG"*

---

### `create_material_image_board`
Arrange multiple images as a material sample board.

**Example prompts:**
- *"Create a material board from these 6 image files: marble.jpg, oak.jpg, brass.jpg, linen.jpg, plaster.jpg, glass.jpg — 3 columns, placed at (0,0)"*
- *"Layout a materials reference board in the drawing with all finish samples"*

---

### `create_mood_board_layout`
Arrange images in a mood board grid.

**Example prompts:**
- *"Create a mood board from these 9 inspiration images in a 3×3 grid"*
- *"Arrange the 6 client reference photos in a mood board layout for the presentation"*

---

## 16. Geometric Construction

### `draw_regular_polygon`
Draw a 3–12 sided regular polygon.

**Example prompts:**
- *"Draw a regular hexagon centred at (3000,3000), circumscribed radius 800mm"*
- *"Construct a regular octagon at (0,0), inscribed radius 1000mm"*
- *"Draw a pentagon with 500mm radius, rotated 18°, on the A-GEOM layer"*

---

### `draw_polygon_by_edge`
Construct a polygon from a known edge.

**Example prompts:**
- *"Draw a regular hexagon where one edge goes from (0,0) to (600,0)"*
- *"Construct an equilateral triangle from the edge between (1000,0) and (1600,0)"*
- *"Build a regular pentagon starting from the 500mm base edge"*

---

### `draw_isometric_grid`
Draw an isometric construction grid.

**Example prompts:**
- *"Set up an isometric grid at (0,0), 200mm spacing, covering a 3000×3000mm area"*
- *"Draw an isometric drawing grid for the axonometric furniture sketch"*
- *"Place a 100mm isometric grid as construction lines for the 3D concept sketch"*

---

### `setup_orthographic_layout`
Draw a 3-view orthographic projection frame.

**Example prompts:**
- *"Set up an orthographic 3-view layout with 600×600mm view boxes and 50mm gaps"*
- *"Create the plan/front/side elevation projection frame for the cabinet drawing"*
- *"Set up orthographic views for the custom joinery piece: width 1200mm, height 900mm"*

---

### `draw_section_cut_line`
Draw a section cutting-plane line.

**Example prompts:**
- *"Draw a section cut line across the kitchen from (0,3000) to (8000,3000), label 'A'"*
- *"Add a cross-section marker through the staircase, label 'B-B'"*
- *"Place a longitudinal section cut along the apartment from left to right"*

---

### `hatch_section_cut`
Apply architectural material hatch to a cross-section.

**Example prompts:**
- *"Hatch the wall section boundary with a concrete pattern"*
- *"Apply brick hatch to the wall cross-section shape (handle 2A3F)"*
- *"Fill the structural slab section with a steel hatch pattern"*

---

### `draw_scale_comparison`
Draw an object at multiple scales side by side.

**Example prompts:**
- *"Draw the 4800mm room at scales 1:20, 1:50, 1:100, and 1:200 for scale study"*
- *"Show the door symbol at 5 different scales for the scale drawing assignment"*

---

### `draw_golden_ratio_rectangle`
Draw a golden ratio rectangle with spiral.

**Example prompts:**
- *"Draw a golden ratio rectangle 2000mm wide at (0,0) with 5 internal subdivisions and the spiral overlay"*
- *"Show the golden ratio proportions for a feature wall 3600mm wide"*
- *"Draw a Fibonacci spiral analysis for the living room composition (6000mm wide)"*

---

### `setup_one_point_perspective`
Set up a 1-point perspective grid.

**Example prompts:**
- *"Set up a 1-point perspective grid 4000mm wide, horizon at 1620mm (eye level), vanishing point centred"*
- *"Create a 1-point perspective template for the living room interior sketch"*
- *"Draw a one-point perspective grid with 10 depth lines for the corridor rendering"*

---

### `setup_two_point_perspective`
Set up a 2-point perspective grid.

**Example prompts:**
- *"Set up a 2-point perspective with VP-left at x=-3000 and VP-right at x=8000, horizon at 1620mm"*
- *"Create a 2-point perspective grid for the corner view of the master bedroom"*
- *"Draw a 2-point perspective template for the exterior corner elevation sketch"*

---

### `draw_prism_surface_development`
Draw the unfolded net of a regular prism.

**Example prompts:**
- *"Draw the surface development of a square prism, edge 600mm, height 900mm"*
- *"Unfold a hexagonal prism, edge 300mm, height 600mm, with top and bottom faces"*
- *"Draw the net of a triangular prism for the model making assignment"*

---

### `draw_pyramid_surface_development`
Draw the unfolded net of a pyramid.

**Example prompts:**
- *"Draw the surface development of a square pyramid, base edge 400mm, slant height 500mm"*
- *"Unfold a hexagonal pyramid with 200mm base edge and 350mm slant height"*
- *"Create the pyramid net for the model of the roof form"*

---

## 17. Anthropometry

### `draw_human_figure`
Draw a schematic human figure.

**Example prompts:**
- *"Draw a standing human figure at (1500,0) facing right, full scale, on the A-FURN-HUMAN layer"*
- *"Add a seated person figure at the desk position for scale reference"*
- *"Place a wheelchair user figure in the accessible bathroom layout"*
- *"Show a child figure next to the kitchen counter for scale comparison"*

---

### `draw_human_reach_zone`
Draw comfortable and maximum reach zones.

**Example prompts:**
- *"Show the standing reach zone in plan view centred at (3000,1500)"*
- *"Draw a reach zone diagram in elevation at the kitchen counter position"*
- *"Add reach zone arcs to the bathroom vanity for accessibility analysis"*

---

### `draw_clearance_zone`
Draw a furniture item with ergonomic clearances.

**Example prompts:**
- *"Draw a 1600×900mm bed at (500,500) with the required 600mm clearances shown around it"*
- *"Show the dining table at (3000,2000) with chair pull-out clearances marked"*
- *"Draw a desk at (0,0) with the 900mm knee clearance zone in front"*
- *"Show toilet clearance zones (460mm either side) for the bathroom layout"*

---

### `draw_wheelchair_turning_circle`
Draw a 1500mm ADA turning circle.

**Example prompts:**
- *"Draw a wheelchair turning circle centred in the accessible bathroom at (1200,1200)"*
- *"Check that the lift lobby has enough room — draw the 1500mm turning circle at (2000,2000)"*
- *"Add the ADA turning circle to the accessible toilet layout"*

---

### `draw_corridor_standard`
Draw a corridor with standard width annotations.

**Example prompts:**
- *"Draw a 1200mm comfortable corridor 4500mm long from (0,0) going horizontally"*
- *"Show an accessible 1500mm corridor with dimension annotations"*
- *"Draw a standard 900mm minimum residential corridor for the plan"*

---

### `check_space_compliance`
Check room dimensions against space standards.

**Example prompts:**
- *"Check if my 2800×2600mm bedroom meets the minimum space standards"*
- *"Is a 1500×900mm bathroom compliant with minimum requirements?"*
- *"Validate the 3200×2800mm kitchen against ergonomic standards"*
- *"Check if my home office (2400×2100mm) meets workstation space requirements"*

---

### `draw_kitchen_work_triangle`
Draw and analyse the kitchen work triangle.

**Example prompts:**
- *"Analyse the kitchen work triangle: sink at (500,3000), hob at (3000,3000), fridge at (500,500)"*
- *"Check if my kitchen layout has a compliant work triangle — sink (1000,2500), cooktop (3500,2500), fridge (200,500)"*
- *"Draw the work triangle and tell me if the legs are within the 1200–2700mm guidelines"*

---

### `draw_ergonomic_dimensions_table`
Draw a reference dimensions table in the drawing.

**Example prompts:**
- *"Add a kitchen ergonomic dimensions reference table to the drawing at (0,-3000)"*
- *"Place a seating ergonomics reference table next to the furniture layout"*
- *"Draw a complete ergonomic dimensions table showing all standard heights"*

---

### `draw_elevation_height_standards`
Draw all standard height reference lines in an elevation.

**Example prompts:**
- *"Draw elevation height reference lines for the 4800mm wide living room wall"*
- *"Set up standard height guidelines (floor, switch, counter, eye level, ceiling) for the kitchen elevation"*
- *"Add all ergonomic reference lines to the bathroom elevation with a human figure for scale"*

---

## 18. MEP Services

### `place_power_outlet`
Place a power outlet symbol.

**Example prompts:**
- *"Place a double power outlet at (2500,300) on the south wall, 300mm AFF"*
- *"Add GFCI outlets near the kitchen sink at (1200,900)"*
- *"Place a floor outlet in the centre of the boardroom floor at (3000,3000)"*
- *"Add a data+power outlet at the desk position, 700mm AFF"*

---

### `place_light_switch`
Place a light switch symbol.

**Example prompts:**
- *"Place a double light switch at (100,1200) by the bedroom entrance, 1200mm AFF"*
- *"Add a dimmer switch for the living room at (200,1200)"*
- *"Place 2-way switches at both ends of the corridor"*

---

### `draw_electrical_circuit`
Draw an electrical circuit run.

**Example prompts:**
- *"Draw a lighting circuit from the switch at (100,1200) to each of the 6 downlights"*
- *"Show the power circuit run from the distribution board through all kitchen outlets"*
- *"Draw a dedicated circuit line for the oven at (3000,3500)"*

---

### `draw_electrical_panel`
Draw a distribution board with circuit schedule.

**Example prompts:**
- *"Draw the main distribution board at (0,0) with 8 circuits: 4 lighting, 3 power, 1 AC dedicated"*
- *"Create an electrical panel schedule for the apartment with all circuit details"*
- *"Place the MDB symbol with a full circuit schedule table listing each zone"*

---

### `draw_plumbing_symbol`
Place a standard plumbing symbol.

**Example prompts:**
- *"Place a floor drain symbol at the lowest point of the wet room (2000,1000)"*
- *"Add a gate valve to the cold water supply at (500,200)"*
- *"Place a cleanout access point at (100,100) in the utility area"*
- *"Add a water heater symbol in the plant room at (500,500)"*

---

### `draw_pipe_run`
Draw a pipe run with type coding.

**Example prompts:**
- *"Draw a cold water supply pipe from (0,200) to (5000,200) to (5000,3000) in 15mm"*
- *"Show the waste pipe run from the bathroom at (3000,2000) to the stack at (0,2000)"*
- *"Draw a hot water pipe branch from the HW main to the bathroom vanity"*

---

### `draw_wet_room_plumbing`
Draw a complete wet room plumbing layout.

**Example prompts:**
- *"Draw a standard bathroom plumbing layout in a 2400×1800mm space at (0,0)"*
- *"Show the ensuite plumbing for a 1800×2400mm space at (5000,0)"*
- *"Create the plumbing plan for the open wet-room bathroom, 2000×2000mm"*
- *"Draw kitchen plumbing layout with sink and dishwasher"*

---

### `place_ac_unit`
Place an AC unit symbol.

**Example prompts:**
- *"Place a split system indoor unit on the north wall at (2400,2600), 800mm wide"*
- *"Add a cassette unit to the living room ceiling at the centrepoint"*
- *"Show the outdoor condensing unit on the balcony at (0,2000)"*

---

### `draw_ac_diffuser`
Draw an HVAC diffuser or grille.

**Example prompts:**
- *"Place a 300×300mm square supply air diffuser at each downlight position in the ceiling"*
- *"Add a round diffuser at (2000,2000) with 400CFM airflow"*
- *"Draw linear diffusers along the perimeter of the open plan ceiling"*

---

### `draw_ductwork`
Draw rectangular ductwork runs.

**Example prompts:**
- *"Draw a 400mm wide supply duct from the AHU at (0,0) to the first diffuser at (3000,0) then to (6000,0)"*
- *"Show the return air ductwork run from the grilles back to the plant room"*
- *"Draw the exhaust duct from the bathroom to the external wall at 200mm wide"*

---

### `place_smoke_detector`
Place a fire/safety detection symbol.

**Example prompts:**
- *"Place smoke detectors in every room at the ceiling centre points"*
- *"Add sprinkler heads on a 3000×3000mm grid across the office ceiling"*
- *"Place an emergency light at each exit door and at corridor intersections"*
- *"Add a pull station at the apartment entry at (200,1200)"*

---

### `draw_services_legend`
Draw a services symbol legend.

**Example prompts:**
- *"Add a complete MEP services legend to the bottom-right of the drawing"*
- *"Create a symbol key showing all electrical, plumbing, and HVAC symbols used"*
- *"Draw a legend for just the electrical symbols at (0,-2000)"*

---

## 19. Tile Design

### `draw_tile_grid`
Lay a standard rectangular tile grid.

**Example prompts:**
- *"Lay 600×600mm floor tiles across the 4800×3600mm living room, centred"*
- *"Draw a 300×300mm tile grid on the bathroom floor, starting from the corner"*
- *"Tile the kitchen with 600×300mm tiles, offset from the centre, with 3mm grout"*
- *"Create a checkerboard tile pattern using two alternating hatches in the hallway"*

---

### `draw_tile_running_bond`
Lay tiles in a running/offset bond.

**Example prompts:**
- *"Lay 600×300mm tiles in a 50% running bond across the feature wall (3600×2700mm)"*
- *"Draw a brick-bond tile pattern on the kitchen splashback, 300×100mm tiles"*
- *"Create a 1/3 offset bond with 900×300mm plank tiles on the living room floor"*

---

### `draw_tile_herringbone`
Lay tiles in a herringbone pattern.

**Example prompts:**
- *"Draw a 45° herringbone pattern with 600×300mm tiles in the hallway (1200×4500mm)"*
- *"Lay a straight (90°) herringbone pattern in the master bedroom"*
- *"Show a diagonal herringbone tile layout centred on the bathroom floor"*

---

### `draw_tile_chevron`
Lay tiles in a true chevron pattern.

**Example prompts:**
- *"Draw a chevron tile pattern with 600×150mm tiles across the 3600×2400mm feature wall"*
- *"Show how 300×75mm tiles look in a chevron layout on the bathroom floor"*
- *"Create a chevron pattern for the narrow hallway to maximise the sense of length"*

---

### `draw_tile_basket_weave`
Lay tiles in a basket weave pattern.

**Example prompts:**
- *"Draw a 2×1 basket weave pattern with 300×150mm tiles on the bathroom floor (2400×1800mm)"*
- *"Create a basket weave layout in the sunroom using 200×200mm square tiles"*

---

### `draw_tile_versailles`
Lay a Versailles/French/Opus Romanum pattern.

**Example prompts:**
- *"Draw a Versailles stone pattern with 300mm module across the entrance lobby"*
- *"Create a French pattern tile layout in the 5000×4000mm living area"*
- *"Show the Opus Romanum layout for the terrazzo-effect tiles in the kitchen"*

---

### `draw_tile_diagonal`
Lay square tiles on the 45° diagonal.

**Example prompts:**
- *"Draw 400×400mm tiles on the diagonal (45°) in the bathroom"*
- *"Show a diamond tile layout with 300×300mm tiles centred on the room"*
- *"Create a diagonal grid for the entrance hall to make the space feel wider"*

---

### `draw_tile_custom_repeat`
Lay tiles using a user-defined looping cell.

**Example prompts:**
- *"Create a custom tile repeat: cell 630×630mm, containing a 300×300mm centre tile at (165,165), and four 150×300mm tiles on each side"*
- *"Draw a pinwheel pattern using a custom 4-tile cell, 200mm module"*
- *"Create a pattern with a feature mosaic tile surrounded by plain tiles using a custom repeat cell"*

---

### `draw_tile_border_strip`
Draw a border or feature strip.

**Example prompts:**
- *"Add a 200mm wide border strip of 200×50mm feature tiles around all 4 sides of the bathroom floor"*
- *"Draw a decorative border band along the bottom of the shower wall at floor level"*
- *"Add a feature tile strip just on the south wall side of the room"*

---

### `calculate_tile_waste`
Calculate tile quantities, waste, and cost.

**Example prompts:**
- *"How many 600×600mm tiles do I need for a 4800×3600mm room with 10% waste?"*
- *"Calculate the tiles needed for a herringbone pattern in the hallway (1200×4500mm), 300×150mm tiles"*
- *"Give me a full tile quantity breakdown: 600×300mm tiles, running bond, 5000×4000mm space, $85/m², include cost estimate"*

---

### `draw_tile_zones`
Draw multiple tile zones with different patterns.

**Example prompts:**
- *"Split the bathroom into two zones: wet area with 200×200mm mosaic tiles, dry area with 600×600mm large format tiles"*
- *"Create a kitchen tile plan with 3 zones: herringbone floor (600×300mm), grid splashback (100×100mm), feature wall (long plank 900×150mm)"*
- *"Draw the entrance lobby with a diamond tile centre panel and grid border zone"*

---

---

*Total: 226 tools across 19 modules*
*Repository: https://github.com/kbatavia12/autocad-mcp*
