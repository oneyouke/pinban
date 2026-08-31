from pathlib import Path
import os, shutil

root=Path(os.environ.get("APP_ROOT","build-src/Desktop-Imposer-Pro-V2.2")).resolve(); patch_root=Path(__file__).resolve().parent
for src,dst in (("label_roll_v2427.py","label_roll.py"),("test_v2427_label_roll.py","test_v2427_label_roll.py"),("test_v2427_label_roll_ui.py","test_v2427_label_roll_ui.py")):
    shutil.copy2(patch_root/src,root/dst)

ui=root/"professional_canvas.py"; text=ui.read_text(encoding="utf-8")
marker="from card_deck import export_card_deck_pdf\n"
addition="from label_roll import export_label_roll_pdf\n"
if addition not in text:
    if marker not in text: raise SystemExit("V2.4.26 card-deck import marker missing")
    text=text.replace(marker,marker+addition,1)
old='''        self.mix_status = QLabel("混拼队列：0 项"); self.mix_status.setObjectName("MixStatus"); self.mix_status.setWordWrap(True)
        layout.addWidget(self.mix_status)
'''
new='''        labels = InspectorSection("卷筒不干胶标签")
        self.label_source_path = QLineEdit(); self.label_source_path.setReadOnly(True); self.label_source_path.setPlaceholderText("标签画稿 PDF")
        label_source_btn = QPushButton("选择标签画稿"); label_source_btn.setObjectName("SmallButton"); label_source_btn.clicked.connect(self._select_label_source)
        self.label_web_width = self._dspin(330, 20, 3000); self.label_repeat_length = self._dspin(254, 20, 3000)
        self.label_lanes = QSpinBox(); self.label_lanes.setRange(1, 64); self.label_lanes.setValue(3)
        self.label_quantity = QSpinBox(); self.label_quantity.setRange(1, 10000000); self.label_quantity.setValue(1000)
        self.label_lane_gap = self._dspin(3, 0, 100); self.label_repeat_gap = self._dspin(3, 0, 100)
        self.label_direction = QComboBox(); self.label_direction.addItem("头出", "head_out"); self.label_direction.addItem("尾出", "tail_out"); self.label_direction.addItem("右出", "right_out"); self.label_direction.addItem("左出", "left_out")
        self.label_winding = QComboBox(); self.label_winding.addItem("外卷", "outside"); self.label_winding.addItem("内卷", "inside")
        self.label_slit_lines = QCheckBox("分条专色线 SlitLine"); self.label_slit_lines.setChecked(True)
        self.label_die_lines = QCheckBox("模切专色线 CutContour"); self.label_die_lines.setChecked(True)
        label_export = QPushButton("导出卷筒标签生产 PDF"); label_export.setObjectName("PrimaryButton"); label_export.clicked.connect(self._export_label_roll_pdf)
        labels.form.addRow("画稿", self.label_source_path); labels.form.addRow("", label_source_btn)
        labels.form.addRow("卷材宽度", self.label_web_width); labels.form.addRow("重复周长", self.label_repeat_length)
        labels.form.addRow("分条数", self.label_lanes); labels.form.addRow("标签数量", self.label_quantity)
        labels.form.addRow("横向间距", self.label_lane_gap); labels.form.addRow("纵向间距", self.label_repeat_gap)
        labels.form.addRow("出标方向", self.label_direction); labels.form.addRow("卷绕方式", self.label_winding)
        labels.form.addRow("", self.label_slit_lines); labels.form.addRow("", self.label_die_lines); labels.form.addRow("", label_export)
        layout.addWidget(labels)

        self.mix_status = QLabel("混拼队列：0 项"); self.mix_status.setObjectName("MixStatus"); self.mix_status.setWordWrap(True)
        layout.addWidget(self.mix_status)
'''
if new not in text:
    if old not in text: raise SystemExit("V2.4.26 inspector tail marker missing")
    text=text.replace(old,new,1)
old='''    def _show_legacy_workspace(self):
'''
new='''    def _select_label_source(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择标签画稿 PDF", "", "PDF (*.pdf)")
        if path: self.label_source_path.setText(path)

    def _export_label_roll_pdf(self):
        source = self.label_source_path.text().strip()
        if not source:
            QMessageBox.information(self, "卷筒标签", "请先选择标签画稿 PDF。"); return
        path, _ = QFileDialog.getSaveFileName(self, "导出卷筒标签生产 PDF", "卷筒标签拼版输出.pdf", "PDF (*.pdf)")
        if not path: return
        if not path.lower().endswith(".pdf"): path += ".pdf"
        try:
            result = export_label_roll_pdf(
                source, path, quantity=self.label_quantity.value(),
                web_width_mm=self.label_web_width.value(), repeat_length_mm=self.label_repeat_length.value(),
                label_width_mm=self.trim_w.value(), label_height_mm=self.trim_h.value(), lanes=self.label_lanes.value(),
                lane_gap_mm=self.label_lane_gap.value(), repeat_gap_mm=self.label_repeat_gap.value(),
                direction=self.label_direction.currentData(), winding=self.label_winding.currentData(),
                draw_slit_lines=self.label_slit_lines.isChecked(), draw_die_lines=self.label_die_lines.isChecked(),
            )
            QMessageBox.information(self, "导出完成", f"每重复 {result['capacity_per_cycle']} 枚，{result['lanes']} 条 × {result['repeats_per_cycle']} 纵向。\\n共 {result['cycle_count']} 个重复页，补空 {result['blank_positions']} 位，面积利用率 {result['utilization_percent']:.1f}%。\\n\\n{path}")
        except Exception as exc: QMessageBox.critical(self, "卷筒标签 PDF 导出失败", str(exc))

    def _show_legacy_workspace(self):
'''
if new not in text:
    if old not in text: raise SystemExit("V2.4.26 method insertion marker missing")
    text=text.replace(old,new,1)
ui.write_text(text,encoding="utf-8")

for filename in ("product.py","pyproject.toml","installer_nsis.nsi"):
    path=root/filename; path.write_text(path.read_text(encoding="utf-8").replace("2.4.26","2.4.27"),encoding="utf-8")
for filename in ("label_roll.py","professional_canvas.py","test_v2427_label_roll.py","test_v2427_label_roll_ui.py"):
    compile((root/filename).read_text(encoding="utf-8"),str(root/filename),"exec")
(root/"V2427_LABEL_ROLL.md").write_text("# V2.4.27 Label Roll\n\n- Web width, repeat circumference, lanes, direction and inside/outside winding model.\n- Vector repeat-cycle PDF with CutContour and SlitLine separations.\n- Quantity, blank-position, waste and utilization verification.\n",encoding="utf-8")
print("V2.4.27 label roll integrated")
