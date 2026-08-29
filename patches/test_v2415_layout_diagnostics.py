from dataclasses import dataclass
from typing import Optional

from layout_diagnostics import collect_layout_diagnostics, format_layout_diagnostics


@dataclass
class Placement:
    x_mm: float
    y_mm: float
    page_index: int
    job_index: int
    rotation: int = 0
    width_mm: float = 0
    height_mm: float = 0


def impose_ready(jobs, settings, layout_override: Optional[list[Placement]] = None):
    return {}


def export_ready(jobs, output_path, settings, **kwargs):
    return {}


def impose_no_layout(jobs, settings):
    return {}


@dataclass
class BrokenPlacement:
    x_mm: float
    y_mm: float


def impose_broken(jobs, settings, layout_override: Optional[list[BrokenPlacement]] = None):
    return {}


def main():
    ready = collect_layout_diagnostics(impose_ready, export_ready)
    assert ready['status'] == 'READY', ready
    mapping = ready['contract']['semantic_mapping']
    assert mapping['x'] == 'x_mm'
    assert mapping['y'] == 'y_mm'
    assert mapping['page_index'] == 'page_index'
    assert mapping['job_index'] == 'job_index'
    text = format_layout_diagnostics(ready)
    assert 'READY' in text and 'job_index -> job_index' in text

    no_layout = collect_layout_diagnostics(impose_no_layout, export_ready)
    assert no_layout['status'] == 'BLOCKED'
    assert any('layout_override' in reason for reason in no_layout['reasons'])

    broken = collect_layout_diagnostics(impose_broken, export_ready)
    assert broken['status'] == 'BLOCKED'
    assert any('page_index' in reason and 'job_index' in reason for reason in broken['reasons'])

    print('V2.4.15 LAYOUT DIAGNOSTICS PASS')


if __name__ == '__main__':
    main()
