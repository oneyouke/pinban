from pathlib import Path
import os,shutil
root=Path(os.environ.get("APP_ROOT","build-src/Desktop-Imposer-Pro-V2.2")).resolve();patch_root=Path(__file__).resolve().parent
for src,dst in (("special_templates_v2428.py","special_templates.py"),("test_v2428_special_templates.py","test_v2428_special_templates.py"),("test_v2428_special_templates_ui.py","test_v2428_special_templates_ui.py")):shutil.copy2(patch_root/src,root/dst)
ui=root/"professional_canvas.py";text=ui.read_text(encoding="utf-8")
marker="from label_roll import export_label_roll_pdf\n";addition="from special_templates import export_special_template_pdf, get_special_preset_defaults, special_preset_choices\n"
if addition not in text:
    if marker not in text:raise SystemExit("V2.4.27 label-roll import marker missing")
    text=text.replace(marker,marker+addition,1)
old='''        self.mix_status = QLabel("混拼队列：0 项"); self.mix_status.setObjectName("MixStatus"); self.mix_status.setWordWrap(True)
        layout.addWidget(self.mix_status)
'''
new='''        special = InspectorSection("特种产品工艺模板")
        self.special_preset = QComboBox()
        for preset_id, preset_name in special_preset_choices(): self.special_preset.addItem(preset_name, preset_id)
        self.special_source_path = QLineEdit(); self.special_source_path.setReadOnly(True); self.special_source_path.setPlaceholderText("可选画稿 PDF")
        special_source_btn = QPushButton("选择画稿"); special_source_btn.setObjectName("SmallButton"); special_source_btn.clicked.connect(self._select_special_source)
        self.special_width = self._dspin(220, 1, 3000); self.special_height = self._dspin(110, 1, 3000)
        self.special_parts = QSpinBox(); self.special_parts.setRange(2, 8); self.special_parts.setValue(3)
        self.special_summary = QLabel(); self.special_summary.setObjectName("Muted"); self.special_summary.setWordWrap(True)
        load_special = QPushButton("载入模板参数"); load_special.setObjectName("SmallButton"); load_special.clicked.connect(self._apply_special_preset)
        special_export = QPushButton("导出特种工艺模板 PDF"); special_export.setObjectName("PrimaryButton"); special_export.clicked.connect(self._export_special_template_pdf)
        special.form.addRow("模板", self.special_preset); special.form.addRow("画稿", self.special_source_path); special.form.addRow("", special_source_btn)
        special.form.addRow("成品宽度", self.special_width); special.form.addRow("成品高度", self.special_height); special.form.addRow("NCR 联数", self.special_parts)
        special.form.addRow("", load_special); special.form.addRow("", self.special_summary); special.form.addRow("", special_export)
        self.special_preset.currentIndexChanged.connect(self._apply_special_preset); layout.addWidget(special); self._apply_special_preset()

        self.mix_status = QLabel("混拼队列：0 项"); self.mix_status.setObjectName("MixStatus"); self.mix_status.setWordWrap(True)
        layout.addWidget(self.mix_status)
'''
if new not in text:
    if old not in text:raise SystemExit("V2.4.27 inspector tail marker missing")
    text=text.replace(old,new,1)
old='''    def _show_legacy_workspace(self):
'''
new='''    def _select_special_source(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择特种产品画稿", "", "PDF (*.pdf)")
        if path: self.special_source_path.setText(path)

    def _apply_special_preset(self, *_):
        defaults = get_special_preset_defaults(self.special_preset.currentData())
        self.special_width.setValue(defaults["width_mm"]); self.special_height.setValue(defaults["height_mm"])
        self.special_parts.setValue(max(2, defaults["parts"])); self.special_summary.setText(defaults["description"])

    def _export_special_template_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出特种工艺模板 PDF", f"{self.special_preset.currentText()}模板.pdf", "PDF (*.pdf)")
        if not path:return
        if not path.lower().endswith(".pdf"):path += ".pdf"
        try:
            result=export_special_template_pdf(self.special_preset.currentData(),path,source_pdf=self.special_source_path.text().strip() or None,width_mm=self.special_width.value(),height_mm=self.special_height.value(),parts=self.special_parts.value())
            QMessageBox.information(self,"导出完成",f"已生成 {result['name']} 工艺模板，共 {result['output_pages']} 页。\\n专色层：{', '.join(result['spot_names']) or '无'}\\n\\n{path}")
        except Exception as exc:QMessageBox.critical(self,"特种工艺模板导出失败",str(exc))

    def _show_legacy_workspace(self):
'''
if new not in text:
    if old not in text:raise SystemExit("V2.4.27 method insertion marker missing")
    text=text.replace(old,new,1)
ui.write_text(text,encoding="utf-8")
for filename in ("product.py","pyproject.toml","installer_nsis.nsi"):
    path=root/filename;path.write_text(path.read_text(encoding="utf-8").replace("2.4.27","2.4.28"),encoding="utf-8")
for filename in ("special_templates.py","professional_canvas.py","test_v2428_special_templates.py","test_v2428_special_templates_ui.py"):compile((root/filename).read_text(encoding="utf-8"),str(root/filename),"exec")
(root/"V2428_SPECIAL_TEMPLATES.md").write_text("# V2.4.28 Special Templates\n\nEnvelope, paper bag, NCR, foil, emboss and laser-cut production templates with verified spot layers.\n",encoding="utf-8")
print("V2.4.28 special template library integrated")
