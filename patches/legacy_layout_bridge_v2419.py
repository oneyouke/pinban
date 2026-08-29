from __future__ import annotations

from inspect import getsource, signature
from pathlib import Path
from typing import Any

PT_TO_MM = 25.4 / 72.0
_REQUIRED_ENGINE_TOKENS = (
    'layout["sheets"]', 'raw["job_index"]', 'raw["unit_index"]',
    'raw["x_mm"]', 'raw["y_mm"]', 'raw["footprint_width_mm"]',
    'raw["footprint_height_mm"]',
)


class LegacyLayoutBridgeError(RuntimeError):
    pass


def verify_legacy_engine_contract(impose_jobs=None, atomic_export=None) -> dict[str, Any]:
    if impose_jobs is None:
        from imposition import impose_jobs
    if atomic_export is None:
        from production_service import atomic_production_export as atomic_export
    if "layout_override" not in signature(impose_jobs).parameters:
        raise LegacyLayoutBridgeError("impose_jobs does not accept layout_override")
    if "layout_override" not in signature(atomic_export).parameters:
        raise LegacyLayoutBridgeError("atomic_production_export does not accept layout_override")
    try:
        from imposition import validate_manual_layout, _packing_from_manual_layout
        source = getsource(validate_manual_layout) + "\n" + getsource(_packing_from_manual_layout)
    except Exception as exc:
        raise LegacyLayoutBridgeError(f"cannot inspect legacy engine contract: {exc}") from exc
    missing = [token for token in _REQUIRED_ENGINE_TOKENS if token not in source]
    if missing:
        raise LegacyLayoutBridgeError("legacy engine contract tokens missing: " + ", ".join(missing))
    return {
        "verified": True,
        "schema": "desktop-imposer.legacy-layout.v1",
        "coordinate_unit": "mm",
        "index_base": 0,
        "required_tokens": list(_REQUIRED_ENGINE_TOKENS),
    }


def build_legacy_layout(page_canvas: dict, jobs) -> dict[str, Any]:
    placements = list((page_canvas or {}).get("placements") or [])
    sheet = (page_canvas or {}).get("sheet") or {}
    if not placements:
        raise LegacyLayoutBridgeError("workspace has no placements")
    index_by_path = {str(Path(str(job.path)).expanduser()): i for i, job in enumerate(jobs)}
    bleed = float(sheet.get("bleed_mm") or 0)
    output = []
    seen = set()
    for row in placements:
        path = str(Path(str(row.get("path") or "")).expanduser())
        if path not in index_by_path:
            raise LegacyLayoutBridgeError(f"placement source is not a production job: {path}")
        unit_index = int(row.get("page_index", 0) or 0)
        key = (index_by_path[path], unit_index)
        if key in seen:
            raise LegacyLayoutBridgeError(f"duplicate placement: job {key[0]} unit {key[1]}")
        seen.add(key)
        rotation = int(row.get("rotation", 0) or 0) % 360
        if rotation not in (0, 90, 180, 270):
            raise LegacyLayoutBridgeError("rotation must be 0, 90, 180 or 270")
        base_w = float(row.get("width_pt") or 0) * PT_TO_MM + 2 * bleed
        base_h = float(row.get("height_pt") or 0) * PT_TO_MM + 2 * bleed
        if base_w <= 0 or base_h <= 0:
            raise LegacyLayoutBridgeError("placement source dimensions are invalid")
        footprint_w, footprint_h = (base_h, base_w) if rotation in (90, 270) else (base_w, base_h)
        output.append({
            "job_index": key[0], "unit_index": key[1],
            "x_mm": float(row.get("x_mm") or 0), "y_mm": float(row.get("y_mm") or 0),
            "footprint_width_mm": footprint_w, "footprint_height_mm": footprint_h,
            "rotation": rotation,
        })
    return {
        "sheet_width_mm": float(sheet.get("width_mm") or 0),
        "sheet_height_mm": float(sheet.get("height_mm") or 0),
        "sheets": [output],
        "expected_keys": [list(key) for key in sorted(seen)],
    }
