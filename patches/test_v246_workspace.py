from pathlib import Path
import tempfile

from workspace import save_workspace, load_workspace

sample = {
    "schema_version": 1,
    "app_version": "2.4.6",
    "page_canvas": {
        "sheet": {"width_mm": 650.0, "height_mm": 450.0, "bleed_mm": 3.0, "snap_mm": 1.0},
        "duplex_mode": "left_right",
        "placements": [
            {"path": "job-a.pdf", "page_index": 0, "width_pt": 595.0, "height_pt": 842.0, "x_mm": 12.5, "y_mm": 18.0, "rotation": 90, "locked": True},
            {"path": "job-b.pdf", "page_index": 2, "width_pt": 612.0, "height_pt": 792.0, "x_mm": 220.0, "y_mm": 44.0, "rotation": 0, "locked": False},
        ],
    },
    "print_marks": {
        "crop_marks": True,
        "register_marks": True,
        "color_bar": True,
        "file_name": True,
        "plate_no": True,
        "date": True,
        "side_label": True,
        "gripper_arrow": True,
        "crop_length_mm": 5.0,
        "crop_offset_mm": 2.0,
        "crop_width_pt": 0.25,
        "register_radius_mm": 3.0,
        "text_size_pt": 7.0,
        "gripper_edge": "top",
        "file_text": "job-a.pdf",
        "plate_text": "A01",
        "side_text": "FRONT",
    },
}

with tempfile.TemporaryDirectory(prefix="workspace-v246-") as td:
    path = Path(td) / "中文项目.dipw"
    actual = save_workspace(path, sample)
    assert actual == path
    assert path.exists() and path.stat().st_size > 0
    loaded = load_workspace(path)
    assert loaded["page_canvas"]["sheet"]["width_mm"] == 650.0
    assert loaded["page_canvas"]["placements"][0]["rotation"] == 90
    assert loaded["page_canvas"]["placements"][0]["locked"] is True
    assert loaded["page_canvas"]["duplex_mode"] == "left_right"
    assert loaded["print_marks"]["gripper_edge"] == "top"
    assert loaded["print_marks"]["plate_text"] == "A01"

print("V2.4.6 workspace round-trip tests passed")
