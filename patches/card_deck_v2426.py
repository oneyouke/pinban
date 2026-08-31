from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from io import BytesIO
from math import ceil
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from reportlab.pdfgen import canvas

from duplex import DuplexMode, Placement, map_backside, within_sheet


MM_TO_PT = 72.0 / 25.4


@dataclass(frozen=True)
class DeckValidation:
    okay: bool
    card_count: int
    duplicates: list[str]
    missing: list[str]
    unexpected: list[str]
    empty_positions: list[int]


@dataclass(frozen=True)
class CardPlacement:
    sheet: int
    side: str
    position: int
    card_index: int | None
    card_id: str | None
    source_page: int | None
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    rotation: int = 0


@dataclass(frozen=True)
class CardDeckPlan:
    card_count: int
    rows: int
    columns: int
    capacity: int
    sheet_count: int
    blank_cards: int
    common_back: bool
    flip: str
    placements: list[CardPlacement]


def _card_id(value):
    if isinstance(value, dict): value = value.get("id", value.get("card_id", ""))
    return str(value if value is not None else "").strip()


def load_card_manifest(path):
    path = Path(path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, list):
            cards, expected = payload, None
        elif isinstance(payload, dict):
            cards = payload.get("cards", payload.get("card_ids", []))
            expected = payload.get("expected_ids", payload.get("expected_cards"))
        else: raise ValueError("牌组 JSON 必须是数组或对象")
        return [_card_id(x) for x in cards], None if expected is None else [_card_id(x) for x in expected]
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows: raise ValueError("牌组 CSV 没有数据")
        fieldnames = set(rows[0])
        id_key = "card_id" if "card_id" in fieldnames else "id" if "id" in fieldnames else None
        if id_key is None: raise ValueError("牌组 CSV 必须包含 card_id 或 id 列")
        cards = [_card_id(row.get(id_key)) for row in rows]
        expected = [_card_id(row.get("expected_id")) for row in rows if _card_id(row.get("expected_id"))] if "expected_id" in fieldnames else None
        return cards, expected
    raise ValueError("牌组清单仅支持 JSON 或 CSV")


def validate_deck(card_ids, expected_ids=None):
    cards = [_card_id(x) for x in card_ids]
    counts = Counter(x for x in cards if x)
    duplicates = [x for x, count in counts.items() if count > 1]
    empty_positions = [index + 1 for index, value in enumerate(cards) if not value]
    expected = None if expected_ids is None else [_card_id(x) for x in expected_ids if _card_id(x)]
    expected_set = set(expected or [])
    missing = [] if expected is None else [x for x in dict.fromkeys(expected) if x not in counts]
    unexpected = [] if expected is None else [x for x in counts if x not in expected_set]
    okay = not duplicates and not empty_positions and not missing and not unexpected
    return DeckValidation(okay, len(cards), duplicates, missing, unexpected, empty_positions)


def _validation_message(result):
    parts = []
    if result.empty_positions: parts.append("空编号位置：" + ", ".join(map(str, result.empty_positions)))
    if result.duplicates: parts.append("重复牌：" + ", ".join(result.duplicates))
    if result.missing: parts.append("缺牌：" + ", ".join(result.missing))
    if result.unexpected: parts.append("多余牌：" + ", ".join(result.unexpected))
    return "；".join(parts) or "牌组清单通过"


