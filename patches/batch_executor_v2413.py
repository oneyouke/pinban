from __future__ import annotations

from pathlib import Path
from typing import Any

from batch_queue import BatchJob
from workspace import load_workspace
from imposition import InputJob, ImpositionSettings
from production_service import atomic_production_export


def _make_settings(page_canvas: dict) -> ImpositionSettings:
    sheet = (page_canvas or {}).get('sheet') or {}
    width = float(sheet.get('width_mm') or 0)
    height = float(sheet.get('height_mm') or 0)
    if width <= 0 or height <= 0:
        raise ValueError('工作区纸张尺寸无效')
    return ImpositionSettings(sheet_width_mm=width, sheet_height_mm=height)


def _source_jobs(page_canvas: dict) -> list[InputJob]:
    placements = list((page_canvas or {}).get('placements') or [])
    if not placements:
        raise ValueError('工作区没有可生产的页面')
    seen = set()
    jobs = []
    for row in placements:
        path = Path(str(row.get('path') or '')).expanduser()
        page_index = int(row.get('page_index', 0) or 0)
        key = (str(path), page_index)
        if key in seen:
            continue
        seen.add(key)
        if not path.is_file():
            raise FileNotFoundError(f'源 PDF 不存在：{path}')
        jobs.append(InputJob(path, page_index + 1))
    if not jobs:
        raise ValueError('工作区没有有效源 PDF')
    return jobs


def _has_manual_layout(page_canvas: dict) -> bool:
    """Detect explicit canvas editing that cannot yet be losslessly mapped to legacy layout_override.

    V2.4.13 deliberately refuses these jobs instead of silently producing a different imposition.
    """
    placements = list((page_canvas or {}).get('placements') or [])
    if not placements:
        return False
    # A single unrotated item at the origin is safe to regenerate automatically.
    if len(placements) == 1:
        p = placements[0]
        return any(abs(float(p.get(k, 0) or 0)) > 1e-7 for k in ('x_mm','y_mm')) or int(p.get('rotation',0) or 0) % 360 != 0
    # Multiple explicit canvas placements are treated as manual until the legacy layout_override schema is bridged.
    return True


def execute_batch_job(job: BatchJob) -> dict[str, Any]:
    ws = load_workspace(job.workspace_path)
    page_canvas = ws.get('page_canvas') or {}
    if _has_manual_layout(page_canvas):
        raise ValueError('当前批量生产仅支持自动拼版工作区；检测到手工版位。为避免输出与画布不一致，本任务已阻止。')
    jobs = _source_jobs(page_canvas)
    settings = _make_settings(page_canvas)
    manifest = atomic_production_export(jobs, job.output_path, settings, write_manifest=True)
    return {
        'output': manifest.get('output') or str(job.output_path),
        'output_sha256': manifest.get('output_sha256',''),
        'output_pages': manifest.get('output_pages'),
        'warnings': list(manifest.get('record_warnings') or []),
        'production_manifest': manifest,
    }
