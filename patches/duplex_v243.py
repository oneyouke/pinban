from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DuplexMode(str, Enum):
    LEFT_RIGHT = "left_right"
    TOP_BOTTOM = "top_bottom"
    LONG_EDGE = "long_edge"
    SHORT_EDGE = "short_edge"
    SELF_TURN = "self_turn"


@dataclass(frozen=True)
class Placement:
    x: float
    y: float
    width: float
    height: float
    rotation: int = 0


def _mirror_x(p: Placement, sheet_w: float) -> Placement:
    return Placement(sheet_w - p.x - p.width, p.y, p.width, p.height, (-p.rotation) % 360)


def _mirror_y(p: Placement, sheet_h: float) -> Placement:
    return Placement(p.x, sheet_h - p.y - p.height, p.width, p.height, (-p.rotation) % 360)


def _rotate_180(p: Placement, sheet_w: float, sheet_h: float) -> Placement:
    return Placement(sheet_w - p.x - p.width, sheet_h - p.y - p.height,
                     p.width, p.height, (p.rotation + 180) % 360)


def map_backside(p: Placement, sheet_w: float, sheet_h: float,
                 mode: DuplexMode | str) -> Placement:
    """Map a front-side placement to its backside registration position.

    Geometry is expressed in sheet millimetres. The mapping is intentionally
    deterministic and involutive so applying the same flip twice returns to
    the original placement.
    """
    mode = DuplexMode(mode)
    if sheet_w <= 0 or sheet_h <= 0:
        raise ValueError("sheet dimensions must be positive")

    if mode == DuplexMode.LEFT_RIGHT:
        return _mirror_x(p, sheet_w)
    if mode == DuplexMode.TOP_BOTTOM:
        return _mirror_y(p, sheet_h)
    if mode == DuplexMode.LONG_EDGE:
        # Flip around the physical long edge: landscape -> top/bottom,
        # portrait -> left/right.
        return _mirror_y(p, sheet_h) if sheet_w >= sheet_h else _mirror_x(p, sheet_w)
    if mode == DuplexMode.SHORT_EDGE:
        return _mirror_x(p, sheet_w) if sheet_w >= sheet_h else _mirror_y(p, sheet_h)
    if mode == DuplexMode.SELF_TURN:
        return _rotate_180(p, sheet_w, sheet_h)
    raise ValueError(f"unsupported duplex mode: {mode}")


def within_sheet(p: Placement, sheet_w: float, sheet_h: float, tolerance: float = 1e-6) -> bool:
    return (
        p.x >= -tolerance and p.y >= -tolerance and
        p.x + p.width <= sheet_w + tolerance and
        p.y + p.height <= sheet_h + tolerance
    )
