from pathlib import Path
import os, shutil

root=Path(os.environ.get("APP_ROOT","build-src/Desktop-Imposer-Pro-V2.2")).resolve(); patch_root=Path(__file__).resolve().parent
for src,dst in (("booklet_export_v2423.py","booklet_export.py"),("test_v2423_booklet_export.py","test_v2423_booklet_export.py")):
    shutil.copy2(patch_root/src,root/dst)

ui=root/"production_modes.py"; text=ui.read_text(encoding="utf-8")
marker="from booklet import perfect_bound_sections, saddle_stitch\n"
addition="from booklet_export import export_booklet_pdf\n"
if addition not in text:
    if marker not in text: raise SystemExit("V2.4.22 booklet import marker missing")
    text=text.replace(marker,marker+addition,1)
old='        export = QPushButton("导出折手页序 JSON"); export.setObjectName("SecondaryMode"); export.clicked.connect(self.export_json); left.addWidget(export)\n'
new='        export_pdf = QPushButton("导出书籍生产 PDF"); export_pdf.setObjectName("PrimaryMode"); export_pdf.clicked.connect(self.export_production_pdf); left.addWidget(export_pdf)\n        export = QPushButton("导出折手页序 JSON"); export.setObjectName("SecondaryMode"); export.clicked.connect(self.export_json); left.addWidget(export)\n'
if new not in text:
    if old not in text: raise SystemExit("V2.4.22 booklet export button marker missing")
    text=text.replace(old,new,1)
old="    def export_json(self):\n"
new='''    def export_production_pdf(self):
        if not self.source_path:
            QMessageBox.information(self, "书籍生产 PDF", "请先导入书籍 PDF。")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出书籍生产 PDF", "书籍拼版输出.pdf", "PDF (*.pdf)")
        if not path: return
        if not path.lower().endswith(".pdf"): path += ".pdf"
        try:
            result = export_booklet_pdf(
                self.source_path, path, binding=self.binding.currentText(),
                signature_pages=int(self.signature_pages.currentText()),
                sheet_width_mm=self.sheet_w.value(), sheet_height_mm=self.sheet_h.value(),
                spine_mm=self.spine.value(), creep_per_sheet_mm=self.creep.value(),
                flip=self.flip.currentText(), draw_fold_lines=self.fold_lines.isChecked(),
            )
            QMessageBox.information(self, "导出完成", f"已生成 {result['output_pages']} 个正背大版 / {result['physical_sheets']} 张物理纸。\\n\\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "书籍生产 PDF 导出失败", str(exc))

    def export_json(self):
'''
if new not in text:
    if old not in text: raise SystemExit("V2.4.22 booklet export method marker missing")
    text=text.replace(old,new,1)
ui.write_text(text,encoding="utf-8")

for filename in ("product.py","pyproject.toml","installer_nsis.nsi"):
    path=root/filename; path.write_text(path.read_text(encoding="utf-8").replace("2.4.22","2.4.23"),encoding="utf-8")
for filename in ("booklet_export.py","production_modes.py","test_v2423_booklet_export.py"):
    compile((root/filename).read_text(encoding="utf-8"),str(root/filename),"exec")
(root/"V2423_BOOKLET_PRODUCTION_PDF.md").write_text("# V2.4.23 Booklet Production PDF\n\n- Produces vector booklet PDF sheets from saddle-stitch or bound signatures.\n- Applies blank-page padding, spine gap, creep compensation, fold marks and back-side flip.\n- Verifies output page count before publishing.\n",encoding="utf-8")
print("V2.4.23 booklet production PDF integrated")
