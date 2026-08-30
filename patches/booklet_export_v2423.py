from __future__ import annotations

from dataclasses import asdict
from io import BytesIO
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from reportlab.pdfgen import canvas

from booklet import perfect_bound_sections, saddle_stitch


MM_TO_PT = 72.0 / 25.4


def _merge_fitted(destination, source, x, y, width, height, inset=0.0):
    x += inset; y += inset; width -= inset*2; height -= inset*2
    source_w = float(source.mediabox.width); source_h = float(source.mediabox.height)
    if source_w <= 0 or source_h <= 0 or width <= 0 or height <= 0:
        raise ValueError("页面或版位尺寸无效")
    scale = min(width/source_w, height/source_h)
    tx = x + (width-source_w*scale)/2
    ty = y + (height-source_h*scale)/2
    destination.merge_transformed_page(source, Transformation().scale(scale).translate(tx, ty), over=True)


def _marks_overlay(width_pt, height_pt, fold_x_pt, spread, draw_fold_lines=True):
    stream = BytesIO(); c = canvas.Canvas(stream, pagesize=(width_pt, height_pt))
    c.setLineWidth(.45); c.setStrokeColorCMYK(0, .85, 0, 0)
    if draw_fold_lines:
        c.setDash(3, 2); c.line(fold_x_pt, 0, fold_x_pt, height_pt); c.setDash()
    mark = 9
    c.setStrokeColorCMYK(0, 0, 0, 1)
    for x in (0, width_pt):
        direction = 1 if x == 0 else -1
        c.line(x, height_pt/2, x+direction*mark, height_pt/2)
    c.setFont("Helvetica", 6)
    label = f"SIG {spread.signature} / SHEET {spread.sheet} / {spread.side.upper()} / CREEP {spread.creep_mm:.3f} mm"
    c.drawCentredString(width_pt/2, 5, label); c.save(); stream.seek(0)
    return PdfReader(stream).pages[0]


def export_booklet_pdf(
    source_path,
    output_path,
    *,
    binding="骑马订",
    signature_pages=16,
    sheet_width_mm=450.0,
    sheet_height_mm=320.0,
    spine_mm=0.0,
    creep_per_sheet_mm=0.0,
    flip="长边翻",
    draw_fold_lines=True,
    safe_inset_mm=3.0,
):
    source_path = Path(source_path); output_path = Path(output_path)
    reader = PdfReader(str(source_path)); page_count = len(reader.pages)
    if page_count < 1: raise ValueError("书籍 PDF 没有页面")
    if sheet_width_mm <= 0 or sheet_height_mm <= 0: raise ValueError("纸张尺寸无效")
    if spine_mm < 0 or spine_mm >= sheet_width_mm: raise ValueError("书脊宽度无效")
    if binding == "骑马订": sections = [saddle_stitch(page_count, creep_per_sheet_mm)]
    else: sections = perfect_bound_sections(page_count, int(signature_pages), creep_per_sheet_mm)
    spreads = [spread for section in sections for spread in section]
    width_pt, height_pt = sheet_width_mm*MM_TO_PT, sheet_height_mm*MM_TO_PT
    spine_pt = spine_mm*MM_TO_PT; slot_w = (width_pt-spine_pt)/2
    inset_pt = max(0.0, safe_inset_mm)*MM_TO_PT
    writer = PdfWriter()
    for spread in spreads:
        sheet = PageObject.create_blank_page(width=width_pt, height=height_pt)
        creep_pt = spread.creep_mm*MM_TO_PT
        slots = (
            (spread.left, 0.0+creep_pt, slot_w-creep_pt, "left"),
            (spread.right, slot_w+spine_pt, slot_w-creep_pt, "right"),
        )
        for page_number, x, slot_width, side in slots:
            if page_number is None: continue
            if side == "right": x += 0.0
            source = reader.pages[int(page_number)-1]
            _merge_fitted(sheet, source, x, 0, slot_width, height_pt, inset_pt)
        overlay = _marks_overlay(width_pt, height_pt, width_pt/2, spread, draw_fold_lines)
        sheet.merge_page(overlay)
        if spread.side == "back" and flip in ("短边翻", "天地翻"):
            sheet.rotate(180)
        writer.add_page(sheet)
    writer.add_metadata({
        "/Title": source_path.stem+" - Booklet Imposition",
        "/Subject": f"{binding}; {len(sections)} signatures; {flip}",
        "/Creator": "Desktop Imposer Pro",
    })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp = output_path.with_suffix(output_path.suffix+".tmp")
    with temp.open("wb") as handle: writer.write(handle); handle.flush()
    temp.replace(output_path)
    verified = PdfReader(str(output_path))
    if len(verified.pages) != len(spreads):
        raise RuntimeError("书籍拼版输出页数校验失败")
    return {
        "output": str(output_path), "source_pages": page_count,
        "signature_count": len(sections), "physical_sheets": len(spreads)//2,
        "output_pages": len(spreads), "binding": binding, "flip": flip,
        "sheet_width_mm": sheet_width_mm, "sheet_height_mm": sheet_height_mm,
        "spine_mm": spine_mm, "creep_per_sheet_mm": creep_per_sheet_mm,
        "spreads": [asdict(x) for x in spreads],
    }
