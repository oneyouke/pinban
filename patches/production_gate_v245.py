from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from enhanced_preflight import scan_pdf
from print_marks import MarkConfig, JobMarkInfo, draw_on_fitz_page


def _job_path(job):
    return Path(getattr(job, 'path', job))


def run_enhanced_gate(jobs, *, min_dpi=250.0, min_bleed_mm=2.5):
    reports = []
    blocking = []
    warnings = []
    for job in jobs:
        path = _job_path(job)
        if path.suffix.lower() != '.pdf':
            continue
        report = scan_pdf(path, min_dpi=min_dpi, min_bleed_mm=min_bleed_mm)
        data = report.to_dict()
        reports.append(data)
        for issue in data.get('issues') or []:
            sev = str(issue.get('severity') or '').lower()
            msg = f"{path.name}: {issue.get('category','预检')} - {issue.get('message','')}"
            if sev == 'error':
                blocking.append(msg)
            elif sev == 'warning':
                warnings.append(msg)
    return {'reports': reports, 'blocking': blocking, 'warnings': warnings, 'ok': not blocking}


def _num(d, *keys):
    for key in keys:
        value = d.get(key) if isinstance(d, dict) else None
        if value is not None:
            try:
                return float(value)
            except Exception:
                pass
    return None


def extract_trim_boxes_mm(summary):
    if not isinstance(summary, dict):
        return []
    candidates = []
    for key in ('placements', 'layout', 'items', 'slots'):
        value = summary.get(key)
        if isinstance(value, list):
            candidates.extend(x for x in value if isinstance(x, dict))
    boxes = []
    for item in candidates:
        x = _num(item, 'x_mm', 'x', 'left_mm', 'left')
        y = _num(item, 'y_mm', 'y', 'top_mm', 'top')
        w = _num(item, 'width_mm', 'w_mm', 'width', 'w', 'trim_width_mm')
        h = _num(item, 'height_mm', 'h_mm', 'height', 'h', 'trim_height_mm')
        if None not in (x, y, w, h) and w > 0 and h > 0:
            box = (x, y, w, h)
            if box not in boxes:
                boxes.append(box)
    return boxes


def _cfg_from_settings(settings):
    raw = getattr(settings, 'print_marks', None)
    if isinstance(raw, dict):
        allowed = set(MarkConfig.__dataclass_fields__)
        return MarkConfig(**{k: v for k, v in raw.items() if k in allowed})
    cfg = MarkConfig()
    # Compatibility with existing flat settings if present.
    aliases = {
        'crop_marks': 'crop_marks', 'register_marks': 'register_marks',
        'color_bar': 'color_bar', 'gripper_edge': 'gripper_edge',
        'crop_length_mm': 'crop_length_mm', 'crop_offset_mm': 'crop_offset_mm',
        'crop_width_pt': 'crop_width_pt', 'mark_margin_mm': 'margin_mm',
    }
    for src, dst in aliases.items():
        if hasattr(settings, src):
            setattr(cfg, dst, getattr(settings, src))
    return cfg


def apply_vector_marks(pdf_path, settings, jobs, summary, *, plate_no=''):
    import fitz

    path = Path(pdf_path)
    sheet_w = float(getattr(settings, 'sheet_width_mm', 0) or 0)
    sheet_h = float(getattr(settings, 'sheet_height_mm', 0) or 0)
    if sheet_w <= 0 or sheet_h <= 0:
        return {'applied': False, 'warning': '无法读取纸张尺寸，已跳过矢量印刷标记', 'trim_boxes': 0}

    cfg = _cfg_from_settings(settings)
    boxes = extract_trim_boxes_mm(summary)
    names = ', '.join(dict.fromkeys(_job_path(j).name for j in jobs))
    doc = fitz.open(path)
    try:
        for index, page in enumerate(doc):
            side = 'FRONT' if index % 2 == 0 else 'BACK'
            draw_on_fitz_page(page, sheet_w, sheet_h, boxes, cfg,
                              JobMarkInfo(file_name=names, plate_no=plate_no or str(index + 1), side=side))
        tmp = path.with_name(path.name + '.marks.tmp.pdf')
        doc.save(tmp, garbage=3, deflate=True)
    finally:
        doc.close()
    tmp.replace(path)
    warning = None if boxes else '未从拼版摘要提取到逐件裁切框；已输出套准线/色标/版信息/咬口标记，未追加逐件裁切线'
    return {'applied': True, 'warning': warning, 'trim_boxes': len(boxes), 'config': asdict(cfg)}
