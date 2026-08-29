from __future__ import annotations

from dataclasses import dataclass, asdict
from math import ceil, floor
from typing import Literal

Unit = Literal["mm", "cm", "in", "pt"]

_MM_PER_UNIT = {"mm": 1.0, "cm": 10.0, "in": 25.4, "pt": 25.4 / 72.0}


def to_mm(value: float, unit: Unit) -> float:
    if unit not in _MM_PER_UNIT:
        raise ValueError(f"unsupported unit: {unit}")
    return float(value) * _MM_PER_UNIT[unit]


def from_mm(value_mm: float, unit: Unit) -> float:
    if unit not in _MM_PER_UNIT:
        raise ValueError(f"unsupported unit: {unit}")
    return float(value_mm) / _MM_PER_UNIT[unit]


@dataclass(frozen=True)
class SheetSpec:
    width_mm: float
    height_mm: float
    margin_left_mm: float = 0.0
    margin_right_mm: float = 0.0
    margin_top_mm: float = 0.0
    margin_bottom_mm: float = 0.0
    gripper_mm: float = 0.0
    gripper_edge: Literal["top", "bottom", "left", "right"] = "bottom"

    def usable_size(self) -> tuple[float, float]:
        w = self.width_mm - self.margin_left_mm - self.margin_right_mm
        h = self.height_mm - self.margin_top_mm - self.margin_bottom_mm
        if self.gripper_mm < 0:
            raise ValueError("gripper cannot be negative")
        if self.gripper_edge in ("left", "right"):
            w -= self.gripper_mm
        else:
            h -= self.gripper_mm
        if w <= 0 or h <= 0:
            raise ValueError("margins/gripper leave no usable sheet area")
        return w, h


@dataclass(frozen=True)
class ProductSpec:
    width_mm: float
    height_mm: float
    bleed_mm: float = 0.0
    gap_x_mm: float = 0.0
    gap_y_mm: float = 0.0


@dataclass(frozen=True)
class FitResult:
    rotated: bool
    cols: int
    rows: int
    count: int
    footprint_width_mm: float
    footprint_height_mm: float
    used_width_mm: float
    used_height_mm: float
    usable_width_mm: float
    usable_height_mm: float
    utilization_percent: float
    leftover_width_mm: float
    leftover_height_mm: float
    fits: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _count_axis(usable: float, item: float, gap: float) -> int:
    if item <= 0:
        raise ValueError("item size must be positive")
    if gap < 0:
        raise ValueError("gap cannot be negative")
    if usable < item:
        return 0
    return max(0, floor((usable + gap + 1e-9) / (item + gap)))


def calculate_fit(sheet: SheetSpec, product: ProductSpec, *, rotated: bool = False) -> FitResult:
    usable_w, usable_h = sheet.usable_size()
    trim_w = product.height_mm if rotated else product.width_mm
    trim_h = product.width_mm if rotated else product.height_mm
    if trim_w <= 0 or trim_h <= 0:
        raise ValueError("product size must be positive")
    if product.bleed_mm < 0:
        raise ValueError("bleed cannot be negative")

    footprint_w = trim_w + 2.0 * product.bleed_mm
    footprint_h = trim_h + 2.0 * product.bleed_mm
    cols = _count_axis(usable_w, footprint_w, product.gap_x_mm)
    rows = _count_axis(usable_h, footprint_h, product.gap_y_mm)
    count = cols * rows
    used_w = cols * footprint_w + max(0, cols - 1) * product.gap_x_mm if cols else 0.0
    used_h = rows * footprint_h + max(0, rows - 1) * product.gap_y_mm if rows else 0.0
    used_area = count * footprint_w * footprint_h
    utilization = (used_area / (sheet.width_mm * sheet.height_mm) * 100.0) if sheet.width_mm > 0 and sheet.height_mm > 0 else 0.0
    return FitResult(
        rotated=rotated,
        cols=cols,
        rows=rows,
        count=count,
        footprint_width_mm=round(footprint_w, 6),
        footprint_height_mm=round(footprint_h, 6),
        used_width_mm=round(used_w, 6),
        used_height_mm=round(used_h, 6),
        usable_width_mm=round(usable_w, 6),
        usable_height_mm=round(usable_h, 6),
        utilization_percent=round(utilization, 4),
        leftover_width_mm=round(max(0.0, usable_w - used_w), 6),
        leftover_height_mm=round(max(0.0, usable_h - used_h), 6),
        fits=count > 0,
    )


def recommend_orientation(sheet: SheetSpec, product: ProductSpec) -> dict:
    normal = calculate_fit(sheet, product, rotated=False)
    rotated = calculate_fit(sheet, product, rotated=True)
    def score(r: FitResult) -> tuple[int, float, float]:
        # Prefer more copies; then higher material utilization; then less remaining linear waste.
        return (r.count, r.utilization_percent, -(r.leftover_width_mm + r.leftover_height_mm))
    best = rotated if score(rotated) > score(normal) else normal
    return {"recommended": "rotated" if best.rotated else "normal", "normal": normal.to_dict(), "rotated": rotated.to_dict()}


@dataclass(frozen=True)
class ProductionPlan:
    order_quantity: int
    copies_per_sheet: int
    base_sheets: int
    make_ready_sheets: int
    waste_rate_percent: float
    waste_sheets: int
    total_sheets: int
    gross_products: int
    surplus_products: int

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_production_plan(order_quantity: int, copies_per_sheet: int, *, make_ready_sheets: int = 0, waste_rate_percent: float = 0.0) -> ProductionPlan:
    order_quantity = int(order_quantity)
    copies_per_sheet = int(copies_per_sheet)
    make_ready_sheets = int(make_ready_sheets)
    if order_quantity < 0:
        raise ValueError("order quantity cannot be negative")
    if copies_per_sheet <= 0:
        raise ValueError("copies per sheet must be positive")
    if make_ready_sheets < 0:
        raise ValueError("make-ready sheets cannot be negative")
    if waste_rate_percent < 0:
        raise ValueError("waste rate cannot be negative")

    base = ceil(order_quantity / copies_per_sheet) if order_quantity else 0
    waste = ceil(base * (float(waste_rate_percent) / 100.0)) if base else 0
    total = base + make_ready_sheets + waste
    gross = total * copies_per_sheet
    surplus = max(0, gross - order_quantity)
    return ProductionPlan(order_quantity, copies_per_sheet, base, make_ready_sheets, float(waste_rate_percent), waste, total, gross, surplus)
