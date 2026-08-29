from __future__ import annotations

from dataclasses import fields, is_dataclass
from inspect import signature
from typing import get_args, get_origin, get_type_hints


def _strip_optional(tp):
    args = [a for a in get_args(tp) if a is not type(None)]
    return args[0] if len(args) == 1 else tp


def detect_layout_item_type(impose_jobs):
    """Return the concrete item type for layout_override when the contract is explicit.

    Only typed sequence/dataclass-style contracts are accepted. Ambiguous dict/Any contracts
    intentionally return None so production remains fail-closed.
    """
    hints = get_type_hints(impose_jobs)
    tp = hints.get('layout_override')
    if tp is None:
        return None
    tp = _strip_optional(tp)
    origin = get_origin(tp)
    args = get_args(tp)
    if origin is None:
        return tp if is_dataclass(tp) else None
    if not args:
        return None
    item = _strip_optional(args[0])
    return item if is_dataclass(item) else None


ALIASES = {
    'x': ('x_mm', 'x', 'left_mm', 'left'),
    'y': ('y_mm', 'y', 'top_mm', 'top'),
    'rotation': ('rotation', 'rotation_deg', 'angle', 'rotate'),
    'page_index': ('page_index', 'page', 'source_page', 'page_no'),
    'job_index': ('job_index', 'source_index', 'input_index', 'job'),
    'width': ('width_mm', 'width', 'w_mm', 'w'),
    'height': ('height_mm', 'height', 'h_mm', 'h'),
}


def _find_field(field_names, semantic):
    for name in ALIASES[semantic]:
        if name in field_names:
            return name
    return None


def build_layout_override(impose_jobs, placements, job_index_by_path):
    """Build the real layout_override object from normalized V2.4 placements.

    placements: dicts containing path/page_index/x_mm/y_mm/width_mm/height_mm/rotation.
    Raises RuntimeError unless the engine exposes a precise typed dataclass contract.
    """
    item_type = detect_layout_item_type(impose_jobs)
    if item_type is None:
        raise RuntimeError('生产引擎未公开可安全识别的 layout_override 类型契约，已阻止手工版位输出')

    names = {f.name for f in fields(item_type)}
    mapping = {
        key: _find_field(names, key)
        for key in ('x','y','rotation','page_index','job_index','width','height')
    }
    required = ('x','y','page_index','job_index')
    missing = [k for k in required if mapping[k] is None]
    if missing:
        raise RuntimeError('layout_override 契约缺少必要字段：' + ', '.join(missing))

    result = []
    for p in placements:
        path = str(p['path'])
        if path not in job_index_by_path:
            raise RuntimeError(f'版位源文件未加入生产任务：{path}')
        kwargs = {
            mapping['x']: float(p['x_mm']),
            mapping['y']: float(p['y_mm']),
            mapping['page_index']: int(p['page_index']),
            mapping['job_index']: int(job_index_by_path[path]),
        }
        if mapping['rotation']:
            kwargs[mapping['rotation']] = int(p.get('rotation', 0)) % 360
        if mapping['width']:
            kwargs[mapping['width']] = float(p['width_mm'])
        if mapping['height']:
            kwargs[mapping['height']] = float(p['height_mm'])
        try:
            result.append(item_type(**kwargs))
        except TypeError as exc:
            raise RuntimeError(f'无法按生产引擎契约构造手工版位：{exc}') from exc
    return result
