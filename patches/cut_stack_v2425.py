from __future__ import annotations

from dataclasses import asdict, dataclass
from io import BytesIO
from math import ceil
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from reportlab.pdfgen import canvas

from duplex import DuplexMode, Placement, map_backside, within_sheet


MM_TO_PT = 72.0 / 25.4


@dataclass(frozen=True)
class CutStackPlacement:
    sheet: int
    side: str
    position: int
    row: int
    column: int
    page: int | None
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    rotation: int = 0


@dataclass(frozen=True)
class CutStackPlan:
    page_count: int
    rows: int
    columns: int
    capacity: int
    sheet_count: int
    duplex: bool
    padded_pages: int
    blank_pages: int
    stack_order: str
    flip: str
    placements: list[CutStackPlacement]


def _position_cells(rows, columns, order):
    if order == "column_major":
        return [(row, column) for column in range(columns) for row in range(rows)]
    if order != "row_major":
        raise ValueError("叠堆顺序必须是 row_major 或 column_major")
    return [(row, column) for row in range(rows) for column in range(columns)]


def plan_cut_stack(
    page_count,
    *,
    sheet_width_mm,
    sheet_height_mm,
    trim_width_mm,
    trim_height_mm,
    rows,
    columns,
    gap_x_mm=0.0,
    gap_y_mm=0.0,
    duplex=False,
    flip=DuplexMode.LONG_EDGE.value,
    stack_order="row_major",
):
    page_count = int(page_count); rows = int(rows); columns = int(columns)
    if page_count < 1: raise ValueError("源 PDF 没有页面")
    if rows < 1 or columns < 1: raise ValueError("行列数必须大于 0")
    if min(sheet_width_mm, sheet_height_mm, trim_width_mm, trim_height_mm) <= 0: raise ValueError("纸张或成品尺寸无效")
    if gap_x_mm < 0 or gap_y_mm < 0: raise ValueError("版位间距不能小于 0")
    capacity = rows * columns
    pages_per_sheet = capacity * (2 if duplex else 1)
    sheet_count = int(ceil(page_count / pages_per_sheet))
    padded_pages = sheet_count * pages_per_sheet
    grid_width = columns * trim_width_mm + (columns - 1) * gap_x_mm
    grid_height = rows * trim_height_mm + (rows - 1) * gap_y_mm
    if grid_width > sheet_width_mm + 1e-9 or grid_height > sheet_height_mm + 1e-9:
        raise ValueError(f"{rows}×{columns} 版位超出纸张：需要 {grid_width:.2f}×{grid_height:.2f} mm")
    origin_x = (sheet_width_mm - grid_width) / 2
    origin_y = (sheet_height_mm - grid_height) / 2
    cells = _position_cells(rows, columns, stack_order)
    placements = []
    pile_span = sheet_count * (2 if duplex else 1)
    flip_mode = DuplexMode(flip).value
    for sheet_index in range(sheet_count):
        for position, (row, column) in enumerate(cells):
            x = origin_x + column * (trim_width_mm + gap_x_mm)
            y = sheet_height_mm - origin_y - (row + 1) * trim_height_mm - row * gap_y_mm
            front_number = position * pile_span + sheet_index * (2 if duplex else 1) + 1
            front_page = front_number if front_number <= page_count else None
            placements.append(CutStackPlacement(
                sheet_index + 1, "front", position, row, column, front_page,
                x, y, trim_width_mm, trim_height_mm, 0,
            ))
            if duplex:
                front_slot = Placement(x, y, trim_width_mm, trim_height_mm, 0)
                back_slot = map_backside(front_slot, sheet_width_mm, sheet_height_mm, flip_mode)
                if not within_sheet(back_slot, sheet_width_mm, sheet_height_mm): raise RuntimeError("反面版位越出纸张")
                back_number = front_number + 1
                back_page = back_number if back_number <= page_count else None
                placements.append(CutStackPlacement(
                    sheet_index + 1, "back", position, row, column, back_page,
                    back_slot.x, back_slot.y, back_slot.width, back_slot.height, back_slot.rotation,
                ))
    return CutStackPlan(
        page_count, rows, columns, capacity, sheet_count, bool(duplex), padded_pages,
        padded_pages - page_count, stack_order, flip_mode, placements,
    )


def reconstruct_cut_sequence(plan):
    sequence = []
    for position in range(plan.capacity):
        for sheet in range(1, plan.sheet_count + 1):
            for side in (("front", "back") if plan.duplex else ("front",)):
                match = next(p for p in plan.placements if p.position == position and p.sheet == sheet and p.side == side)
                sequence.append(match.page)
    return sequence


