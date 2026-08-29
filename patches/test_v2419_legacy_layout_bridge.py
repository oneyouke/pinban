from pathlib import Path
from types import SimpleNamespace

from legacy_layout_bridge import PT_TO_MM, LegacyLayoutBridgeError, build_legacy_layout

jobs = [SimpleNamespace(path=Path("A.pdf")), SimpleNamespace(path=Path("B.pdf"))]
canvas = {
    "sheet": {"width_mm": 650, "height_mm": 450, "bleed_mm": 3},
    "placements": [
        {"path":"A.pdf","page_index":0,"width_pt":72,"height_pt":144,"x_mm":10,"y_mm":20,"rotation":0},
        {"path":"B.pdf","page_index":2,"width_pt":72,"height_pt":144,"x_mm":100,"y_mm":30,"rotation":90},
    ],
}
layout = build_legacy_layout(canvas, jobs)
assert layout["sheet_width_mm"] == 650
assert layout["expected_keys"] == [[0,0],[1,2]]
a, b = layout["sheets"][0]
assert a["job_index"] == 0 and a["unit_index"] == 0
assert abs(a["footprint_width_mm"] - (72 * PT_TO_MM + 6)) < 1e-8
assert b["job_index"] == 1 and b["unit_index"] == 2
assert b["footprint_width_mm"] > b["footprint_height_mm"]

bad = dict(canvas)
bad["placements"] = [canvas["placements"][0], canvas["placements"][0]]
try:
    build_legacy_layout(bad, jobs)
except LegacyLayoutBridgeError:
    pass
else:
    raise AssertionError("duplicate placement must fail closed")

print("V2.4.19 LEGACY LAYOUT BRIDGE PASS")
