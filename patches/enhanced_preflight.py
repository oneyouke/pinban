from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import math

from pypdf import PdfReader
from pypdf.generic import ContentStream

PT_PER_MM = 72.0 / 25.4


@dataclass
class PreflightIssue:
    severity: str
    category: str
    message: str
    page: int | None = None
    suggestion: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class PreflightReport:
    path: str
    page_count: int
    issues: list[PreflightIssue]
    stats: dict

    def to_dict(self):
        return {
            "path": self.path,
            "page_count": self.page_count,
            "issues": [i.to_dict() for i in self.issues],
            "stats": self.stats,
        }


def _obj(value):
    try:
        return value.get_object()
    except Exception:
        return value


def _box_tuple(box):
    try:
        return tuple(float(x) for x in box)
    except Exception:
        return None


def _font_embedded(font):
    font = _obj(font)
    if not font:
        return False
    descriptor = _obj(font.get("/FontDescriptor"))
    if descriptor is None:
        descendants = _obj(font.get("/DescendantFonts")) or []
        if descendants:
            descriptor = _obj(_obj(descendants[0]).get("/FontDescriptor"))
    if descriptor:
        return any(descriptor.get(k) is not None for k in ("/FontFile", "/FontFile2", "/FontFile3"))
    return False


def _color_names(value):
    value = _obj(value)
    found = set()
    if isinstance(value, str):
        found.add(value)
    elif isinstance(value, (list, tuple)):
        for item in value:
            found |= _color_names(item)
    elif hasattr(value, "items"):
        for _, item in value.items():
            found |= _color_names(item)
    return found


def _concat(m, n):
    a,b,c,d,e,f = m
    A,B,C,D,E,F = n
    return (
        a*A + c*B,
        b*A + d*B,
        a*C + c*D,
        b*C + d*D,
        a*E + c*F + e,
        b*E + d*F + f,
    )


def _effective_image_dpi(page, reader, resources, issues, page_no, min_dpi, stats):
    try:
        contents = page.get_contents()
        if not contents:
            return
        stream = ContentStream(contents, reader)
    except Exception:
        return
    xobjects = _obj(resources.get("/XObject")) if resources else None
    if not xobjects:
        return

    ctm = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    stack = []
    for operands, operator in stream.operations:
        try:
            if operator == b"q":
                stack.append(ctm)
            elif operator == b"Q":
                if stack:
                    ctm = stack.pop()
            elif operator == b"cm" and len(operands) >= 6:
                n = tuple(float(v) for v in operands[:6])
                ctm = _concat(ctm, n)
            elif operator == b"Do" and operands:
                name = operands[0]
                xo = _obj(xobjects.get(name))
                if not xo or xo.get("/Subtype") != "/Image":
                    continue
                px_w = float(xo.get("/Width", 0) or 0)
                px_h = float(xo.get("/Height", 0) or 0)
                disp_w_pt = math.hypot(ctm[0], ctm[1])
                disp_h_pt = math.hypot(ctm[2], ctm[3])
                if px_w <= 0 or px_h <= 0 or disp_w_pt <= 0.01 or disp_h_pt <= 0.01:
                    continue
                dpi_x = px_w * 72.0 / disp_w_pt
                dpi_y = px_h * 72.0 / disp_h_pt
                dpi = min(dpi_x, dpi_y)
                stats["images_checked"] += 1
                stats["min_effective_dpi"] = dpi if stats["min_effective_dpi"] is None else min(stats["min_effective_dpi"], dpi)
                if dpi < min_dpi:
                    issues.append(PreflightIssue(
                        "warning", "图片DPI",
                        f"图片 {name} 有效分辨率约 {dpi:.0f} DPI，低于 {min_dpi:.0f} DPI",
                        page_no,
                        "建议替换更高分辨率原图，或减小该图片在版面中的实际输出尺寸。",
                    ))
        except Exception:
            continue


