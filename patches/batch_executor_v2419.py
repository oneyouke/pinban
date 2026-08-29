from __future__ import annotations

from pathlib import Path
from typing import Any

from batch_queue import BatchJob
from workspace import load_workspace
from imposition import InputJob, ImpositionSettings
from production_service import atomic_production_export
from legacy_layout_bridge import PT_TO_MM, build_legacy_layout, verify_legacy_engine_contract


def _make_settings(page_canvas: dict) -> ImpositionSettings:
    sheet = (page_canvas or {}).get("sheet") or {}
    width = float(sheet.get("width_mm") or 0)
    height = float(sheet.get("height_mm") or 0)
    if width <= 0 or height <= 0:
        raise ValueError("工作区纸张尺寸无效")
    return ImpositionSettings(
        sheet_width_mm=width, sheet_height_mm=height,
        bleed_mm=float(sheet.get("bleed_mm") or 0),
        smart_mixed_sizes=True,
    )


def _source_jobs(page_canvas: dict) -> list[InputJob]:
    placements = list((page_canvas or {}).get("placements") or [])
    if not placements:
        raise ValueError("工作区没有可生产的页面")
    bleed = float(((page_canvas or {}).get("sheet") or {}).get("bleed_mm") or 0)
    rows_by_path = {}
    order = []
    for row in placements:
        path = Path(str(row.get("path") or "")).expanduser()
        key = str(path)
        if key not in rows_by_path:
            rows_by_path[key] = row
            order.append(key)
        if not path.is_file():
            raise FileNotFoundError(f"源 PDF 不存在：{path}")
    jobs = []
    for key in order:
        row = rows_by_path[key]
        width = float(row.get("width_pt") or 0) * PT_TO_MM
        height = float(row.get("height_pt") or 0) * PT_TO_MM
        if width <= 0 or height <= 0:
            raise ValueError(f"源页面尺寸无效：{key}")
        jobs.append(InputJob(
            path=Path(key), quantity=1,
            trim_width_mm=width, trim_height_mm=height, bleed_mm=bleed,
        ))
    return jobs


def _has_manual_layout(page_canvas: dict) -> bool:
    placements = list((page_canvas or {}).get("placements") or [])
    if not placements:
        return False
    if len(placements) == 1:
        p = placements[0]
        return any(abs(float(p.get(k, 0) or 0)) > 1e-7 for k in ("x_mm","y_mm")) or int(p.get("rotation",0) or 0) % 360 != 0
    return True


def execute_batch_job(job: BatchJob) -> dict[str, Any]:
    ws = load_workspace(job.workspace_path)
    page_canvas = ws.get("page_canvas") or {}
    jobs = _source_jobs(page_canvas)
    settings = _make_settings(page_canvas)
    layout_override = None
    if _has_manual_layout(page_canvas):
        verify_legacy_engine_contract()
        layout_override = build_legacy_layout(page_canvas, jobs)
    manifest = atomic_production_export(
        jobs, job.output_path, settings,
        layout_override=layout_override, write_manifest=True,
    )
    return {
        "output": manifest.get("output") or str(job.output_path),
        "output_sha256": manifest.get("output_sha256",""),
        "output_pages": manifest.get("output_pages"),
        "warnings": list(manifest.get("record_warnings") or []),
        "production_manifest": manifest,
    }
