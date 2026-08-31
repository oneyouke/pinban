from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from reportlab.lib.colors import CMYKColorSep
from reportlab.pdfgen import canvas
from shapely.geometry import Polygon


MM_TO_PT = 72.0 / 25.4


def _safe_spot_name(value):
    name = re.sub(r"[\x00-\x1f\x7f]+", "", str(value or "").strip())
    return name[:80] or "CutContour"


def _rotated_points(points, angle):
    transformed = []
    for x, y in points:
        if angle == 90:
            rx, ry = -y, x
        elif angle == 180:
            rx, ry = -x, -y
        elif angle == 270:
            rx, ry = y, -x
        else:
            rx, ry = x, y
        transformed.append((float(rx), float(ry)))
    min_x = min(x for x, _ in transformed)
    min_y = min(y for _, y in transformed)
    return [(x - min_x, y - min_y) for x, y in transformed]


def _draw_polygon(c, points, x_mm, y_mm):
    path = c.beginPath()
    first_x, first_y = points[0]
    path.moveTo((x_mm + first_x) * MM_TO_PT, (y_mm + first_y) * MM_TO_PT)
    for px, py in points[1:]:
        path.lineTo((x_mm + px) * MM_TO_PT, (y_mm + py) * MM_TO_PT)
    path.close()
    c.drawPath(path, stroke=1, fill=0)


def _sheet_overlay(width_pt, height_pt, points, placements, sheet_no, spot_name, bleed_mm):
    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=(width_pt, height_pt), pageCompression=1)
    c.setLineWidth(0.55)
    c.setStrokeColorCMYK(0, 0, 0, 1)
    c.rect(0, 0, width_pt, height_pt, stroke=1, fill=0)
    for placement in placements:
        if int(placement.sheet) != sheet_no:
            continue
        rotated = _rotated_points(points, int(placement.rotation) % 360)
        if bleed_mm > 0:
            bleed = Polygon(rotated).buffer(float(bleed_mm), join_style=2)
            if not bleed.is_empty:
                exterior = list(bleed.exterior.coords)[:-1]
                c.setStrokeColorCMYK(0, 0.75, 0, 0)
                c.setLineWidth(0.35)
                c.setDash(2.5, 1.5)
                _draw_polygon(c, exterior, placement.x_mm, placement.y_mm)
                c.setDash()
        c.setStrokeColor(CMYKColorSep(0, 100, 0, 0, spotName=spot_name, density=1))
        c.setLineWidth(0.7)
        _draw_polygon(c, rotated, placement.x_mm, placement.y_mm)
        center_x = placement.x_mm + (min(x for x, _ in rotated) + max(x for x, _ in rotated)) / 2
        center_y = placement.y_mm + (min(y for _, y in rotated) + max(y for _, y in rotated)) / 2
        c.setFillColorCMYK(0, 0, 0, 1)
        c.setFont("Helvetica", 5.5)
        c.drawCentredString(center_x * MM_TO_PT, center_y * MM_TO_PT, str(placement.copy_index + 1))
    c.setFillColorCMYK(0, 0, 0, 1)
    c.setFont("Helvetica", 6)
    c.drawString(5, 5, f"SHEET {sheet_no} / SPOT {spot_name} / BLEED {bleed_mm:.2f} mm")
    c.save(); stream.seek(0)
    return PdfReader(stream).pages[0]


def _merge_pdf_artwork(sheet, source_page, points, placement):
    base_w = max(x for x, _ in points) - min(x for x, _ in points)
    base_h = max(y for _, y in points) - min(y for _, y in points)
    if base_w <= 0 or base_h <= 0:
        raise ValueError("刀模轮廓尺寸无效")
    source_w = float(source_page.mediabox.width)
    source_h = float(source_page.mediabox.height)
    if source_w <= 0 or source_h <= 0:
        raise ValueError("刀模 PDF 页面尺寸无效")
    angle = int(placement.rotation) % 360
    if angle == 90:
        offset_x, offset_y = base_h, 0.0
    elif angle == 180:
        offset_x, offset_y = base_w, base_h
    elif angle == 270:
        offset_x, offset_y = 0.0, base_w
    else:
        offset_x = offset_y = 0.0
    transform = (
        Transformation()
        .scale(base_w * MM_TO_PT / source_w, base_h * MM_TO_PT / source_h)
        .rotate(angle)
        .translate((placement.x_mm + offset_x) * MM_TO_PT, (placement.y_mm + offset_y) * MM_TO_PT)
    )
    sheet.merge_transformed_page(source_page, transform, over=True)


def export_box_pdf(
    source_path,
    points,
    plan,
    output_path,
    *,
    sheet_width_mm,
    sheet_height_mm,
    bleed_mm=3.0,
    spot_name="CutContour",
):
    source_path = Path(source_path)
    output_path = Path(output_path)
    if not points or len(points) < 3:
        raise ValueError("刀模轮廓至少需要 3 个点")
    if plan is None or not plan.placements or plan.sheet_count < 1:
        raise ValueError("请先完成异形套料")
    if sheet_width_mm <= 0 or sheet_height_mm <= 0:
        raise ValueError("纸张尺寸无效")
    if bleed_mm < 0:
        raise ValueError("出血不能小于 0")
    spot_name = _safe_spot_name(spot_name)
    artwork = PdfReader(str(source_path)).pages[0] if source_path.suffix.lower() == ".pdf" else None
    width_pt = float(sheet_width_mm) * MM_TO_PT
    height_pt = float(sheet_height_mm) * MM_TO_PT
    writer = PdfWriter()
    for sheet_no in range(1, int(plan.sheet_count) + 1):
        sheet = PageObject.create_blank_page(width=width_pt, height=height_pt)
        if artwork is not None:
            for placement in plan.placements:
                if int(placement.sheet) == sheet_no:
                    _merge_pdf_artwork(sheet, artwork, points, placement)
        overlay = _sheet_overlay(width_pt, height_pt, points, plan.placements, sheet_no, spot_name, float(bleed_mm))
        sheet.merge_page(overlay)
        writer.add_page(sheet)
    writer.add_metadata({
        "/Title": source_path.stem + " - Box Imposition",
        "/Subject": f"Die nesting; spot {spot_name}; bleed {bleed_mm:.2f} mm",
        "/Creator": "Desktop Imposer Pro",
    })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        writer.write(handle)
        handle.flush()
    temporary.replace(output_path)
    verified = PdfReader(str(output_path))
    if len(verified.pages) != int(plan.sheet_count):
        raise RuntimeError("盒型拼版输出页数校验失败")
    payload = output_path.read_bytes()
    if b"/Separation" not in payload:
        raise RuntimeError("刀线专色写入校验失败")
    return {
        "output": str(output_path),
        "sheet_count": int(plan.sheet_count),
        "placement_count": len(plan.placements),
        "sheet_width_mm": float(sheet_width_mm),
        "sheet_height_mm": float(sheet_height_mm),
        "bleed_mm": float(bleed_mm),
        "spot_name": spot_name,
        "vector_artwork": artwork is not None,
    }
