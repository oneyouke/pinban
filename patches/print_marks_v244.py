from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

PT_PER_MM = 72.0 / 25.4


def mm(v: float) -> float:
    return float(v) * PT_PER_MM


@dataclass
class MarkConfig:
    crop_marks: bool = True
    register_marks: bool = True
    color_bar: bool = True
    file_name: bool = True
    plate_no: bool = True
    date: bool = True
    side_label: bool = True
    gripper_arrow: bool = True
    crop_length_mm: float = 5.0
    crop_offset_mm: float = 2.0
    crop_width_pt: float = 0.25
    register_radius_mm: float = 3.0
    text_size_pt: float = 7.0
    gripper_edge: str = "top"
    margin_mm: float = 6.0


@dataclass
class JobMarkInfo:
    file_name: str = ""
    plate_no: str = ""
    side: str = "FRONT"
    date_text: str = ""

    def resolved_date(self) -> str:
        return self.date_text or datetime.now().strftime("%Y-%m-%d %H:%M")


def crop_segments(x: float, y: float, w: float, h: float, cfg: MarkConfig):
    off = cfg.crop_offset_mm
    ln = cfg.crop_length_mm
    return [
        ((x-off-ln, y), (x-off, y)), ((x, y-off-ln), (x, y-off)),
        ((x+w+off, y), (x+w+off+ln, y)), ((x+w, y-off-ln), (x+w, y-off)),
        ((x-off-ln, y+h), (x-off, y+h)), ((x, y+h+off), (x, y+h+off+ln)),
        ((x+w+off, y+h), (x+w+off+ln, y+h)), ((x+w, y+h+off), (x+w, y+h+off+ln)),
    ]


def registration_centers(sheet_w: float, sheet_h: float, cfg: MarkConfig):
    m = cfg.margin_mm
    return [(sheet_w/2, m), (sheet_w/2, sheet_h-m), (m, sheet_h/2), (sheet_w-m, sheet_h/2)]


def color_bar_rects(sheet_w: float, sheet_h: float, cfg: MarkConfig):
    cell_w, cell_h = 8.0, 5.0
    total = 4 * cell_w
    x = max(cfg.margin_mm, (sheet_w-total)/2)
    y = max(1.0, sheet_h-cfg.margin_mm-cell_h)
    return [(x+i*cell_w, y, cell_w, cell_h, name) for i, name in enumerate(("C","M","Y","K"))]


def info_lines(info: JobMarkInfo, cfg: MarkConfig):
    out = []
    if cfg.file_name and info.file_name: out.append(info.file_name)
    if cfg.plate_no and info.plate_no: out.append(f"PLATE {info.plate_no}")
    if cfg.side_label: out.append(info.side.upper())
    if cfg.date: out.append(info.resolved_date())
    return out


def gripper_arrow(sheet_w: float, sheet_h: float, cfg: MarkConfig):
    edge = cfg.gripper_edge.lower()
    s = 6.0
    cx, cy = sheet_w/2, sheet_h/2
    if edge == "top": return [(cx, cfg.margin_mm+s), (cx-s/2, cfg.margin_mm+2*s), (cx+s/2, cfg.margin_mm+2*s)]
    if edge == "bottom": return [(cx, sheet_h-cfg.margin_mm-s), (cx-s/2, sheet_h-cfg.margin_mm-2*s), (cx+s/2, sheet_h-cfg.margin_mm-2*s)]
    if edge == "left": return [(cfg.margin_mm+s, cy), (cfg.margin_mm+2*s, cy-s/2), (cfg.margin_mm+2*s, cy+s/2)]
    return [(sheet_w-cfg.margin_mm-s, cy), (sheet_w-cfg.margin_mm-2*s, cy-s/2), (sheet_w-cfg.margin_mm-2*s, cy+s/2)]


def draw_on_fitz_page(page, sheet_w_mm: float, sheet_h_mm: float, trim_boxes_mm, cfg: MarkConfig, info: JobMarkInfo):
    """Draw vector marks directly into a PyMuPDF page. Coordinates are in mm."""
    import fitz

    black = (0, 0, 0)
    if cfg.crop_marks:
        for x, y, w, h in trim_boxes_mm:
            for a, b in crop_segments(x, y, w, h, cfg):
                page.draw_line(fitz.Point(mm(a[0]), mm(a[1])), fitz.Point(mm(b[0]), mm(b[1])), color=black, width=cfg.crop_width_pt)

    if cfg.register_marks:
        r = mm(cfg.register_radius_mm)
        for cx, cy in registration_centers(sheet_w_mm, sheet_h_mm, cfg):
            p = fitz.Point(mm(cx), mm(cy))
            page.draw_circle(p, r, color=black, width=0.35)
            page.draw_line(fitz.Point(p.x-r*1.5, p.y), fitz.Point(p.x+r*1.5, p.y), color=black, width=0.25)
            page.draw_line(fitz.Point(p.x, p.y-r*1.5), fitz.Point(p.x, p.y+r*1.5), color=black, width=0.25)

    if cfg.color_bar:
        colors = {"C": (0,1,1), "M": (1,0,1), "Y": (1,1,0), "K": (0,0,0)}
        for x, y, w, h, name in color_bar_rects(sheet_w_mm, sheet_h_mm, cfg):
            rect = fitz.Rect(mm(x), mm(y), mm(x+w), mm(y+h))
            page.draw_rect(rect, color=black, fill=colors[name], width=0.2)

    lines = info_lines(info, cfg)
    if lines:
        x = mm(cfg.margin_mm)
        y = mm(max(cfg.margin_mm+8, 12))
        for line in lines:
            page.insert_text(fitz.Point(x, y), line, fontsize=cfg.text_size_pt, color=black)
            y += cfg.text_size_pt + 2

    if cfg.gripper_arrow:
        pts = gripper_arrow(sheet_w_mm, sheet_h_mm, cfg)
        shape = page.new_shape()
        p0 = fitz.Point(mm(pts[0][0]), mm(pts[0][1]))
        p1 = fitz.Point(mm(pts[1][0]), mm(pts[1][1]))
        p2 = fitz.Point(mm(pts[2][0]), mm(pts[2][1]))
        shape.draw_polyline([p0, p1, p2, p0])
        shape.finish(color=black, fill=black, width=0.25)
        shape.commit()

    return page
