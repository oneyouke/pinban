from pathlib import Path
import os, shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent
shutil.copy2(patch_root / "test_v2436_book_box_upgrade.py", root / "test_v2436_book_box_upgrade.py")

def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text: return
    if old not in text: raise SystemExit(f"V2.4.36 marker missing in {path.name}: {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

mode = root / "production_modes.py"
replace_once(mode, "from nesting import NestItem, nest_polygons_multi_sheet\n", "from nesting import NestItem, NestPlacement, NestPlan, nest_polygons_multi_sheet\n", "nest plan imports")
replace_once(mode,
    '''        self.binding = QComboBox(); self.binding.addItems(["骑马订", "胶装 / 锁线分帖"])
''',
    '''        self.binding = QComboBox(); self.binding.addItems(["骑马订", "胶装 / 锁线分帖", "锁线精装"])
''', "binding options")
replace_once(mode,
    '''        self.spine = _spin(0, 0, 200, 2, " mm"); self.creep = _spin(.10, 0, 10, 3, " mm/张")
        self.fold_lines = QCheckBox("显示折手线"); self.fold_lines.setChecked(True)
        for label, widget in (("总页数", self.total_pages), ("每帖页数", self.signature_pages), ("装订方式", self.binding), ("翻页方式", self.flip), ("纸张宽度", self.sheet_w), ("纸张高度", self.sheet_h), ("书脊宽度", self.spine), ("爬移补偿", self.creep), ("", self.fold_lines)):
''',
    '''        self.spine = _spin(0, 0, 200, 2, " mm"); self.creep = _spin(.10, 0, 10, 3, " mm/张")
        self.paper_caliper = _spin(.10, .03, .50, 3, " mm/张"); self.auto_spine = QCheckBox("按页数与纸厚自动计算书脊"); self.auto_spine.setChecked(True)
        self.safe_inset = _spin(3, 0, 30, 1, " mm"); self.fold_lines = QCheckBox("显示折手线"); self.fold_lines.setChecked(True)
        for label, widget in (("总页数", self.total_pages), ("每帖页数", self.signature_pages), ("装订方式", self.binding), ("翻页方式", self.flip), ("纸张宽度", self.sheet_w), ("纸张高度", self.sheet_h), ("纸张厚度", self.paper_caliper), ("书脊宽度", self.spine), ("", self.auto_spine), ("爬移补偿", self.creep), ("页面安全边", self.safe_inset), ("", self.fold_lines)):
''', "book production controls")
replace_once(mode,
    '''        self.table = QTableWidget(0, 7); self.table.setHorizontalHeaderLabels(["帖", "张", "面", "左页", "右页", "爬移 mm", "翻页"])
''',
    '''        self.table = QTableWidget(0, 8); self.table.setHorizontalHeaderLabels(["帖", "张", "面", "左页", "右页", "爬移 mm", "书脊 mm", "翻页"])
''', "book table detail")
replace_once(mode,
    '''    def calculate(self):
        pages = self.total_pages.value(); creep = self.creep.value()
''',
    '''    def calculate(self):
        pages = self.total_pages.value(); creep = self.creep.value()
        if self.auto_spine.isChecked():
            calculated = 0.0 if self.binding.currentText() == "骑马订" else pages * self.paper_caliper.value() / 2.0
            self.spine.setValue(calculated)
''', "automatic spine")
replace_once(mode,
    '''            values = [spread.signature, spread.sheet, "正面" if spread.side == "front" else "背面", spread.left or "空白", spread.right or "空白", f"{spread.creep_mm:.3f}", self.flip.currentText()]
''',
    '''            values = [spread.signature, spread.sheet, "正面" if spread.side == "front" else "背面", spread.left or "空白", spread.right or "空白", f"{spread.creep_mm:.3f}", f"{self.spine.value():.2f}", self.flip.currentText()]
''', "book table spine")
replace_once(mode,
    '''        self.summary.setText(f"共 {len(sections)} 帖 · {len(keys)} 张物理纸 · {len(self.plan)} 个正背版 · 补白 {padded} 页")
''',
    '''        signature_detail = " / ".join(f"第{i+1}帖 {len(section)//2}张" for i, section in enumerate(sections))
        self.summary.setText(f"共 {len(sections)} 帖 · {len(keys)} 张物理纸 · {len(self.plan)} 个正背版 · 补白 {padded} 页\\n书脊 {self.spine.value():.2f} mm · 安全边 {self.safe_inset.value():.1f} mm · {signature_detail}")
''', "book production summary")
replace_once(mode,
    '''                flip=self.flip.currentText(), draw_fold_lines=self.fold_lines.isChecked(),
''',
    '''                flip=self.flip.currentText(), draw_fold_lines=self.fold_lines.isChecked(), safe_inset_mm=self.safe_inset.value(),
''', "book safe inset export")
replace_once(mode,
    '''        payload = {"source": self.source_path, "total_pages": self.total_pages.value(), "signature_pages": int(self.signature_pages.currentText()), "binding": self.binding.currentText(), "flip": self.flip.currentText(), "spine_mm": self.spine.value(), "creep_per_sheet_mm": self.creep.value(), "spreads": [x.to_dict() for x in self.plan]}
''',
    '''        payload = {"source": self.source_path, "total_pages": self.total_pages.value(), "signature_pages": int(self.signature_pages.currentText()), "binding": self.binding.currentText(), "flip": self.flip.currentText(), "paper_caliper_mm": self.paper_caliper.value(), "auto_spine": self.auto_spine.isChecked(), "spine_mm": self.spine.value(), "creep_per_sheet_mm": self.creep.value(), "safe_inset_mm": self.safe_inset.value(), "spreads": [x.to_dict() for x in self.plan]}
''', "book json production data")

replace_once(mode,
    '''        self.sheet_w=_spin(650,20,3000,1," mm"); self.sheet_h=_spin(450,20,3000,1," mm"); self.gap=_spin(3,0,100,1," mm"); self.bleed=_spin(3,0,50,1," mm"); self.step=_spin(2,.5,20,1," mm")
        self.rotations=QComboBox(); self.rotations.addItems(["0° / 90° / 180° / 270°", "仅 0° / 180°", "仅 0°"])
''',
    '''        self.sheet_w=_spin(650,20,3000,1," mm"); self.sheet_h=_spin(450,20,3000,1," mm"); self.margin=_spin(10,0,100,1," mm"); self.gap=_spin(3,0,100,1," mm"); self.bleed=_spin(3,0,50,1," mm"); self.step=_spin(2,.5,20,1," mm")
        self.grain=QComboBox(); self.grain.addItems(["不限纸纹", "顺纹（仅 0° / 180°）", "横纹（仅 90° / 270°）"])
        self.rotations=QComboBox(); self.rotations.addItems(["0° / 90° / 180° / 270°", "仅 0° / 180°", "仅 0°"])
''', "box margin grain controls")
replace_once(mode,
    '''        for label,w in (("数量",self.quantity),("纸张宽度",self.sheet_w),("纸张高度",self.sheet_h),("轮廓间距",self.gap),("出血",self.bleed),("搜索步长",self.step),("允许旋转",self.rotations),("刀线专色",self.spot)): form.addRow(label,w)
''',
    '''        for label,w in (("数量",self.quantity),("纸张宽度",self.sheet_w),("纸张高度",self.sheet_h),("纸边留白",self.margin),("纸纹方向",self.grain),("轮廓间距",self.gap),("出血",self.bleed),("搜索步长",self.step),("允许旋转",self.rotations),("刀线专色",self.spot)): form.addRow(label,w)
''', "box form controls")
replace_once(mode,
    '''        choices=((0,90,180,270),(0,180),(0,)); rotations=choices[self.rotations.currentIndex()]
        try:
            item=NestItem(Path(self.source_path).stem or "box",self.points,self.quantity.value(),rotations)
            self.plan=nest_polygons_multi_sheet([item],self.sheet_w.value(),self.sheet_h.value(),self.gap.value()+self.bleed.value()*2,self.step.value())
''',
    '''        choices=((0,90,180,270),(0,180),(0,)); rotations=choices[self.rotations.currentIndex()]
        if self.grain.currentIndex() == 1: rotations=tuple(x for x in rotations if x in (0,180)) or (0,180)
        elif self.grain.currentIndex() == 2: rotations=tuple(x for x in rotations if x in (90,270)) or (90,270)
        margin=self.margin.value(); usable_w=self.sheet_w.value()-margin*2; usable_h=self.sheet_h.value()-margin*2
        if usable_w <= 0 or usable_h <= 0: QMessageBox.warning(self,"套料失败","纸边留白超过纸张有效尺寸。"); return
        try:
            item=NestItem(Path(self.source_path).stem or "box",self.points,self.quantity.value(),rotations)
            raw=nest_polygons_multi_sheet([item],usable_w,usable_h,self.gap.value()+self.bleed.value()*2,self.step.value())
            shifted=[NestPlacement(p.item_id,p.copy_index,p.x_mm+margin,p.y_mm+margin,p.rotation,p.sheet) for p in raw.placements]
            self.plan=NestPlan(shifted,raw.sheet_count,raw.utilization)
''', "box usable nesting area")
replace_once(mode,
    '''        average=sum(self.plan.utilization)/max(1,len(self.plan.utilization))*100
        self.summary.setText(f"{len(self.plan.placements)} 个盒型 · {self.plan.sheet_count} 张大版 · 平均轮廓利用率 {average:.1f}% · 刀线专色 {self.spot.text().strip() or 'CutContour'}")
''',
    '''        average=sum(self.plan.utilization)/max(1,len(self.plan.utilization))*100; waste=max(0.0,100-average)
        usable_w=self.sheet_w.value()-self.margin.value()*2; usable_h=self.sheet_h.value()-self.margin.value()*2
        self.summary.setText(f"{len(self.plan.placements)} 个盒型 · {self.plan.sheet_count} 张大版 · 利用率 {average:.1f}% · 废料率 {waste:.1f}%\\n有效版心 {usable_w:.1f} × {usable_h:.1f} mm · {self.grain.currentText()} · 刀线专色 {self.spot.text().strip() or 'CutContour'}")
''', "box utilization summary")
replace_once(mode,
    '''                bleed_mm=self.bleed.value(),spot_name=self.spot.text().strip() or "CutContour",
''',
    '''                bleed_mm=self.bleed.value(),spot_name=self.spot.text().strip() or "CutContour", margin_mm=self.margin.value(), grain_direction=self.grain.currentText(),
''', "box export production options")
replace_once(mode,
    '''        payload={"source":self.source_path,"spot_color":self.spot.text().strip() or "CutContour","bleed_mm":self.bleed.value(),"sheet":{"width_mm":self.sheet_w.value(),"height_mm":self.sheet_h.value()},"contour":self.points,"sheet_count":self.plan.sheet_count,"utilization":self.plan.utilization,"placements":[vars(x) for x in self.plan.placements]}
''',
    '''        payload={"source":self.source_path,"spot_color":self.spot.text().strip() or "CutContour","bleed_mm":self.bleed.value(),"margin_mm":self.margin.value(),"grain_direction":self.grain.currentText(),"sheet":{"width_mm":self.sheet_w.value(),"height_mm":self.sheet_h.value()},"contour":self.points,"sheet_count":self.plan.sheet_count,"utilization":self.plan.utilization,"placements":[vars(x) for x in self.plan.placements]}
''', "box json production data")

box_export = root / "box_export.py"
replace_once(box_export,
    '''    spot_name="CutContour",
):
''',
    '''    spot_name="CutContour",
    margin_mm=0.0,
    grain_direction="不限纸纹",
):
''', "box export options")
replace_once(box_export,
    '''    if bleed_mm < 0:
        raise ValueError("出血不能小于 0")
''',
    '''    if bleed_mm < 0 or margin_mm < 0:
        raise ValueError("出血和纸边留白不能小于 0")
    if margin_mm * 2 >= min(sheet_width_mm, sheet_height_mm):
        raise ValueError("纸边留白超过纸张有效尺寸")
''', "box export validation")
replace_once(box_export,
    '''        "/Subject": f"Die nesting; spot {spot_name}; bleed {bleed_mm:.2f} mm",
''',
    '''        "/Subject": f"Die nesting; spot {spot_name}; bleed {bleed_mm:.2f} mm; margin {margin_mm:.2f} mm; grain {grain_direction}",
''', "box metadata")
replace_once(box_export,
    '''        "spot_name": spot_name,
        "vector_artwork": artwork is not None,
''',
    '''        "spot_name": spot_name,
        "margin_mm": float(margin_mm),
        "grain_direction": str(grain_direction),
        "vector_artwork": artwork is not None,
''', "box export result")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    path=root/filename; path.write_text(path.read_text(encoding="utf-8").replace("2.4.35","2.4.36"),encoding="utf-8")
for filename in ("production_modes.py","box_export.py","test_v2436_book_box_upgrade.py"):
    compile((root/filename).read_text(encoding="utf-8"),str(root/filename),"exec")
(root/"V2436_BOOK_BOX_UPGRADE.md").write_text("# V2.4.36 Book and Box Upgrade\n\nProduction-grade book spine/signature controls and box margin/grain-aware nesting.\n",encoding="utf-8")
print("V2.4.36 book and box upgrade integrated")
