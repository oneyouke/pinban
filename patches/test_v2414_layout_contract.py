from dataclasses import dataclass
from typing import Sequence

from layout_contract import build_layout_override, detect_layout_item_type


@dataclass
class PlacementContract:
    job_index: int
    page_index: int
    x_mm: float
    y_mm: float
    rotation: int = 0
    width_mm: float = 0.0
    height_mm: float = 0.0


def fake_impose(jobs, output, settings, layout_override: Sequence[PlacementContract] | None = None):
    return None


@dataclass
class BadContract:
    x_mm: float
    y_mm: float


def bad_impose(jobs, output, settings, layout_override: Sequence[BadContract] | None = None):
    return None


assert detect_layout_item_type(fake_impose) is PlacementContract
rows = build_layout_override(
    fake_impose,
    [{
        'path': 'A.pdf', 'page_index': 2,
        'x_mm': 12.5, 'y_mm': 20.25,
        'width_mm': 90.0, 'height_mm': 54.0, 'rotation': 90,
    }],
    {'A.pdf': 3},
)
assert len(rows) == 1
p = rows[0]
assert p.job_index == 3 and p.page_index == 2
assert p.x_mm == 12.5 and p.y_mm == 20.25
assert p.rotation == 90 and p.width_mm == 90.0 and p.height_mm == 54.0

try:
    build_layout_override(bad_impose, [{'path':'A.pdf','page_index':0,'x_mm':0,'y_mm':0,'width_mm':10,'height_mm':10,'rotation':0}], {'A.pdf':0})
except RuntimeError as exc:
    assert '必要字段' in str(exc)
else:
    raise AssertionError('bad contract must fail closed')

print('V2.4.14 layout contract adapter tests passed')
