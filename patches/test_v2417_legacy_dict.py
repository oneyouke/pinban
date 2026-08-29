from dataclasses import dataclass
from typing import Optional

from layout_diagnostics import collect_layout_diagnostics


def atomic_export(*args, **kwargs):
    return {}


def legacy(jobs, output_path, settings, layout_override: dict | None = None):
    return {}


def no_layout(jobs, output_path, settings):
    return {}


@dataclass
class Placement:
    x_mm: float
    y_mm: float
    page_index: int
    job_index: int
    rotation: int = 0


def typed(jobs, output_path, settings, layout_override: Optional[list[Placement]] = None):
    return {}


r = collect_layout_diagnostics(legacy, atomic_export)
assert r['status'] == 'LEGACY_DICT', r
assert r['contract']['kind'] == 'legacy_dict'
assert any('dict' in x for x in r['reasons'])

r = collect_layout_diagnostics(no_layout, atomic_export)
assert r['status'] == 'BLOCKED', r

r = collect_layout_diagnostics(typed, atomic_export)
assert r['status'] == 'READY', r
assert r['contract']['semantic_mapping']['x'] == 'x_mm'
assert r['contract']['semantic_mapping']['job_index'] == 'job_index'

print('V2.4.17 LEGACY DICT DIAGNOSTICS PASS')
