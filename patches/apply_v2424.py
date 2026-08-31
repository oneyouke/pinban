from pathlib import Path
import os, shutil

root=Path(os.environ.get("APP_ROOT","build-src/Desktop-Imposer-Pro-V2.2")).resolve(); patch_root=Path(__file__).resolve().parent
for src,dst in (("box_export_v2424.py","box_export.py"),("test_v2424_box_export.py","test_v2424_box_export.py")):
    shutil.copy2(patch_root/src,root/dst)

ui=root/"production_modes.py"; text=ui.read_text(encoding="utf-8")
marker="from booklet_export import export_booklet_pdf\n"
addition="from box_export import export_box_pdf\n"
if addition not in text:
    if marker not in text: raise SystemExit("V2.4.23 export import marker missing")
    text=text.replace(marker,marker+addition,1)
old='        export=QPushButton("导出套料方案 JSON"); export.setObjectName("SecondaryMode"); export.clicked.connect(self.export_json); left.addWidget(export)\n'
new='        export_pdf=QPushButton("导出盒型生产 PDF"); export_pdf.setObjectName("PrimaryMode"); export_pdf.clicked.connect(self.export_production_pdf); left.addWidget(export_pdf)\n        export=QPushButton("导出套料方案 JSON"); export.setObjectName("SecondaryMode"); export.clicked.connect(self.export_json); left.addWidget(export)\n'
if new not in text:
    if old not in text: raise SystemExit("V2.4.22 box export button marker missing")
    text=text.replace(old,new,1)
old="    def export_json(self):\n        if not self.plan: QMessageBox.information(self,\"导出套料\",\"请先完成异形套料。\"); return\n"
new='''    def export_production_pdf(self):
        if not self.plan: QMessageBox.information(self,"盒型生产 PDF","请先完成异形套料。"); return
        path,_=QFileDialog.getSaveFileName(self,"导出盒型生产 PDF","盒型拼版输出.pdf","PDF (*.pdf)")
        if not path:return
        if not path.lower().endswith(".pdf"):path += ".pdf"
        try:
            result=export_box_pdf(
                self.source_path,self.points,self.plan,path,
                sheet_width_mm=self.sheet_w.value(),sheet_height_mm=self.sheet_h.value(),
                bleed_mm=self.bleed.value(),spot_name=self.spot.text().strip() or "CutContour",
            )
            QMessageBox.information(self,"导出完成",f"已生成 {result['sheet_count']} 张盒型生产大版，包含 {result['placement_count']} 个刀模。\\n刀线专色：{result['spot_name']}\\n\\n{path}")
        except Exception as exc: QMessageBox.critical(self,"盒型生产 PDF 导出失败",str(exc))

    def export_json(self):
        if not self.plan: QMessageBox.information(self,"导出套料","请先完成异形套料。"); return
'''
if new not in text:
    if old not in text: raise SystemExit("V2.4.22 box export method marker missing")
    text=text.replace(old,new,1)
ui.write_text(text,encoding="utf-8")

for filename in ("product.py","pyproject.toml","installer_nsis.nsi"):
    path=root/filename; path.write_text(path.read_text(encoding="utf-8").replace("2.4.23","2.4.24"),encoding="utf-8")
for filename in ("box_export.py","production_modes.py","test_v2424_box_export.py"):
    compile((root/filename).read_text(encoding="utf-8"),str(root/filename),"exec")
(root/"V2424_BOX_COMPOSITE_PDF.md").write_text("# V2.4.24 Box Composite Production PDF\n\n- Places source PDF artwork at every deterministic nesting position.\n- Adds bleed outlines and a true Separation spot-color die line.\n- Produces one verified vector PDF page per production sheet.\n",encoding="utf-8")
print("V2.4.24 box composite production PDF integrated")