def _merge_fitted(sheet, source, placement):
    source_w = float(source.mediabox.width); source_h = float(source.mediabox.height)
    slot_w = placement.width_mm * MM_TO_PT; slot_h = placement.height_mm * MM_TO_PT
    if min(source_w, source_h, slot_w, slot_h) <= 0: raise ValueError("源页面或版位尺寸无效")
    scale = min(slot_w / source_w, slot_h / source_h)
    content_w, content_h = source_w * scale, source_h * scale
    local_x = (slot_w - content_w) / 2; local_y = (slot_h - content_h) / 2
    angle = int(placement.rotation) % 360
    if angle == 180:
        tx = (placement.x_mm * MM_TO_PT) + slot_w - local_x
        ty = (placement.y_mm * MM_TO_PT) + slot_h - local_y
    else:
        tx = placement.x_mm * MM_TO_PT + local_x
        ty = placement.y_mm * MM_TO_PT + local_y
    transform = Transformation().scale(scale).rotate(angle).translate(tx, ty)
    sheet.merge_transformed_page(source, transform, over=True)


def _marks_overlay(width_pt, height_pt, placements, sheet, side, crop_marks):
    stream = BytesIO(); c = canvas.Canvas(stream, pagesize=(width_pt, height_pt), pageCompression=1)
    c.setStrokeColorCMYK(0, 0, 0, 1); c.setLineWidth(.35)
    if crop_marks:
        mark = 4 * MM_TO_PT; offset = 1 * MM_TO_PT
        for p in placements:
            if p.sheet != sheet or p.side != side: continue
            x = p.x_mm * MM_TO_PT; y = p.y_mm * MM_TO_PT
            w = p.width_mm * MM_TO_PT; h = p.height_mm * MM_TO_PT
            for edge_x in (x, x + w):
                c.line(edge_x, max(0, y - offset - mark), edge_x, max(0, y - offset))
                c.line(edge_x, min(height_pt, y + h + offset), edge_x, min(height_pt, y + h + offset + mark))
            for edge_y in (y, y + h):
                c.line(max(0, x - offset - mark), edge_y, max(0, x - offset), edge_y)
                c.line(min(width_pt, x + w + offset), edge_y, min(width_pt, x + w + offset + mark), edge_y)
    c.setFillColorCMYK(0, 0, 0, 1); c.setFont("Helvetica", 6)
    c.drawString(5, 5, f"CUT & STACK / SHEET {sheet} / {side.upper()}")
    c.save(); stream.seek(0)
    return PdfReader(stream).pages[0]


def export_cut_stack_pdf(
    source_path,
    output_path,
    *,
    sheet_width_mm,
    sheet_height_mm,
    trim_width_mm,
    trim_height_mm,
    rows,
    columns,
    gap_x_mm=0.0,
    gap_y_mm=0.0,
    duplex=False,
    flip=DuplexMode.LONG_EDGE.value,
    stack_order="row_major",
    crop_marks=True,
):
    source_path = Path(source_path); output_path = Path(output_path)
    reader = PdfReader(str(source_path))
    plan = plan_cut_stack(
        len(reader.pages), sheet_width_mm=sheet_width_mm, sheet_height_mm=sheet_height_mm,
        trim_width_mm=trim_width_mm, trim_height_mm=trim_height_mm,
        rows=rows, columns=columns, gap_x_mm=gap_x_mm, gap_y_mm=gap_y_mm,
        duplex=duplex, flip=flip, stack_order=stack_order,
    )
    expected = list(range(1, plan.page_count + 1))
    actual = [p for p in reconstruct_cut_sequence(plan) if p is not None]
    if actual != expected: raise RuntimeError("切叠页序校验失败")
    width_pt = sheet_width_mm * MM_TO_PT; height_pt = sheet_height_mm * MM_TO_PT
    writer = PdfWriter()
    for sheet_number in range(1, plan.sheet_count + 1):
        for side in (("front", "back") if plan.duplex else ("front",)):
            output_page = PageObject.create_blank_page(width=width_pt, height=height_pt)
            side_placements = [p for p in plan.placements if p.sheet == sheet_number and p.side == side]
            for placement in side_placements:
                if placement.page is not None: _merge_fitted(output_page, reader.pages[placement.page - 1], placement)
            output_page.merge_page(_marks_overlay(width_pt, height_pt, plan.placements, sheet_number, side, crop_marks))
            writer.add_page(output_page)
    writer.add_metadata({
        "/Title": source_path.stem + " - Cut and Stack",
        "/Subject": f"{plan.rows}x{plan.columns}; duplex={plan.duplex}; flip={plan.flip}; order={plan.stack_order}",
        "/Creator": "Desktop Imposer Pro",
    })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary.open("wb") as handle: writer.write(handle); handle.flush()
    temporary.replace(output_path)
    verified = PdfReader(str(output_path)); expected_output = plan.sheet_count * (2 if plan.duplex else 1)
    if len(verified.pages) != expected_output: raise RuntimeError("切叠输出页数校验失败")
    return {
        "output": str(output_path), "source_pages": plan.page_count,
        "sheet_count": plan.sheet_count, "output_pages": expected_output,
        "capacity": plan.capacity, "blank_pages": plan.blank_pages,
        "duplex": plan.duplex, "flip": plan.flip, "stack_order": plan.stack_order,
        "placements": [asdict(p) for p in plan.placements],
    }
