from pathlib import Path
import os, shutil

root=Path(os.environ.get("APP_ROOT","build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root=Path(__file__).resolve().parent
shutil.copy2(patch_root/"test_v2437_pdf_color_bars.py",root/"test_v2437_pdf_color_bars.py")

def replace_once(path,old,new,label):
    text=path.read_text(encoding="utf-8")
    if new in text:return
    if old not in text:raise SystemExit(f"V2.4.37 marker missing in {path.name}: {label}")
    path.write_text(text.replace(old,new,1),encoding="utf-8")

book=root/"booklet_export.py"
replace_once(book,
'''def _marks_overlay(width_pt, height_pt, fold_x_pt, spread, draw_fold_lines=True):
''',
'''def _draw_color_bar(c, width_pt, y_pt=14):
    colors=((1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1),(1,1,0,0),(1,0,1,0),(0,1,1,0),(1,1,1,1))
    patch_w, patch_h = 13, 8; start=(width_pt-len(colors)*patch_w)/2
    for index,color in enumerate(colors):
        c.setFillColorCMYK(*color); c.rect(start+index*patch_w,y_pt,patch_w,patch_h,stroke=0,fill=1)
    c.setStrokeColorCMYK(0,0,0,1); c.setLineWidth(.25); c.rect(start,y_pt,len(colors)*patch_w,patch_h,stroke=1,fill=0)


def _marks_overlay(width_pt, height_pt, fold_x_pt, spread, draw_fold_lines=True, draw_color_bar=True):
''',"book color bar helper")
replace_once(book,
'''    c.setFont("Helvetica", 6)
    label = f"SIG {spread.signature} / SHEET {spread.sheet} / {spread.side.upper()} / CREEP {spread.creep_mm:.3f} mm"
''',
'''    if draw_color_bar: _draw_color_bar(c,width_pt)
    c.setFillColorCMYK(0,0,0,1); c.setFont("Helvetica", 6)
    label = f"SIG {spread.signature} / SHEET {spread.sheet} / {spread.side.upper()} / CREEP {spread.creep_mm:.3f} mm"
''',"book color bar draw")
replace_once(book,
'''    draw_fold_lines=True,
    safe_inset_mm=3.0,
):
''',
'''    draw_fold_lines=True,
    safe_inset_mm=3.0,
    draw_color_bar=True,
):
''',"book export color bar option")
replace_once(book,
'''        overlay = _marks_overlay(width_pt, height_pt, width_pt/2, spread, draw_fold_lines)
''',
'''        overlay = _marks_overlay(width_pt, height_pt, width_pt/2, spread, draw_fold_lines, draw_color_bar)
''',"book export overlay")
replace_once(book,
'''        "spine_mm": spine_mm, "creep_per_sheet_mm": creep_per_sheet_mm,
''',
'''        "spine_mm": spine_mm, "creep_per_sheet_mm": creep_per_sheet_mm, "color_bar": bool(draw_color_bar),
''',"book export result")

box=root/"box_export.py"
replace_once(box,
'''def _sheet_overlay(width_pt, height_pt, points, placements, sheet_no, spot_name, bleed_mm):
''',
'''def _draw_color_bar(c, width_pt, y_pt=14):
    colors=((1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1),(1,1,0,0),(1,0,1,0),(0,1,1,0),(1,1,1,1))
    patch_w, patch_h=13,8; start=(width_pt-len(colors)*patch_w)/2
    for index,color in enumerate(colors):
        c.setFillColorCMYK(*color); c.rect(start+index*patch_w,y_pt,patch_w,patch_h,stroke=0,fill=1)
    c.setStrokeColorCMYK(0,0,0,1); c.setLineWidth(.25); c.rect(start,y_pt,len(colors)*patch_w,patch_h,stroke=1,fill=0)


def _sheet_overlay(width_pt, height_pt, points, placements, sheet_no, spot_name, bleed_mm, draw_color_bar=True):
''',"box color bar helper")
replace_once(box,
'''    c.setFillColorCMYK(0, 0, 0, 1)
    c.setFont("Helvetica", 6)
''',
'''    if draw_color_bar: _draw_color_bar(c,width_pt)
    c.setFillColorCMYK(0, 0, 0, 1)
    c.setFont("Helvetica", 6)
''',"box color bar draw")
replace_once(box,
'''    grain_direction="不限纸纹",
):
''',
'''    grain_direction="不限纸纹",
    draw_color_bar=True,
):
''',"box export color bar option")
replace_once(box,
'''        overlay = _sheet_overlay(width_pt, height_pt, points, plan.placements, sheet_no, spot_name, float(bleed_mm))
''',
'''        overlay = _sheet_overlay(width_pt, height_pt, points, plan.placements, sheet_no, spot_name, float(bleed_mm), draw_color_bar)
''',"box export overlay")
replace_once(box,
'''        "grain_direction": str(grain_direction),
        "vector_artwork": artwork is not None,
''',
'''        "grain_direction": str(grain_direction),
        "color_bar": bool(draw_color_bar),
        "vector_artwork": artwork is not None,
''',"box export result")

mode=root/"production_modes.py"
replace_once(mode,
'''        self.safe_inset = _spin(3, 0, 30, 1, " mm"); self.fold_lines = QCheckBox("显示折手线"); self.fold_lines.setChecked(True)
        for label, widget in (("总页数", self.total_pages), ("每帖页数", self.signature_pages), ("装订方式", self.binding), ("翻页方式", self.flip), ("纸张宽度", self.sheet_w), ("纸张高度", self.sheet_h), ("纸张厚度", self.paper_caliper), ("书脊宽度", self.spine), ("", self.auto_spine), ("爬移补偿", self.creep), ("页面安全边", self.safe_inset), ("", self.fold_lines)):
''',
'''        self.safe_inset = _spin(3, 0, 30, 1, " mm"); self.fold_lines = QCheckBox("显示折手线"); self.fold_lines.setChecked(True); self.color_bar=QCheckBox("输出 CMYK 色标"); self.color_bar.setChecked(True)
        for label, widget in (("总页数", self.total_pages), ("每帖页数", self.signature_pages), ("装订方式", self.binding), ("翻页方式", self.flip), ("纸张宽度", self.sheet_w), ("纸张高度", self.sheet_h), ("纸张厚度", self.paper_caliper), ("书脊宽度", self.spine), ("", self.auto_spine), ("爬移补偿", self.creep), ("页面安全边", self.safe_inset), ("", self.fold_lines), ("", self.color_bar)):
''',"book color bar control")
replace_once(mode,
'''                flip=self.flip.currentText(), draw_fold_lines=self.fold_lines.isChecked(), safe_inset_mm=self.safe_inset.value(),
''',
'''                flip=self.flip.currentText(), draw_fold_lines=self.fold_lines.isChecked(), safe_inset_mm=self.safe_inset.value(), draw_color_bar=self.color_bar.isChecked(),
''',"book UI export color bar")
replace_once(mode,
'''        self.spot=QLineEdit("CutContour"); self.spot.setPlaceholderText("刀线专色名称")
        for label,w in (("数量",self.quantity),("纸张宽度",self.sheet_w),("纸张高度",self.sheet_h),("纸边留白",self.margin),("纸纹方向",self.grain),("轮廓间距",self.gap),("出血",self.bleed),("搜索步长",self.step),("允许旋转",self.rotations),("刀线专色",self.spot)): form.addRow(label,w)
''',
'''        self.spot=QLineEdit("CutContour"); self.spot.setPlaceholderText("刀线专色名称"); self.color_bar=QCheckBox("输出 CMYK 色标"); self.color_bar.setChecked(True)
        for label,w in (("数量",self.quantity),("纸张宽度",self.sheet_w),("纸张高度",self.sheet_h),("纸边留白",self.margin),("纸纹方向",self.grain),("轮廓间距",self.gap),("出血",self.bleed),("搜索步长",self.step),("允许旋转",self.rotations),("刀线专色",self.spot),("",self.color_bar)): form.addRow(label,w)
''',"box color bar control")
replace_once(mode,
'''                bleed_mm=self.bleed.value(),spot_name=self.spot.text().strip() or "CutContour", margin_mm=self.margin.value(), grain_direction=self.grain.currentText(),
''',
'''                bleed_mm=self.bleed.value(),spot_name=self.spot.text().strip() or "CutContour", margin_mm=self.margin.value(), grain_direction=self.grain.currentText(), draw_color_bar=self.color_bar.isChecked(),
''',"box UI export color bar")

for filename in ("product.py","pyproject.toml","installer_nsis.nsi"):
    path=root/filename;path.write_text(path.read_text(encoding="utf-8").replace("2.4.36","2.4.37"),encoding="utf-8")
for filename in ("booklet_export.py","box_export.py","production_modes.py","test_v2437_pdf_color_bars.py"):
    compile((root/filename).read_text(encoding="utf-8"),str(root/filename),"exec")
(root/"V2437_PDF_COLOR_BARS.md").write_text("# V2.4.37 PDF Color Bars\n\nBook and box production PDF exports include optional CMYK and overprint color bars.\n",encoding="utf-8")
print("V2.4.37 PDF color bars integrated")
