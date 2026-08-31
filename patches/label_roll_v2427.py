from __future__ import annotations

from dataclasses import asdict, dataclass
from io import BytesIO
from math import ceil, floor
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from reportlab.lib.colors import CMYKColorSep
from reportlab.pdfgen import canvas


MM_TO_PT = 72.0 / 25.4
DIRECTION_ROTATION = {"head_out": 0, "right_out": 90, "tail_out": 180, "left_out": 270}


@dataclass(frozen=True)
class RollPlacement:
    output_page: int
    repeat_cycle: int
    lane: int
    repeat: int
    copy_number: int
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    rotation: int


@dataclass(frozen=True)
class LabelRollPlan:
    quantity: int
    web_width_mm: float
    repeat_length_mm: float
    lanes: int
    repeats_per_cycle: int
    capacity_per_cycle: int
    cycle_count: int
    blank_positions: int
    direction: str
    winding: str
    slit_x_mm: list[float]
    cross_waste_mm: float
    repeat_waste_mm: float
    utilization_percent: float
    placements: list[RollPlacement]


def plan_label_roll(
    quantity,
    *,
    web_width_mm,
    repeat_length_mm,
    label_width_mm,
    label_height_mm,
    lanes,
    lane_gap_mm=3.0,
    repeat_gap_mm=3.0,
    direction="head_out",
    winding="outside",
):
    quantity = int(quantity); lanes = int(lanes)
    if quantity < 1: raise ValueError("标签数量必须大于 0")
    if lanes < 1: raise ValueError("分条数必须大于 0")
    if min(web_width_mm, repeat_length_mm, label_width_mm, label_height_mm) <= 0: raise ValueError("卷材、周长或标签尺寸无效")
    if lane_gap_mm < 0 or repeat_gap_mm < 0: raise ValueError("标签间距不能小于 0")
    if direction not in DIRECTION_ROTATION: raise ValueError("不支持的出标方向")
    if winding not in ("outside", "inside"): raise ValueError("卷绕方式必须是 outside 或 inside")
    rotation = DIRECTION_ROTATION[direction]
    footprint_w, footprint_h = (label_width_mm, label_height_mm) if rotation in (0, 180) else (label_height_mm, label_width_mm)
    used_cross = lanes * footprint_w + (lanes - 1) * lane_gap_mm
    if used_cross > web_width_mm + 1e-9:
        raise ValueError(f"{lanes} 条超出卷材宽度：需要 {used_cross:.2f} mm，当前 {web_width_mm:.2f} mm")
    repeats = int(floor((repeat_length_mm + repeat_gap_mm) / (footprint_h + repeat_gap_mm)))
    if repeats < 1: raise ValueError("版辊重复周长无法容纳 1 枚标签")
    used_repeat = repeats * footprint_h + (repeats - 1) * repeat_gap_mm
    capacity = lanes * repeats; cycles = int(ceil(quantity / capacity))
    cross_origin = (web_width_mm - used_cross) / 2; repeat_origin = (repeat_length_mm - used_repeat) / 2
    logical_cycles = list(range(1, cycles + 1))
    if winding == "inside": logical_cycles.reverse()
    placements = []
    for output_page, cycle in enumerate(logical_cycles, 1):
        first_copy = (cycle - 1) * capacity + 1
        for repeat in range(repeats):
            for lane in range(lanes):
                copy_number = first_copy + repeat * lanes + lane
                if copy_number > quantity: continue
                placements.append(RollPlacement(
                    output_page, cycle, lane + 1, repeat + 1, copy_number,
                    cross_origin + lane * (footprint_w + lane_gap_mm),
                    repeat_origin + repeat * (footprint_h + repeat_gap_mm),
                    footprint_w, footprint_h, rotation,
                ))
    slit_x = [cross_origin + lane * footprint_w + (lane - .5) * lane_gap_mm for lane in range(1, lanes)]
    used_area = quantity * label_width_mm * label_height_mm
    total_area = cycles * web_width_mm * repeat_length_mm
    return LabelRollPlan(
        quantity, float(web_width_mm), float(repeat_length_mm), lanes, repeats, capacity, cycles,
        cycles * capacity - quantity, direction, winding, slit_x,
        float(web_width_mm - used_cross), float(repeat_length_mm - used_repeat),
        used_area / total_area * 100, placements,
    )


def _merge_label(sheet, source, placement, label_width_mm, label_height_mm):
    source_w, source_h = float(source.mediabox.width), float(source.mediabox.height)
    base_w, base_h = label_width_mm * MM_TO_PT, label_height_mm * MM_TO_PT
    scale = min(base_w / source_w, base_h / source_h)
    content_w, content_h = source_w * scale, source_h * scale
    local_x, local_y = (base_w - content_w) / 2, (base_h - content_h) / 2
    angle = placement.rotation % 360
    if angle == 90: tx, ty = base_h - local_y, local_x
    elif angle == 180: tx, ty = base_w - local_x, base_h - local_y
    elif angle == 270: tx, ty = local_y, base_w - local_x
    else: tx, ty = local_x, local_y
    transform = Transformation().scale(scale).rotate(angle).translate(
        placement.x_mm * MM_TO_PT + tx, placement.y_mm * MM_TO_PT + ty,
    )
    sheet.merge_transformed_page(source, transform, over=True)


