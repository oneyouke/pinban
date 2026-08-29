from __future__ import annotations

from dataclasses import dataclass, asdict
from math import ceil

from mix_optimizer import ProductSpec, optimize_mixed


@dataclass(frozen=True)
class PaperSpec:
    name: str
    width_mm: float
    height_mm: float
    enabled: bool = True


@dataclass(frozen=True)
class PressSpec:
    name: str
    max_width_mm: float
    max_height_mm: float
    gripper_mm: float = 0.0
    enabled: bool = True

    def supports(self, w: float, h: float) -> bool:
        return ((w <= self.max_width_mm + 1e-9 and h <= self.max_height_mm + 1e-9)
                or (h <= self.max_width_mm + 1e-9 and w <= self.max_height_mm + 1e-9))


@dataclass
class ResourceCandidate:
    paper: PaperSpec
    press: PressSpec
    sheet_width_mm: float
    sheet_height_mm: float
    packed_by_key: dict[str, int]
    utilization: float
    sheets_required: int
    total_paper_area_mm2: float
    strategy: str
    placements: list[dict]

    def to_dict(self):
        d = asdict(self)
        return d


def _required_sheets(specs: list[ProductSpec], packed: dict[str, int]) -> int | None:
    needed = 0
    for spec in specs:
        per_sheet = int(packed.get(spec.key, 0) or 0)
        if per_sheet <= 0:
            return None
        needed = max(needed, int(ceil(int(spec.quantity) / per_sheet)))
    return max(1, needed)


def compare_resources(specs: list[ProductSpec], papers: list[PaperSpec], presses: list[PressSpec],
                      margin_mm: float = 5.0, gap_x_mm: float = 2.0, gap_y_mm: float = 2.0,
                      max_items: int = 256) -> list[ResourceCandidate]:
    specs = [s for s in specs if s.width_mm > 0 and s.height_mm > 0 and int(s.quantity) > 0]
    out: list[ResourceCandidate] = []
    if not specs:
        return out
    for paper in papers:
        if not paper.enabled or paper.width_mm <= 0 or paper.height_mm <= 0:
            continue
        for press in presses:
            if not press.enabled or not press.supports(paper.width_mm, paper.height_mm):
                continue
            for sw, sh, orientation in ((paper.width_mm, paper.height_mm, 'normal'), (paper.height_mm, paper.width_mm, 'rotated')):
                if sw == sh and orientation == 'rotated':
                    continue
                effective_margin = max(float(margin_mm), float(press.gripper_mm))
                result = optimize_mixed(specs, sw, sh, margin_mm=effective_margin,
                                        gap_x_mm=gap_x_mm, gap_y_mm=gap_y_mm, max_items=max_items)
                sheets = _required_sheets(specs, result.packed_by_key)
                if sheets is None or not result.items:
                    continue
                area = float(sw) * float(sh) * sheets
                out.append(ResourceCandidate(
                    paper=paper, press=press, sheet_width_mm=float(sw), sheet_height_mm=float(sh),
                    packed_by_key=dict(result.packed_by_key), utilization=float(result.utilization),
                    sheets_required=sheets, total_paper_area_mm2=area,
                    strategy=f'{orientation}/{result.strategy}', placements=[x.to_dict() for x in result.items],
                ))
    out.sort(key=lambda c: (c.total_paper_area_mm2, c.sheets_required, -c.utilization,
                            c.paper.name, c.press.name, c.strategy))
    return out


def best_resource_match(*args, **kwargs):
    rows = compare_resources(*args, **kwargs)
    return rows[0] if rows else None


DEFAULT_PAPERS = [
    PaperSpec('320×450', 320, 450), PaperSpec('330×480', 330, 480),
    PaperSpec('450×650', 450, 650), PaperSpec('520×760', 520, 760),
    PaperSpec('650×920', 650, 920),
]

DEFAULT_PRESSES = [
    PressSpec('数字机 330×488', 330, 488, 3),
    PressSpec('四开机 530×770', 530, 770, 8),
    PressSpec('对开机 750×1060', 750, 1060, 10),
]
