from __future__ import annotations

import json
import tempfile
import traceback
from dataclasses import asdict
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib.colors import CMYKColorSep
from reportlab.pdfgen import canvas
from shapely import affinity
from shapely.geometry import Polygon

from booklet import flat_sheet_pairs, perfect_bound_sections, saddle_stitch
from duplex import DuplexMode, Placement, map_backside
from imposition import (
    ImpositionSettings, InputJob, analyze_pdf_prepress, calculate_grid,
    impose_jobs, plan_smart_layout,
)
from nesting import NestItem, nest_polygons_multi_sheet
from product import APP_VERSION


RESULTS = []


def record(category, case_id, name, status, detail, evidence=""):
    RESULTS.append({
        "category": category, "case_id": case_id, "name": name,
        "status": status, "detail": detail, "evidence": evidence,
    })


def check(category, case_id, name, fn):
    try:
        detail, evidence = fn()
        record(category, case_id, name, "PASS", detail, evidence)
    except Exception as exc:
        record(category, case_id, name, "FAIL", str(exc), traceback.format_exc(limit=4))


def sample_pdf(path: Path, pages: int, width_mm=90, height_mm=54):
    c = canvas.Canvas(str(path), pagesize=(width_mm*72/25.4, height_mm*72/25.4))
    for index in range(pages):
        c.drawString(20, 20, f"PAGE-{index+1}"); c.showPage()
    c.save()


def check_booklet():
    spreads = saddle_stitch(14, .15)
    assert len(spreads) == 8
    assert (spreads[0].left, spreads[0].right) == (None, 1)
    assert (spreads[1].left, spreads[1].right) == (2, None)
    assert abs(spreads[-2].creep_mm - .45) < 1e-9
    sections = perfect_bound_sections(38, 16, .1)
    assert len(sections) == 3 and sections[-1][0].signature == 3
    real_pages = [p for section in sections for spread in section for p in (spread.left, spread.right) if p]
    assert sorted(real_pages) == list(range(1, 39))
    return "14P骑马订补白、38P分帖及逐张爬移页序正确", f"spreads={len(spreads)}, signatures={len(sections)}"


def check_commercial(tmp):
    src = tmp/"flyer.pdf"; out = tmp/"flyer-imposed.pdf"; sample_pdf(src, 1, 100, 70)
    settings = ImpositionSettings(sheet_width_mm=450, sheet_height_mm=320, trim_width_mm=100, trim_height_mm=70, copies_per_page=12, auto_rotate=True, crop_marks=True)
    grid = calculate_grid(settings); summary = impose_jobs([InputJob(src, 12, 100, 70, 0, "宣传单")], out, settings)
    assert grid.capacity >= 12 and summary["total_items"] == 12
    assert len(PdfReader(str(out)).pages) == summary["sheet_count"]
    return "商业单页自动模数、数量和生产PDF页数一致", f"capacity={grid.capacity}, sheets={summary['sheet_count']}"


def check_cards(tmp):
    src = tmp/"cards.pdf"; out = tmp/"cards-duplex.pdf"; sample_pdf(src, 2, 90, 54)
    settings = ImpositionSettings(sheet_width_mm=450, sheet_height_mm=320, trim_width_mm=90, trim_height_mm=54, copies_per_page=20, duplex=True, duplex_flip="long")
    summary = impose_jobs([InputJob(src, 20, 90, 54, 0, "双面卡")], out, settings)
    assert summary["duplex"] and summary["output_pages"] == summary["sheet_count"]*2
    front = Placement(10, 20, 90, 54, 0); back = map_backside(front, 450, 320, DuplexMode.LONG_EDGE.value)
    assert back.x >= 0 and back.y >= 0
    return "双面卡片正背输出页数和长边翻版坐标有效", f"output_pages={summary['output_pages']}"


def check_labels():
    points = [(0,0),(42,0),(52,18),(42,36),(0,36),(8,18)]
    item = NestItem("label", points, 18, (0,180))
    plan = nest_polygons_multi_sheet([item], 220, 160, gap_mm=3, step_mm=2)
    assert len(plan.placements) == 18 and all(0 < u <= 1 for u in plan.utilization)
    base = Polygon(points); by_sheet = {}
    for p in plan.placements:
        poly = affinity.rotate(base, p.rotation, origin=(0,0)); minx,miny,_,_=poly.bounds
        poly = affinity.translate(poly, p.x_mm-minx, p.y_mm-miny)
        by_sheet.setdefault(p.sheet, []).append(poly)
    for polys in by_sheet.values():
        for i,a in enumerate(polys):
            assert all(not a.intersects(b) for b in polys[i+1:])
    return "18枚异形标签按真实多边形完成多张套料且无轮廓相交", f"sheets={plan.sheet_count}, utilization={plan.utilization}"


def check_packaging(tmp):
    path = tmp/"cut-signal.pdf"; c = canvas.Canvas(str(path), pagesize=(300,200))
    c.setStrokeColor(CMYKColorSep(0,1,0,0,spotName="CutContour")); c.rect(20,20,240,150,stroke=1,fill=0); c.showPage(); c.save()
    report = analyze_pdf_prepress(path)
    assert "CutContour" in report["spot_colors"]
    assert "CutContour" in report["production_inks"]["cut"]
    return "彩盒CutContour专色刀线可识别并归类为模切工艺", "spot=CutContour, class=cut"