def plan_card_deck(
    card_ids,
    *,
    sheet_width_mm,
    sheet_height_mm,
    trim_width_mm,
    trim_height_mm,
    rows,
    columns,
    gap_x_mm=0.0,
    gap_y_mm=0.0,
    common_back=True,
    flip=DuplexMode.LONG_EDGE.value,
):
    rows = int(rows); columns = int(columns); cards = [_card_id(x) for x in card_ids]
    if not cards: raise ValueError("牌组没有卡牌")
    if rows < 1 or columns < 1: raise ValueError("行列数必须大于 0")
    if min(sheet_width_mm, sheet_height_mm, trim_width_mm, trim_height_mm) <= 0: raise ValueError("纸张或卡牌尺寸无效")
    if gap_x_mm < 0 or gap_y_mm < 0: raise ValueError("版位间距不能小于 0")
    grid_width = columns * trim_width_mm + (columns - 1) * gap_x_mm
    grid_height = rows * trim_height_mm + (rows - 1) * gap_y_mm
    if grid_width > sheet_width_mm + 1e-9 or grid_height > sheet_height_mm + 1e-9:
        raise ValueError(f"{rows}×{columns} 牌位超出纸张：需要 {grid_width:.2f}×{grid_height:.2f} mm")
    origin_x = (sheet_width_mm - grid_width) / 2; origin_y = (sheet_height_mm - grid_height) / 2
    capacity = rows * columns; sheet_count = int(ceil(len(cards) / capacity)); placements = []
    flip_mode = DuplexMode(flip).value
    for sheet_index in range(sheet_count):
        for position in range(capacity):
            row, column = divmod(position, columns)
            card_index = sheet_index * capacity + position
            real = card_index < len(cards)
            x = origin_x + column * (trim_width_mm + gap_x_mm)
            y = sheet_height_mm - origin_y - (row + 1) * trim_height_mm - row * gap_y_mm
            placements.append(CardPlacement(
                sheet_index + 1, "front", position, card_index if real else None,
                cards[card_index] if real else None, card_index + 1 if real else None,
                x, y, trim_width_mm, trim_height_mm, 0,
            ))
            front_slot = Placement(x, y, trim_width_mm, trim_height_mm, 0)
            back_slot = map_backside(front_slot, sheet_width_mm, sheet_height_mm, flip_mode)
            if not within_sheet(back_slot, sheet_width_mm, sheet_height_mm): raise RuntimeError("背面牌位越出纸张")
            placements.append(CardPlacement(
                sheet_index + 1, "back", position, card_index if real else None,
                cards[card_index] if real else None,
                (1 if common_back else card_index + 1) if real else None,
                back_slot.x, back_slot.y, back_slot.width, back_slot.height, back_slot.rotation,
            ))
    return CardDeckPlan(len(cards), rows, columns, capacity, sheet_count, sheet_count * capacity - len(cards), bool(common_back), flip_mode, placements)


def _merge_fitted(sheet, source, placement):
    source_w = float(source.mediabox.width); source_h = float(source.mediabox.height)
    slot_w = placement.width_mm * MM_TO_PT; slot_h = placement.height_mm * MM_TO_PT
    scale = min(slot_w / source_w, slot_h / source_h)
    content_w, content_h = source_w * scale, source_h * scale
    local_x = (slot_w - content_w) / 2; local_y = (slot_h - content_h) / 2
    angle = int(placement.rotation) % 360
    if angle == 180:
        tx = placement.x_mm * MM_TO_PT + slot_w - local_x
        ty = placement.y_mm * MM_TO_PT + slot_h - local_y
    else:
        tx = placement.x_mm * MM_TO_PT + local_x; ty = placement.y_mm * MM_TO_PT + local_y
    sheet.merge_transformed_page(source, Transformation().scale(scale).rotate(angle).translate(tx, ty), over=True)


def _marks_overlay(width_pt, height_pt, placements, sheet_no, side, crop_marks):
    stream = BytesIO(); c = canvas.Canvas(stream, pagesize=(width_pt, height_pt), pageCompression=1)
    c.setStrokeColorCMYK(0, 0, 0, 1); c.setLineWidth(.35)
    if crop_marks:
        mark = 4 * MM_TO_PT; offset = 1 * MM_TO_PT
        for p in placements:
            if p.sheet != sheet_no or p.side != side: continue
            x, y = p.x_mm * MM_TO_PT, p.y_mm * MM_TO_PT; w, h = p.width_mm * MM_TO_PT, p.height_mm * MM_TO_PT
            for edge_x in (x, x + w):
                c.line(edge_x, max(0, y-offset-mark), edge_x, max(0, y-offset)); c.line(edge_x, min(height_pt, y+h+offset), edge_x, min(height_pt, y+h+offset+mark))
            for edge_y in (y, y + h):
                c.line(max(0, x-offset-mark), edge_y, max(0, x-offset), edge_y); c.line(min(width_pt, x+w+offset), edge_y, min(width_pt, x+w+offset+mark), edge_y)
    c.setFillColorCMYK(0, 0, 0, 1); c.setFont("Helvetica", 6)
    c.drawString(5, 5, f"CARD DECK / SHEET {sheet_no} / {side.upper()}")
    c.save(); stream.seek(0); return PdfReader(stream).pages[0]


