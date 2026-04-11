"""
test_all_tools.py
Runs every registered MCP tool against a live AutoCAD session and reports
PASS / FAIL for each one. Run with AutoCAD open and a drawing active.

Usage:
    venv\Scripts\python.exe test_all_tools.py
    venv\Scripts\python.exe test_all_tools.py --stop-on-fail
"""

import sys
import traceback
import argparse


# ---------------------------------------------------------------------------
# Mock FastMCP — captures registered tool functions so we can call them
# ---------------------------------------------------------------------------
class MockMCP:
    def __init__(self):
        self._tools = {}

    def tool(self):
        def decorator(fn):
            self._tools[fn.__name__] = fn
            return fn
        return decorator


# ---------------------------------------------------------------------------
# Register all tool modules against the mock
# ---------------------------------------------------------------------------
mcp = MockMCP()

from tools.drawing               import register_drawing_tools
from tools.layers                import register_layer_tools
from tools.objects               import register_object_tools
from tools.files                 import register_file_tools
from tools.query                 import register_query_tools
from tools.layouts               import register_layout_tools
from tools.blocks_xrefs_styles   import register_blocks_xrefs_styles_tools
from tools.arrays                import register_array_tools
from tools.interior_spaces       import register_interior_space_tools
from tools.furniture             import register_furniture_tools
from tools.schedules             import register_schedule_tools
from tools.id_annotations        import register_id_annotation_tools
from tools.interior_advanced     import register_interior_advanced_tools
from tools.match_properties      import register_match_properties_tools
from tools.images                import register_image_tools
from tools.geometric_construction import register_geometric_construction_tools
from tools.anthropometry         import register_anthropometry_tools
from tools.mep_services          import register_mep_services_tools
from tools.tile_design           import register_tile_design_tools

register_drawing_tools(mcp)
register_layer_tools(mcp)
register_object_tools(mcp)
register_file_tools(mcp)
register_query_tools(mcp)
register_layout_tools(mcp)
register_blocks_xrefs_styles_tools(mcp)
register_array_tools(mcp)
register_interior_space_tools(mcp)
register_furniture_tools(mcp)
register_schedule_tools(mcp)
register_id_annotation_tools(mcp)
register_interior_advanced_tools(mcp)
register_match_properties_tools(mcp)
register_image_tools(mcp)
register_geometric_construction_tools(mcp)
register_anthropometry_tools(mcp)
register_mep_services_tools(mcp)
register_tile_design_tools(mcp)


