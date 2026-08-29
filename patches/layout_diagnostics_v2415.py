from __future__ import annotations

from dataclasses import fields, is_dataclass
from inspect import signature
from typing import Any, get_type_hints

from layout_contract import ALIASES, detect_layout_item_type


def _semantic_map(item_type):
    if item_type is None or not is_dataclass(item_type):
        return {}
    names = {f.name for f in fields(item_type)}
    out = {}
    for semantic, aliases in ALIASES.items():
        out[semantic] = next((name for name in aliases if name in names), None)
    return out


def collect_layout_diagnostics(impose_jobs=None, atomic_export=None) -> dict[str, Any]:
    report: dict[str, Any] = {
        'status': 'BLOCKED',
        'engine': {},
        'contract': {},
        'reasons': [],
    }
    try:
        if impose_jobs is None:
            from imposition import impose_jobs as impose_jobs
        if atomic_export is None:
            from production_service import atomic_production_export as atomic_export
    except Exception as exc:
        report['reasons'].append(f'无法导入生产引擎：{exc}')
        return report

    try:
        impose_sig = signature(impose_jobs)
        export_sig = signature(atomic_export)
    except Exception as exc:
        report['reasons'].append(f'无法读取生产函数签名：{exc}')
        return report

    report['engine'] = {
        'impose_jobs': str(impose_sig),
        'atomic_production_export': str(export_sig),
        'has_layout_override': 'layout_override' in impose_sig.parameters,
    }
    if 'layout_override' not in impose_sig.parameters:
        report['reasons'].append('impose_jobs 未暴露 layout_override 参数')
        return report

    try:
        hints = get_type_hints(impose_jobs)
        report['contract']['layout_override_annotation'] = str(hints.get('layout_override'))
    except Exception as exc:
        report['contract']['layout_override_annotation'] = ''
        report['reasons'].append(f'无法解析 layout_override 类型注解：{exc}')
        return report

    item_type = detect_layout_item_type(impose_jobs)
    if item_type is None:
        report['reasons'].append('layout_override 没有明确的 dataclass 元素类型')
        return report

    report['contract']['item_type'] = f'{item_type.__module__}.{item_type.__qualname__}'
    report['contract']['fields'] = [f.name for f in fields(item_type)]
    mapping = _semantic_map(item_type)
    report['contract']['semantic_mapping'] = mapping

    required = ('x', 'y', 'page_index', 'job_index')
    missing = [name for name in required if not mapping.get(name)]
    if missing:
        report['reasons'].append('缺少必要语义字段：' + ', '.join(missing))
        return report

    report['status'] = 'READY'
    report['reasons'].append('生产引擎公开了可安全识别的手工版位契约')
    return report


def format_layout_diagnostics(report: dict[str, Any]) -> str:
    lines = [f"手工版位生产状态：{report.get('status', 'BLOCKED')}"]
    engine = report.get('engine') or {}
    if engine:
        lines.append('')
        lines.append('生产函数：')
        lines.append(f"  impose_jobs {engine.get('impose_jobs', '')}")
        lines.append(f"  atomic_production_export {engine.get('atomic_production_export', '')}")
        lines.append(f"  layout_override 参数：{'有' if engine.get('has_layout_override') else '无'}")
    contract = report.get('contract') or {}
    if contract:
        lines.append('')
        lines.append('识别到的契约：')
        if contract.get('layout_override_annotation'):
            lines.append(f"  注解：{contract['layout_override_annotation']}")
        if contract.get('item_type'):
            lines.append(f"  元素类型：{contract['item_type']}")
        if contract.get('fields'):
            lines.append('  字段：' + ', '.join(contract['fields']))
        mapping = contract.get('semantic_mapping') or {}
        if mapping:
            lines.append('  语义映射：')
            for key in ('x','y','page_index','job_index','rotation','width','height'):
                lines.append(f"    {key} -> {mapping.get(key) or '未识别'}")
    reasons = report.get('reasons') or []
    if reasons:
        lines.append('')
        lines.append('结论：')
        for reason in reasons:
            lines.append('  - ' + str(reason))
    if report.get('status') != 'READY':
        lines.append('')
        lines.append('安全策略：当前继续阻止手工版位生产，自动拼版生产不受影响。')
    return '\n'.join(lines)