def export_card_deck_pdf(
    front_pdf,
    back_pdf,
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
    common_back=True,
    flip=DuplexMode.LONG_EDGE.value,
    manifest_path=None,
    crop_marks=True,
):
    front_reader = PdfReader(str(front_pdf)); back_reader = PdfReader(str(back_pdf))
    front_count, back_count = len(front_reader.pages), len(back_reader.pages)
    if front_count < 1: raise ValueError("卡牌正面 PDF 没有页面")
    if common_back and back_count != 1: raise ValueError("通用背面模式要求背面 PDF 恰好 1 页")
    if not common_back and back_count != front_count: raise ValueError(f"逐牌背面要求 {front_count} 页，当前 {back_count} 页")
    if manifest_path:
        card_ids, expected_ids = load_card_manifest(manifest_path)
        if len(card_ids) != front_count: raise ValueError(f"牌组清单 {len(card_ids)} 项与正面 PDF {front_count} 页不一致")
    else:
        card_ids = [f"CARD-{index+1:03d}" for index in range(front_count)]; expected_ids = None
    validation = validate_deck(card_ids, expected_ids)
    if not validation.okay: raise ValueError(_validation_message(validation))
    plan = plan_card_deck(
        card_ids, sheet_width_mm=sheet_width_mm, sheet_height_mm=sheet_height_mm,
        trim_width_mm=trim_width_mm, trim_height_mm=trim_height_mm,
        rows=rows, columns=columns, gap_x_mm=gap_x_mm, gap_y_mm=gap_y_mm,
        common_back=common_back, flip=flip,
    )
    width_pt, height_pt = sheet_width_mm * MM_TO_PT, sheet_height_mm * MM_TO_PT; writer = PdfWriter()
    for sheet_no in range(1, plan.sheet_count + 1):
        for side, reader in (("front", front_reader), ("back", back_reader)):
            output = PageObject.create_blank_page(width=width_pt, height=height_pt)
            for placement in plan.placements:
                if placement.sheet == sheet_no and placement.side == side and placement.source_page is not None:
                    _merge_fitted(output, reader.pages[placement.source_page - 1], placement)
            output.merge_page(_marks_overlay(width_pt, height_pt, plan.placements, sheet_no, side, crop_marks)); writer.add_page(output)
    writer.add_metadata({
        "/Title": Path(front_pdf).stem + " - Card Deck Imposition",
        "/Subject": f"cards={front_count}; common_back={common_back}; flip={plan.flip}",
        "/Creator": "Desktop Imposer Pro",
    })
    output_path = Path(output_path); output_path.parent.mkdir(parents=True, exist_ok=True); temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary.open("wb") as handle: writer.write(handle); handle.flush()
    temporary.replace(output_path)
    verified = PdfReader(str(output_path)); expected_pages = plan.sheet_count * 2
    if len(verified.pages) != expected_pages: raise RuntimeError("卡牌正背大版页数校验失败")
    pairs = [{"card_id": card_ids[i], "front_page": i+1, "back_page": 1 if common_back else i+1} for i in range(front_count)]
    return {
        "output": str(output_path), "card_count": front_count, "sheet_count": plan.sheet_count,
        "output_pages": expected_pages, "capacity": plan.capacity, "blank_cards": plan.blank_cards,
        "common_back": bool(common_back), "flip": plan.flip, "validation": asdict(validation),
        "pairs": pairs, "placements": [asdict(x) for x in plan.placements],
    }