def _overlay(width_pt, height_pt, plan, output_page, draw_slit_lines, draw_die_lines):
    stream = BytesIO(); c = canvas.Canvas(stream, pagesize=(width_pt, height_pt), pageCompression=1)
    c.setStrokeColorCMYK(0, 0, 0, 1); c.setLineWidth(.35); c.rect(0, 0, width_pt, height_pt, stroke=1, fill=0)
    page_placements = [p for p in plan.placements if p.output_page == output_page]
    if draw_die_lines:
        c.setStrokeColor(CMYKColorSep(0, 100, 0, 0, spotName="CutContour", density=1)); c.setLineWidth(.55)
        for p in page_placements: c.rect(p.x_mm*MM_TO_PT, p.y_mm*MM_TO_PT, p.width_mm*MM_TO_PT, p.height_mm*MM_TO_PT, stroke=1, fill=0)
    if draw_slit_lines:
        c.setStrokeColor(CMYKColorSep(100, 0, 0, 0, spotName="SlitLine", density=1)); c.setLineWidth(.45); c.setDash(4, 2)
        for x in plan.slit_x_mm: c.line(x*MM_TO_PT, 0, x*MM_TO_PT, height_pt)
        c.setDash()
    c.setFillColorCMYK(0, 0, 0, 1); c.setFont("Helvetica", 5.5)
    for p in page_placements: c.drawString(p.x_mm*MM_TO_PT+2, p.y_mm*MM_TO_PT+2, f"#{p.copy_number}")
    cycle = page_placements[0].repeat_cycle if page_placements else output_page
    c.setFont("Helvetica", 6); c.drawString(5, 5, f"LABEL ROLL / CYCLE {cycle} / {plan.direction} / {plan.winding}")
    c.save(); stream.seek(0); return PdfReader(stream).pages[0]


def export_label_roll_pdf(
    source_pdf,
    output_path,
    *,
    quantity,
    web_width_mm,
    repeat_length_mm,
    label_width_mm,
    label_height_mm,
    lanes,
    lane_gap_mm=3.0,
    repeat_gap_mm=3.0,
    direction="head_out",
    winding="outside",
    draw_slit_lines=True,
    draw_die_lines=True,
):
    reader = PdfReader(str(source_pdf))
    if len(reader.pages) < 1: raise ValueError("标签 PDF 没有页面")
    plan = plan_label_roll(
        quantity, web_width_mm=web_width_mm, repeat_length_mm=repeat_length_mm,
        label_width_mm=label_width_mm, label_height_mm=label_height_mm, lanes=lanes,
        lane_gap_mm=lane_gap_mm, repeat_gap_mm=repeat_gap_mm,
        direction=direction, winding=winding,
    )
    if plan.cycle_count > 10000: raise ValueError("输出重复页超过 10000，请拆分生产批次")
    width_pt, height_pt = web_width_mm * MM_TO_PT, repeat_length_mm * MM_TO_PT; writer = PdfWriter()
    source = reader.pages[0]
    for output_page in range(1, plan.cycle_count + 1):
        page = PageObject.create_blank_page(width=width_pt, height=height_pt)
        for placement in plan.placements:
            if placement.output_page == output_page: _merge_label(page, source, placement, label_width_mm, label_height_mm)
        page.merge_page(_overlay(width_pt, height_pt, plan, output_page, draw_slit_lines, draw_die_lines)); writer.add_page(page)
    writer.add_metadata({
        "/Title": Path(source_pdf).stem + " - Label Roll",
        "/Subject": f"web={web_width_mm}; repeat={repeat_length_mm}; lanes={lanes}; direction={direction}; winding={winding}",
        "/Creator": "Desktop Imposer Pro",
    })
    output_path = Path(output_path); output_path.parent.mkdir(parents=True, exist_ok=True); temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary.open("wb") as handle: writer.write(handle); handle.flush()
    temporary.replace(output_path)
    verified = PdfReader(str(output_path))
    if len(verified.pages) != plan.cycle_count: raise RuntimeError("卷筒标签输出重复页数校验失败")
    payload = output_path.read_bytes()
    if draw_die_lines and (b"/Separation" not in payload or b"CutContour" not in payload): raise RuntimeError("标签模切专色写入校验失败")
    if draw_slit_lines and b"SlitLine" not in payload: raise RuntimeError("标签分条专色写入校验失败")
    return {**asdict(plan), "output": str(output_path), "output_pages": plan.cycle_count,
            "draw_slit_lines": bool(draw_slit_lines), "draw_die_lines": bool(draw_die_lines)}