def scan_pdf(path: str | Path, *, min_dpi: float = 250.0, min_bleed_mm: float = 2.5) -> PreflightReport:
    path = Path(path)
    issues: list[PreflightIssue] = []
    stats = {
        "fonts_checked": 0,
        "fonts_unembedded": 0,
        "rgb_detected": False,
        "spot_colors": [],
        "overprint_detected": False,
        "transparency_detected": False,
        "images_checked": 0,
        "min_effective_dpi": None,
        "mixed_page_sizes": False,
    }
    try:
        reader = PdfReader(str(path), strict=False)
    except Exception as exc:
        return PreflightReport(str(path), 0, [PreflightIssue("error", "文件", f"PDF 无法读取：{exc}", None, "请重新导出 PDF 或使用专业修复工具检查文件结构。")], stats)

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            issues.append(PreflightIssue("error", "文件", "PDF 已加密，无法完整预检", None, "请提供未加密的生产 PDF。"))
            return PreflightReport(str(path), len(reader.pages), issues, stats)

    first_trim = None
    seen_fonts = set()
    seen_spots = set()

    for idx, page in enumerate(reader.pages, 1):
        media = _box_tuple(page.mediabox)
        crop = _box_tuple(page.cropbox)
        trim = _box_tuple(page.get("/TrimBox")) or crop or media
        bleed = _box_tuple(page.get("/BleedBox"))

        if trim:
            size = (round(trim[2]-trim[0], 2), round(trim[3]-trim[1], 2))
            if first_trim is None:
                first_trim = size
            elif abs(size[0]-first_trim[0]) > 1.5 or abs(size[1]-first_trim[1]) > 1.5:
                stats["mixed_page_sizes"] = True
                issues.append(PreflightIssue("warning", "页面尺寸", f"页面成品尺寸 {size[0]/PT_PER_MM:.1f} × {size[1]/PT_PER_MM:.1f} mm 与首页不同", idx, "确认是否为有意混合尺寸；若是画册/册子，建议统一 TrimBox。"))

        if page.get("/TrimBox") is None:
            issues.append(PreflightIssue("warning", "页面框", "缺少 TrimBox（成品框）", idx, "建议在源文件或专业 PDF 工具中设置准确成品框。"))
        if bleed is None:
            issues.append(PreflightIssue("warning", "出血", "缺少 BleedBox（出血框）", idx, f"建议至少设置 {min_bleed_mm:.1f} mm 出血，并确认内容真实延伸到出血区域。"))
        elif trim:
            left = (trim[0]-bleed[0]) / PT_PER_MM
            bottom = (trim[1]-bleed[1]) / PT_PER_MM
            right = (bleed[2]-trim[2]) / PT_PER_MM
            top = (bleed[3]-trim[3]) / PT_PER_MM
            minimum = min(left, bottom, right, top)
            if minimum < min_bleed_mm - 0.05:
                issues.append(PreflightIssue("warning", "出血", f"最小出血约 {minimum:.2f} mm，低于 {min_bleed_mm:.1f} mm", idx, "回源文件补足出血；不要仅扩大页面框冒充真实出血。"))

        rotation = int(page.get("/Rotate", 0) or 0) % 360
        if rotation not in (0, 90, 180, 270):
            issues.append(PreflightIssue("warning", "页面旋转", f"页面旋转角度为 {rotation}°", idx, "建议规范为 0/90/180/270° 后再进入拼版流程。"))

        resources = _obj(page.get("/Resources")) or {}
        fonts = _obj(resources.get("/Font")) or {}
        for key, font_ref in fonts.items():
            font = _obj(font_ref)
            base = str(font.get("/BaseFont", key)) if font else str(key)
            ident = (base, getattr(font_ref, "idnum", None))
            if ident in seen_fonts:
                continue
            seen_fonts.add(ident)
            stats["fonts_checked"] += 1
            if not _font_embedded(font_ref):
                stats["fonts_unembedded"] += 1
                issues.append(PreflightIssue("error", "字体", f"字体 {base} 未检测到嵌入字库", idx, "建议回源文件嵌入字体或转曲；不要在生产端随意替换字体。"))

        color_names = _color_names(resources.get("/ColorSpace"))
        xobjects = _obj(resources.get("/XObject")) or {}
        for _, xref in xobjects.items():
            xo = _obj(xref)
            if xo and xo.get("/Subtype") == "/Image":
                color_names |= _color_names(xo.get("/ColorSpace"))
        if "/DeviceRGB" in color_names or "/CalRGB" in color_names:
            stats["rgb_detected"] = True
            issues.append(PreflightIssue("warning", "颜色", "检测到 RGB 色彩空间", idx, "印刷前确认色彩管理策略；如需纯 CMYK 生产，请由受控 ICC/专业 Provider 转换。"))
        if "/Separation" in color_names or "/DeviceN" in color_names:
            for name in color_names:
                if name not in ("/Separation", "/DeviceN", "/DeviceRGB", "/DeviceCMYK", "/DeviceGray") and name.startswith("/"):
                    seen_spots.add(name[1:])

        ext = _obj(resources.get("/ExtGState")) or {}
        for _, gs_ref in ext.items():
            gs = _obj(gs_ref) or {}
            if bool(gs.get("/OP", False)) or bool(gs.get("/op", False)):
                stats["overprint_detected"] = True
            try:
                if float(gs.get("/ca", 1) or 1) < 0.999 or float(gs.get("/CA", 1) or 1) < 0.999:
                    stats["transparency_detected"] = True
            except Exception:
                pass
            bm = gs.get("/BM")
            if bm not in (None, "/Normal"):
                stats["transparency_detected"] = True

        _effective_image_dpi(page, reader, resources, issues, idx, min_dpi, stats)

    stats["spot_colors"] = sorted(seen_spots)
    if stats["overprint_detected"]:
        issues.append(PreflightIssue("info", "叠印", "检测到叠印设置", None, "建议在专业分色预览中核对黑色、专色及套印对象，防止意外镂空或叠印。"))
    if stats["transparency_detected"]:
        issues.append(PreflightIssue("info", "透明度", "检测到透明度/混合模式", None, "现代 PDF/RIP 通常可直接处理；旧 RIP 或特殊工艺请做透明度兼容性验证。"))
    if seen_spots:
        issues.append(PreflightIssue("info", "专色", "检测到专色/DeviceN 资源：" + ", ".join(sorted(seen_spots)[:12]), None, "确认专色命名、白墨/光油/烫金版及输出分色策略。"))
    if not issues:
        issues.append(PreflightIssue("info", "结果", "未发现内置规则可识别的明显风险", None, "正式生产前仍建议执行打样、分色预览及设备端 RIP 检查。"))
    return PreflightReport(str(path), len(reader.pages), issues, stats)


def scan_paths(paths, *, min_dpi=250.0, min_bleed_mm=2.5):
    reports = []
    for p in paths:
        path = Path(p)
        if path.suffix.lower() == ".pdf":
            reports.append(scan_pdf(path, min_dpi=min_dpi, min_bleed_mm=min_bleed_mm))
        else:
            reports.append(PreflightReport(str(path), 0, [PreflightIssue("info", "文件格式", f"{path.suffix or '未知格式'} 使用现有图像/转换 Provider 预检", None, "TIFF/JPG 检查分辨率与色彩模式；AI/EPS/PS 建议先由受控转换 Provider 生成 PDF。")], {}))
    return reports
