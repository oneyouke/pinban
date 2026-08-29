from __future__ import annotations

from dataclasses import dataclass, asdict
from math import gcd
from functools import reduce


@dataclass(frozen=True)
class ProductSpec:
    key: str
    width_mm: float
    height_mm: float
    quantity: int = 1
    allow_rotate: bool = True


@dataclass
class PackedItem:
    key: str
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    rotation: int

    def to_dict(self):
        return asdict(self)


@dataclass
class PackResult:
    items: list[PackedItem]
    utilization: float
    used_area_mm2: float
    sheet_area_mm2: float
    packed_by_key: dict[str, int]
    requested_ratio: dict[str, int]
    strategy: str

    def to_dict(self):
        return {
            'items': [x.to_dict() for x in self.items],
            'utilization': self.utilization,
            'used_area_mm2': self.used_area_mm2,
            'sheet_area_mm2': self.sheet_area_mm2,
            'packed_by_key': dict(self.packed_by_key),
            'requested_ratio': dict(self.requested_ratio),
            'strategy': self.strategy,
        }


def _normalized_ratio(specs: list[ProductSpec]) -> dict[str, int]:
    qs = [max(1, int(s.quantity)) for s in specs]
    g = reduce(gcd, qs) if qs else 1
    return {s.key: max(1, int(s.quantity) // max(1, g)) for s in specs}


def _expanded_cycle(specs: list[ProductSpec], max_items=256):
    ratio = _normalized_ratio(specs)
    cycle = []
    by_key = {s.key: s for s in specs}
    for s in specs:
        cycle.extend([s.key] * ratio[s.key])
    if not cycle:
        return [], ratio
    out = []
    while len(out) + len(cycle) <= max_items:
        out.extend(cycle)
    if not out:
        out = cycle[:max_items]
    return [by_key[k] for k in out], ratio


def _shelf_pack(sequence, sheet_w, sheet_h, margin, gap_x, gap_y, rotate_policy, strategy):
    usable_left = margin
    usable_top = margin
    usable_right = sheet_w - margin
    usable_bottom = sheet_h - margin
    if usable_right <= usable_left or usable_bottom <= usable_top:
        return PackResult([], 0.0, 0.0, max(0.0, sheet_w * sheet_h), {}, {}, strategy)

    x, y = usable_left, usable_top
    shelf_h = 0.0
    placed = []
    counts = {}

    for spec in sequence:
        candidates = [(float(spec.width_mm), float(spec.height_mm), 0)]
        if spec.allow_rotate and abs(spec.width_mm - spec.height_mm) > 1e-9:
            candidates.append((float(spec.height_mm), float(spec.width_mm), 90))

        def score(c):
            w, h, rot = c
            fits_current = (x + w <= usable_right + 1e-9 and y + h <= usable_bottom + 1e-9)
            fits_new = (usable_left + w <= usable_right + 1e-9 and y + shelf_h + (gap_y if shelf_h else 0) + h <= usable_bottom + 1e-9)
            if rotate_policy == 'prefer_rotated': pref = 0 if rot == 90 else 1
            elif rotate_policy == 'prefer_normal': pref = 0 if rot == 0 else 1
            else: pref = 0
            return (0 if fits_current else 1 if fits_new else 2, pref, h, w)

        candidates.sort(key=score)
        chosen = None
        for w, h, rot in candidates:
            if x + w <= usable_right + 1e-9 and y + h <= usable_bottom + 1e-9:
                chosen = (w, h, rot, x, y)
                break
        if chosen is None:
            new_y = y + shelf_h + (gap_y if shelf_h else 0.0)
            for w, h, rot in candidates:
                if usable_left + w <= usable_right + 1e-9 and new_y + h <= usable_bottom + 1e-9:
                    x, y, shelf_h = usable_left, new_y, 0.0
                    chosen = (w, h, rot, x, y)
                    break
        if chosen is None:
            continue

        w, h, rot, px, py = chosen
        placed.append(PackedItem(spec.key, px, py, w, h, rot))
        counts[spec.key] = counts.get(spec.key, 0) + 1
        x = px + w + gap_x
        shelf_h = max(shelf_h, h)

    used = sum(i.width_mm * i.height_mm for i in placed)
    area = max(0.0, sheet_w * sheet_h)
    return PackResult(placed, used / area if area else 0.0, used, area, counts, {}, strategy)


def optimize_mixed(specs: list[ProductSpec], sheet_width_mm: float, sheet_height_mm: float,
                   margin_mm: float = 5.0, gap_x_mm: float = 2.0, gap_y_mm: float = 2.0,
                   max_items: int = 256) -> PackResult:
    specs = [s for s in specs if s.width_mm > 0 and s.height_mm > 0 and int(s.quantity) > 0]
    if not specs:
        return PackResult([], 0.0, 0.0, max(0.0, sheet_width_mm * sheet_height_mm), {}, {}, 'empty')

    sequence, ratio = _expanded_cycle(specs, max_items=max_items)
    sorters = {
        'area_desc': lambda s: -(s.width_mm * s.height_mm),
        'height_desc': lambda s: -max(s.height_mm, s.width_mm),
        'width_desc': lambda s: -max(s.width_mm, s.height_mm),
        'ratio_cycle': lambda s: 0,
    }
    results = []
    for name, sorter in sorters.items():
        seq = list(sequence) if name == 'ratio_cycle' else sorted(sequence, key=sorter)
        for rot_policy in ('auto', 'prefer_normal', 'prefer_rotated'):
            r = _shelf_pack(seq, float(sheet_width_mm), float(sheet_height_mm), float(margin_mm),
                            float(gap_x_mm), float(gap_y_mm), rot_policy, f'{name}/{rot_policy}')
            r.requested_ratio = ratio
            results.append(r)

    # Prefer more placed items first, then higher utilization, then closer adherence to requested ratio.
    def ratio_error(r):
        if not r.items:
            return 10**9
        total = sum(r.packed_by_key.values()) or 1
        req_total = sum(ratio.values()) or 1
        return sum(abs(r.packed_by_key.get(k, 0) / total - v / req_total) for k, v in ratio.items())

    results.sort(key=lambda r: (-len(r.items), -r.utilization, ratio_error(r), r.strategy))
    return results[0]