# ---------------------------------------------------------------------------
# Test cases: (tool_name, kwargs)
# All coordinates use a 10000×8000mm working area so nothing overlaps badly.
# ---------------------------------------------------------------------------
TESTS = [
    # ── drawing ──────────────────────────────────────────────────────────────
    ("draw_line",           dict(x1=0, y1=0, x2=1000, y2=0)),
    ("draw_polyline",       dict(points_flat=[0,100, 500,100, 500,600], closed=False)),
    ("draw_rectangle",      dict(x1=0, y1=200, x2=800, y2=600)),
    ("draw_circle",         dict(cx=1500, cy=500, radius=300)),
    ("draw_arc",            dict(cx=2500, cy=500, radius=300, start_angle_deg=0, end_angle_deg=180)),
    ("draw_ellipse",        dict(cx=3500, cy=500, major_x=400, major_y=0, ratio=0.5)),
    ("draw_text",           dict(x=4500, y=500, text="TEST TEXT", height=100)),
    ("draw_mtext",          dict(x=5500, y=500, text="MTEXT TEST", width=500, height=100)),
    ("draw_hatch",          dict(boundary_x1=6000, boundary_y1=200,
                                 boundary_x2=6800, boundary_y2=700, pattern="ANSI31")),
    ("add_linear_dimension", dict(x1=0, y1=-200, x2=1000, y2=-200,
                                   text_x=500, text_y=-400)),
    # ── layers ───────────────────────────────────────────────────────────────
    ("create_layer",        dict(name="TEST-LAYER", color="red")),
    ("set_active_layer",    dict(name="TEST-LAYER")),
    ("list_layers",         dict()),
    ("setup_id_layers",     dict()),
    # ── objects ──────────────────────────────────────────────────────────────
    ("list_entities",       dict()),
    # ── files ────────────────────────────────────────────────────────────────
    ("list_open_drawings",  dict()),
    ("save_drawing",        dict()),
    ("zoom_extents",        dict()),
    # ── query ────────────────────────────────────────────────────────────────
    ("get_drawing_info",    dict()),
    ("count_entities_by_type", dict()),
    # ── layouts ──────────────────────────────────────────────────────────────
    ("list_layouts",        dict()),
    # ── blocks / xrefs / styles ──────────────────────────────────────────────
    ("list_blocks",         dict()),
    ("list_text_styles",    dict()),
    ("list_dim_styles",     dict()),
    ("create_block_definition", dict(name="TEST_BLK", base_x=0, base_y=0)),
    # ── arrays ───────────────────────────────────────────────────────────────
    # (arrays need a handle — skip for now, test separately after draw)
    # ── interior spaces ───────────────────────────────────────────────────────
    ("draw_wall",           dict(x1=0,  y1=1000, x2=3000, y2=1000, thickness=150)),
    ("draw_wall",           dict(x1=0,  y1=1000, x2=0,    y2=3000, thickness=150)),
    ("draw_wall",           dict(x1=3000,y1=1000, x2=3000, y2=3000, thickness=150)),
    ("draw_wall",           dict(x1=0,  y1=3000, x2=3000, y2=3000, thickness=150)),
    ("add_door",            dict(x=500, y=1000, width=900, rotation_deg=0,
                                  swing_direction="left")),
    ("add_window",          dict(x=1500, y=1000, width=1200, wall_thickness=150)),
    ("add_opening",         dict(x=2200, y=1000, width=800)),
    ("draw_room",           dict(x=3500, y=1000, width=3000, depth=2000,
                                  name="LIVING", layer="A-WALL")),
    ("draw_staircase",      dict(x=7000, y=1000, width=1200, num_steps=12,
                                  going=250)),
    ("tag_room",            dict(x=4000, y=2000, room_name="LIVING ROOM",
                                  area_m2=24.5, text_height=150)),
    # ── furniture ─────────────────────────────────────────────────────────────
    ("place_sofa",          dict(x=100, y=3500, width=2200, depth=900)),
    ("place_chair",         dict(x=3000, y=3500)),
    ("place_armchair",      dict(x=3700, y=3500)),
    ("place_dining_table",  dict(x=5000, y=3800, width=1800, depth=900, num_chairs=6)),
    ("place_coffee_table",  dict(x=100, y=4600)),
    ("place_coffee_table",  dict(x=1500, y=4600, shape="oval")),
    ("place_coffee_table",  dict(x=2800, y=4600, shape="round")),
    ("place_desk",          dict(x=3500, y=4500, with_return=True)),
    ("place_bed",           dict(x=100, y=5200, size="queen")),
    ("place_bed",           dict(x=2200, y=5200, size="king")),
    ("place_bed",           dict(x=4300, y=5200, size="single")),
    ("place_kitchen_unit",  dict(x=6000, y=5200, unit_type="base")),
    ("place_kitchen_unit",  dict(x=6700, y=5200, unit_type="sink")),
    ("place_kitchen_unit",  dict(x=7400, y=5200, unit_type="hob")),
    ("place_kitchen_unit",  dict(x=8100, y=5200, unit_type="corner")),
    ("place_toilet",        dict(x=100, y=6300)),
    ("place_bath",          dict(x=1000, y=6300)),
    ("place_sink",          dict(x=3000, y=6300, num_bowls=2)),
    ("place_shower",        dict(x=3800, y=6300)),
    ("place_wardrobe",      dict(x=5000, y=6300, door_type="hinged")),
    ("place_wardrobe",      dict(x=6900, y=6300, door_type="sliding")),
    ("place_bookshelf",     dict(x=8000, y=6300)),
    ("place_light_downlight", dict(x=500, y=7200)),
    ("place_light_pendant", dict(x=1200, y=7200)),
    ("place_power_outlet",  dict(x=2000, y=7200)),
    # ── schedules ─────────────────────────────────────────────────────────────
    ("create_room_schedule",   dict(x=0, y=-1000,
                                     rooms=[{"name":"Living","width":4000,"depth":5000,
                                             "floor":"Oak","wall":"White","ceiling":"White"}])),
    ("create_door_schedule",   dict(x=3000, y=-1000,
                                     doors=[{"mark":"D1","width":900,"height":2100,
                                             "type":"Solid","material":"Timber"}])),
    ("create_window_schedule", dict(x=6000, y=-1000,
                                     windows=[{"mark":"W1","width":1200,"height":1050,
                                               "type":"Casement","material":"uPVC"}])),
    ("create_ffe_schedule",    dict(x=0, y=-3000,
                                     items=[{"mark":"F01","name":"Sofa","qty":1,
                                             "supplier":"TBD","code":"S001","finish":"Fabric"}])),
    ("create_material_legend", dict(x=4000, y=-3000,
                                     materials=[{"name":"Oak Floor",
                                                 "hatch_pattern":"ANSI31",
                                                 "hatch_scale":1.0,
                                                 "description":"Engineered oak",
                                                 "supplier":"TBD","code":"F01"}])),
    ("create_revision_table",  dict(x=8000, y=-3000,
                                     revisions=[{"rev":"A","date":"2026-01-15",
                                                 "description":"Initial issue","by":"KB"}])),
    # ── id_annotations ───────────────────────────────────────────────────────
    ("add_elevation_marker",    dict(x=0,    y=-5000, label="A", directions=["N", "S"])),
    ("add_section_marker",      dict(x1=0,   y1=-5500, x2=2000, y2=-5500, label="1")),
    ("add_north_arrow",         dict(x=3000, y=-5000, size=200)),
    ("add_scale_bar",           dict(x=4000, y=-5000, scale=100, num_segments=5)),
    ("add_revision_cloud",      dict(x1=5000,y1=-5200,x2=6000,y2=-4800)),
    ("add_material_callout",    dict(pointer_x=7000, pointer_y=-5000,
                                      text_x=7300, text_y=-4800,
                                      material_name="OAK FLOOR")),
    ("add_detail_bubble",       dict(x=8500, y=-5000, detail_ref="1", sheet_ref="A301")),
    ("add_grid_lines",          dict(origin_x=0, origin_y=-6000,
                                      x_spacings=[3000.0], y_spacings=[2000.0])),
    ("generate_room_data_tag",  dict(x=1500, y=-5500, room_name="BEDROOM",
                                      room_number="B01", area_m2=18.5)),
    # ── interior_advanced ────────────────────────────────────────────────────
    ("draw_l_shaped_room",       dict(x=0, y=-9000,
                                       total_width=5000, total_depth=4000,
                                       notch_width=2000, notch_depth=2000,
                                       wall_thickness=150)),
    ("draw_rcp_room",            dict(x=0, y=-14000, width=4000, depth=3000)),
    ("draw_wall_elevation",      dict(x=5000, y=-9000,
                                       wall_width=4000, floor_to_ceiling=2700,
                                       wall_label="ELEVATION A")),
    ("draw_skirting_boards",     dict(room_x=0, room_y=-15000,
                                       room_width=4000, room_depth=3000, height=100)),
    ("add_window_to_elevation",  dict(elevation_x=5000, elevation_y=-14000,
                                       window_x=5600)),
    ("draw_staircase",           dict(x=0, y=-17000, width=1200, num_steps=14,
                                       going=250, direction="up")),
    ("draw_kitchen_layout",      dict(x=5000, y=-15000,
                                       room_width=4000, room_depth=3000,
                                       layout_type="L-shape")),
    ("draw_bathroom_layout",     dict(x=0, y=-20000,
                                       room_width=2400, room_depth=2000,
                                       layout_type="standard")),
    # ── geometric_construction ───────────────────────────────────────────────
    ("draw_regular_polygon",     dict(cx=0, cy=-23000, radius=500, sides=6)),
    ("draw_polygon_by_edge",     dict(x1=1500, y1=-23000, x2=2500, y2=-23000, sides=5)),
    ("draw_isometric_grid",      dict(origin_x=3000, origin_y=-23000,
                                       width=3000, height=3000, grid_spacing=500)),
    ("setup_orthographic_layout", dict(origin_x=0, origin_y=-25000,
                                        view_width=2000, view_height=1500)),
    ("draw_scale_comparison",    dict(origin_x=7000, origin_y=-23000,
                                       object_length=1000, scales=[50, 100, 200])),
    ("draw_golden_ratio_rectangle", dict(origin_x=0, origin_y=-28000, width=1618)),
    ("setup_one_point_perspective", dict(origin_x=3000, origin_y=-28000,
                                          horizon_height=1500, vp_x=3000)),
    ("setup_two_point_perspective", dict(origin_x=6000, origin_y=-28000,
                                          horizon_height=1500,
                                          vp_left_x=4000, vp_right_x=10000)),
    ("draw_prism_surface_development",   dict(origin_x=0, origin_y=-32000,
                                               sides=4, edge_length=500, height=1000)),
    ("draw_pyramid_surface_development", dict(origin_x=2000, origin_y=-32000,
                                               sides=4, base_edge=500, slant_height=800)),
    # ── anthropometry ─────────────────────────────────────────────────────────
    ("draw_human_figure",        dict(x=0, y=-35000, posture="standing")),
    ("draw_human_figure",        dict(x=600, y=-35000, posture="seated")),
    ("draw_human_figure",        dict(x=1200, y=-35000, posture="wheelchair")),
    ("draw_clearance_zone",      dict(x=2500, y=-35000, width=1500, depth=750,
                                       clearance_type="desk")),
    ("draw_wheelchair_turning_circle", dict(cx=4000, cy=-35000)),
    ("draw_corridor_standard",   dict(x1=5000, y1=-35000, length=3000,
                                       corridor_type="standard")),
    ("check_space_compliance",   dict(room_width=3000, room_depth=3000,
                                       room_type="bedroom")),
    ("draw_kitchen_work_triangle", dict(sink_x=0,    sink_y=-38000,
                                         hob_x=1200,  hob_y=-38000,
                                         fridge_x=600, fridge_y=-39200)),
    ("draw_human_reach_zone",    dict(x=3000, y=-38000, standing=True)),
    ("draw_ergonomic_dimensions_table", dict(origin_x=5000, origin_y=-36000,
                                              category="seating")),
    ("draw_elevation_height_standards", dict(x=8000, y=-38000, width=3000)),
    # ── mep_services ─────────────────────────────────────────────────────────
    ("place_power_outlet",        dict(x=0, y=-42000)),
    ("place_light_switch",        dict(x=500, y=-42000)),
    ("draw_electrical_circuit",   dict(circuit_id="C1", circuit_type="lighting",
                                        points=[(0,-43000),(2000,-43000),(2000,-42000)])),
    ("draw_electrical_panel",     dict(origin_x=3000, origin_y=-43000,
                                        circuits=[{"id":"C1","type":"lighting","load":"100W"},
                                                  {"id":"C2","type":"power","load":"2kW"}])),
    ("draw_plumbing_symbol",      dict(x=7000, y=-42000, symbol_type="wc")),
    ("draw_pipe_run",             dict(pipe_type="CW", pipe_size="22mm",
                                        points=[(0,-45000),(3000,-45000)])),
    ("draw_wet_room_plumbing",    dict(origin_x=4000, origin_y=-47000,
                                        room_width=2400, room_depth=2000)),
    ("place_ac_unit",             dict(x=0, y=-49000, unit_type="split_indoor")),
    ("draw_ac_diffuser",          dict(x=1500, y=-49000, diffuser_type="square")),
    ("draw_ductwork",             dict(points=[(3000,-49000),(5000,-49000)],
                                        duct_width=400)),
    ("place_smoke_detector",      dict(x=6000, y=-49000, detector_type="smoke")),
    ("draw_services_legend",      dict(origin_x=8000, origin_y=-48000)),
    # ── tile_design ──────────────────────────────────────────────────────────
    ("draw_tile_grid",            dict(room_x=0,  room_y=-53000,
                                        room_w=3000, room_h=3000,
                                        tile_w=600,  tile_h=600)),
    ("draw_tile_running_bond",    dict(room_x=4000, room_y=-53000,
                                        room_w=3000,  room_h=3000,
                                        tile_w=600,   tile_h=300)),
    ("draw_tile_herringbone",     dict(room_x=8000, room_y=-53000,
                                        room_w=3000,  room_h=3000,
                                        tile_w=600,   tile_h=300)),
    ("draw_tile_chevron",         dict(room_x=0, room_y=-57000,
                                        room_w=3000, room_h=3000, tile_w=600, tile_h=300)),
    ("draw_tile_basket_weave",    dict(room_x=4000, room_y=-57000,
                                        room_w=3000, room_h=3000,
                                        tile_w=300,  tile_h=150)),
    ("draw_tile_versailles",      dict(room_x=8000, room_y=-57000,
                                        room_w=3000, room_h=3000)),
    ("draw_tile_diagonal",        dict(room_x=0, room_y=-61000,
                                        room_w=3000, room_h=3000, tile_size=600)),
    ("calculate_tile_waste",      dict(room_w=4000, room_h=3000,
                                        tile_w=600, tile_h=600, pattern="grid")),
    ("draw_tile_border_strip",    dict(room_x=7000, room_y=-62000,
                                        room_w=3000, room_h=3000,
                                        border_width=150)),
    ("draw_tile_zones",           dict(room_x=0, room_y=-65000,
                                        room_w=5000, room_h=4000,
                                        zones=[{"name":"A","x":0,"y":0,
                                                "w":2500,"h":4000,
                                                "pattern":"grid",
                                                "tile_w":600,"tile_h":600},
                                               {"name":"B","x":2500,"y":0,
                                                "w":2500,"h":4000,
                                                "pattern":"herringbone",
                                                "tile_w":300,"tile_h":300}])),
]


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
def run_tests(stop_on_fail=False):
    tools = mcp._tools
    results = []
    passed = 0
    failed = 0
    skipped = 0

    print(f"\n{'='*70}")
    print(f"  AutoCAD MCP Tool Test Runner")
    print(f"  {len(TESTS)} tests across {len(set(t[0] for t in TESTS))} unique tools")
    print(f"{'='*70}\n")

    for tool_name, kwargs in TESTS:
        fn = tools.get(tool_name)
        if fn is None:
            print(f"  SKIP  {tool_name}  (not registered)")
            skipped += 1
            results.append((tool_name, "SKIP", "not registered", kwargs))
            continue

        try:
            result = fn(**kwargs)
            print(f"  PASS  {tool_name}")
            passed += 1
            results.append((tool_name, "PASS", None, kwargs))
        except Exception as e:
            tb = traceback.format_exc().strip().splitlines()
            # Show last 3 lines of traceback (most useful)
            short_tb = "\n          ".join(tb[-3:])
            print(f"  FAIL  {tool_name}")
            print(f"          {short_tb}")
            failed += 1
            results.append((tool_name, "FAIL", str(e), kwargs))
            if stop_on_fail:
                break

    print(f"\n{'='*70}")
    print(f"  PASSED: {passed}   FAILED: {failed}   SKIPPED: {skipped}")
    print(f"{'='*70}\n")

    if failed:
        print("FAILED TOOLS:")
        for name, status, err, _ in results:
            if status == "FAIL":
                print(f"  {name}: {err}")

    return failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stop-on-fail", action="store_true")
    args = parser.parse_args()

    ok = run_tests(stop_on_fail=args.stop_on_fail)
    sys.exit(0 if ok else 1)
