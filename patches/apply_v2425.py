from pathlib import Path
import os, shutil

root=Path(os.environ.get("APP_ROOT","build-src/Desktop-Imposer-Pro-V2.2")).resolve(); patch_root=Path(__file__).resolve().parent
for src,dst in (("cut_stack_v2425.py","cut_stack.py"),("test_v2425_cut_stack.py","test_v2425_cut_stack.py"),("test_v2425_cut_stack_ui.py","test_v2425_cut_stack_ui.py")):
    shutil.copy2(patch_root/src,root/dst)

ui=root/"professional_canvas.py"; text=ui.read_text(encoding="utf-8")
marker="from duplex import DuplexMode\n"
addition="from cut_stack import export_cut_stack_pdf\n"
if addition not in text:
    if marker not in text: raise SystemExit("V2.4.20 professional canvas import marker missing")
    text=text.replace(marker,addition+marker,1)
old='''        self.mix_status = QLabel("混拼队列：0 项"); self.mix_status.setObjectName("MixStatus"); self.mix_status.setWordWrap(True)
        layout.addWidget(self.mix_status)
'''
new='''        cut_stack = InspectorSection("切叠式 Cut & Stack")
        self.cut_rows = QSpinBox(); self.cut_rows.setRange(1, 32); self.cut_rows.setValue(2)
        self.cut_columns = QSpinBox(); self.cut_columns.setRange(1, 32); self.cut_columns.setValue(2)
        self.cut_duplex = QCheckBox("双面切叠")
        self.cut_order = QComboBox(); self.cut_order.addItem("逐行叠堆", "row_major"); self.cut_order.addItem("逐列叠堆", "column_major")
        cut_export = QPushButton("导出切叠式生产 PDF"); cut_export.setObjectName("PrimaryButton"); cut_export.clicked.connect(self._export_cut_stack_pdf)
        cut_stack.form.addRow("行数", self.cut_rows); cut_stack.form.addRow("列数", self.cut_columns)
        cut_stack.form.addRow("叠堆顺序", self.cut_order); cut_stack.form.addRow("", self.cut_duplex); cut_stack.form.addRow("", cut_export)
        layout.addWidget(cut_stack)

        self.mix_status = QLabel("混拼队列：0 项"); self.mix_status.setObjectName("MixStatus"); self.mix_status.setWordWrap(True)
        layout.addWidget(self.mix_status)
'''
if new not in text:
    if old not in text: raise SystemExit("V2.4.20 inspector marker missing")
    text=text.replace(old,new,1)
old='''    def _show_legacy_workspace(self):
'''
new='''    def _export_cut_stack_pdf(self):
        current = self.list.currentItem()
        if current is None:
            QMessageBox.information(self, "切叠式拼版", "请先导入并选择一个多页 PDF。"); return
        source = self.pages[int(current.data(Qt.UserRole))].path
        path, _ = QFileDialog.getSaveFileName(self, "导出切叠式生产 PDF", "切叠式拼版输出.pdf", "PDF (*.pdf)")
        if not path: return
        if not path.lower().endswith(".pdf"): path += ".pdf"
        try:
            result = export_cut_stack_pdf(
                source, path, sheet_width_mm=self.sheet_w.value(), sheet_height_mm=self.sheet_h.value(),
                trim_width_mm=self.trim_w.value(), trim_height_mm=self.trim_h.value(),
                rows=self.cut_rows.value(), columns=self.cut_columns.value(),
                gap_x_mm=self.gap_x.value(), gap_y_mm=self.gap_y.value(),
                duplex=self.cut_duplex.isChecked(), flip=self.duplex_mode.currentData(),
                stack_order=self.cut_order.currentData(), crop_marks=self.crop_marks.isChecked(),
            )
            QMessageBox.information(self, "导出完成", f"已生成 {result['sheet_count']} 张物理纸 / {result['output_pages']} 个印刷面。\\n每面 {result['capacity']} 个版位，补白 {result['blank_pages']} 页。\\n\\n{path}")
        except Exception as exc: QMessageBox.critical(self, "切叠式 PDF 导出失败", str(exc))

    def _show_legacy_workspace(self):
'''
if new not in text:
    if old not in text: raise SystemExit("V2.4.20 export method marker missing")
    text=text.replace(old,new,1)
ui.write_text(text,encoding="utf-8")

for filename in ("product.py","pyproject.toml","installer_nsis.nsi"):
    path=root/filename; path.write_text(path.read_text(encoding="utf-8").replace("2.4.24","2.4.25"),encoding="utf-8")
for filename in ("cut_stack.py","professional_canvas.py","test_v2425_cut_stack.py","test_v2425_cut_stack_ui.py"):
    compile((root/filename).read_text(encoding="utf-8"),str(root/filename),"exec")
(root/"V2425_CUT_STACK.md").write_text("# V2.4.25 Cut & Stack\n\n- Deterministic simplex and duplex cut-and-stack page ordering.\n- Row-major or column-major pile order, blank padding, duplex flip mapping and crop marks.\n- Vector source pages and verified reconstructed sequence.\n",encoding="utf-8")
print("V2.4.25 Cut & Stack integrated")
