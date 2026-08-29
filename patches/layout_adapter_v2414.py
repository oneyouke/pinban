from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path


_ALLOWED_ROTATIONS = {0, 90, 180, 270}


@dataclass(frozen=True)
class NormalizedPlacement:
    path: str
    page_index: int
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    rotation: int

    def to_dict(self):
        return asdict(self)


def _rotated_size(width_mm: float, height_mm: float, rotation: int) -> tuple[float, float]:
    return (height_mm, width_mm) if rotation % 180 else (width_mm, height_mm)


def normalize_workspace_placements(workspace: dict, *, require_files: bool = True) -> tuple[dict, list[NormalizedPlacement]]:
    page_canvas = (workspace or {}).get('page_canvas') or {}
    sheet = page_canvas.get('sheet') or {}
    sheet_w = float(sheet.get('width_mm') or 0)
    sheet_h = float(sheet.get('height_mm') or 0)
    if sheet_w <= 0 or sheet_h <= 0:
        raise ValueError('工作区纸张尺寸无效')

    rows = list(page_canvas.get('placements') or [])
    if not rows:
        raise ValueError('工作区没有可生产的手工版位')

    out: list[NormalizedPlacement] = []
    for index, row in enumerate(rows, 1):
        path = str(row.get('path') or '').strip()
        if not path:
            raise ValueError(f'第 {index} 个版位缺少源 PDF 路径')
        if require_files and not Path(path).is_file():
            raise FileNotFoundError(f'第 {index} 个版位源 PDF 不存在：{path}')
        page_index = int(row.get('page_index', 0))
        if page_index < 0:
            raise ValueError(f'第 {index} 个版位页码无效')
        rotation = int(row.get('rotation', 0)) % 360
        if rotation not in _ALLOWED_ROTATIONS:
            raise ValueError(f'第 {index} 个版位旋转角度必须是 0/90/180/270°')
        width_pt = float(row.get('width_pt') or 0)
        height_pt = float(row.get('height_pt') or 0)
        if width_pt <= 0 or height_pt <= 0:
            raise ValueError(f'第 {index} 个版位缺少有效页面尺寸')
        width_mm = width_pt * 25.4 / 72.0
        height_mm = height_pt * 25.4 / 72.0
        x_mm = float(row.get('x_mm') or 0)
        y_mm = float(row.get('y_mm') or 0)
        placed_w, placed_h = _rotated_size(width_mm, height_mm, rotation)
        eps = 1e-6
        if x_mm < -eps or y_mm < -eps or x_mm + placed_w > sheet_w + eps or y_mm + placed_h > sheet_h + eps:
            raise ValueError(
                f'第 {index} 个版位超出纸张：x={x_mm:.3f}, y={y_mm:.3f}, '
                f'尺寸={placed_w:.3f}×{placed_h:.3f} mm，纸张={sheet_w:.3f}×{sheet_h:.3f} mm'
            )
        out.append(NormalizedPlacement(path, page_index, x_mm, y_mm, width_mm, height_mm, rotation))

    return {'width_mm': sheet_w, 'height_mm': sheet_h}, out


def unique_source_pages(placements: list[NormalizedPlacement]) -> list[tuple[str, int]]:
    seen = set(); out = []
    for p in placements:
        key = (str(Path(p.path)), int(p.page_index))
        if key not in seen:
            seen.add(key); out.append(key)
    return out