def check_special():
    pairs = flat_sheet_pairs(7, duplex=True)
    pages = [p for spread in pairs for p in (spread.left, spread.right) if p]
    assert sorted(pages) == list(range(1,8)) and any(p is None for spread in pairs for p in (spread.left,spread.right))
    return "7页票据/活页双面顺序无缺页并正确补白", f"spreads={len(pairs)}"


def check_digital(tmp):
    a=tmp/"digital-a.pdf"; b=tmp/"digital-b.pdf"; out=tmp/"digital-mix.pdf"
    sample_pdf(a,1,90,54); sample_pdf(b,1,50,90)
    jobs=[InputJob(a,17,90,54,0,"A"),InputJob(b,9,50,90,0,"B")]
    settings=ImpositionSettings(sheet_width_mm=450,sheet_height_mm=320,smart_mixed_sizes=True,auto_rotate=True,gap_x_mm=3,gap_y_mm=3)
    layout=plan_smart_layout(jobs,settings,[1,1]); summary=impose_jobs(jobs,out,settings)
    assert summary["total_items"]==26 and layout["expected_keys"]
    assert len(PdfReader(str(out)).pages)==summary["sheet_count"]
    return "数码异尺寸动态合版数量、布局键和输出页数一致", f"sheets={summary['sheet_count']}, utilization={summary['utilization_percent']:.1f}%"


def add_known_gaps():
    gaps = [
        ("书刊画册类","BOOK-PROD-001","书籍折手直接输出生产PDF","BLOCKED","当前书籍模式已完成页序、正背预览和JSON，但尚未生成按折手页序放置的生产PDF。"),
        ("商业单页类","COMM-CUTSTACK-001","裁切堆叠专用模式","BLOCKED","引擎具备普通拼版和混拼，尚无独立Cut & Stack裁切路径及堆叠顺序输出。"),
        ("卡片类","CARD-DECK-001","整副卡牌配对与缺牌检测","BLOCKED","已有通用双面卡片拼版，尚无牌组清单、通用背面及缺牌/重复牌验收器。"),
        ("不干胶标签类","LABEL-ROLL-001","卷筒方向、分条和重复周长","BLOCKED","已有异形套料，尚无卷材宽度、出标方向、内外卷、分条和版辊周长模型。"),
        ("彩盒包装类","BOX-PROD-001","刀模与印刷稿合成生产PDF","BLOCKED","已有刀模导入、套料与方案JSON，尚未输出保留CutContour/Crease专色的复合生产PDF。"),
        ("特种产品","SPECIAL-PRESET-001","特种产品工艺模板库","BLOCKED","尚无信封、纸袋、NCR、烫金、击凸及激光切割的专用参数模板。"),
        ("数码印刷拼版","DIGITAL-CONTINUOUS-001","卷筒连续纸和断点续印","BLOCKED","已有平张混拼和可变数据，尚无卷长、分卷、续号与断点恢复模型。"),
    ]
    for category, case_id, name, status, detail in gaps: record(category,case_id,name,status,detail)


def write_reports(output: Path):
    output.mkdir(parents=True,exist_ok=True)
    counts={s:sum(r["status"]==s for r in RESULTS) for s in ("PASS","FAIL","BLOCKED")}
    payload={"software_version":APP_VERSION,"level":"P0","summary":counts,"results":RESULTS}
    (output/"PRINT_CATEGORY_P0_REPORT.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=[f"# 印刷品类 P0 自动化验收报告", "", f"- 软件版本：V{APP_VERSION}", f"- 结论：PASS {counts['PASS']} / FAIL {counts['FAIL']} / BLOCKED {counts['BLOCKED']}", "", "| 品类 | 用例 | 检查项 | 状态 | 结果 |", "|---|---|---|---|---|"]
    for r in RESULTS: lines.append(f"| {r['category']} | {r['case_id']} | {r['name']} | **{r['status']}** | {r['detail'].replace('|','/')} |")
    lines += ["", "## 判定规则", "", "- PASS：已由自动化样本验证。", "- FAIL：已实现能力发生错误，阻止发布。", "- BLOCKED：测试发现对应生产能力尚未实现，不得宣称为生产完成。", ""]
    (output/"PRINT_CATEGORY_P0_REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    return counts


def main():
    with tempfile.TemporaryDirectory(prefix="print-category-p0-") as temp:
        tmp=Path(temp)
        check("书刊画册类","BOOK-ORDER-001","骑马订、分帖、补白与爬移",check_booklet)
        check("商业单页类","COMM-NUP-001","N-up模数、数量与生产PDF",lambda:check_commercial(tmp))
        check("卡片类","CARD-DUPLEX-001","双面卡片正背输出",lambda:check_cards(tmp))
        check("不干胶标签类","LABEL-NEST-001","异形标签真实轮廓套料",check_labels)
        check("彩盒包装类","BOX-SPOT-001","CutContour刀线专色识别",lambda:check_packaging(tmp))
        check("特种产品","SPECIAL-SEQUENCE-001","票据/活页顺序与补白",check_special)
        check("数码印刷拼版","DIGITAL-MIX-001","异尺寸动态合版与生产PDF",lambda:check_digital(tmp))
    add_known_gaps(); counts=write_reports(Path("acceptance-output"))
    print(json.dumps(counts,ensure_ascii=False))
    if counts["FAIL"]: raise SystemExit(1)


if __name__=="__main__": main()
