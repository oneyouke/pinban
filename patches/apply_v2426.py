from pathlib import Path
import os, shutil

root=Path(os.environ.get("APP_ROOT","build-src/Desktop-Imposer-Pro-V2.2")).resolve(); patch_root=Path(__file__).resolve().parent
for src,dst in (("card_deck_v2426.py","card_deck.py"),("test_v2426_card_deck.py","test_v2426_card_deck.py"),("test_v2426_card_deck_ui.py","test_v2426_card_deck_ui.py")):
    shutil.copy2(patch_root/src,root/dst)

ui=root/"professional_canvas.py"; text=ui.read_text(encoding="utf-8")
marker="from cut_stack import export_cut_stack_pdf\n"
addition="from card_deck import export_card_deck_pdf\n"
if addition not in text:
    if marker not in text: raise SystemExit("V2.4.25 cut-stack import marker missing")
    text=text.replace(marker,marker+addition,1)
old='''        self.mix_status = QLabel("混拼队列：0 项"); self.mix_status.setObjectName("MixStatus"); self.mix_status.setWordWrap(True)
        layout.addWidget(self.mix_status)
'''
new='''        cards = InspectorSection("卡牌正背配对")
        self.card_front_path = QLineEdit(); self.card_front_path.setReadOnly(True); self.card_front_path.setPlaceholderText("正面牌组 PDF")
        self.card_back_path = QLineEdit(); self.card_back_path.setReadOnly(True); self.card_back_path.setPlaceholderText("通用或逐牌背面 PDF")
        self.card_manifest_path = QLineEdit(); self.card_manifest_path.setReadOnly(True); self.card_manifest_path.setPlaceholderText("可选 JSON / CSV 清单")
        front_btn = QPushButton("选择正面牌组"); front_btn.setObjectName("SmallButton"); front_btn.clicked.connect(self._select_card_front)
        back_btn = QPushButton("选择背面牌组"); back_btn.setObjectName("SmallButton"); back_btn.clicked.connect(self._select_card_back)
        manifest_btn = QPushButton("选择牌组清单"); manifest_btn.setObjectName("SmallButton"); manifest_btn.clicked.connect(self._select_card_manifest)
        self.card_rows = QSpinBox(); self.card_rows.setRange(1, 32); self.card_rows.setValue(1)
        self.card_columns = QSpinBox(); self.card_columns.setRange(1, 32); self.card_columns.setValue(3)
        self.card_common_back = QCheckBox("通用背面（背面 PDF 仅 1 页）"); self.card_common_back.setChecked(True)
        card_export = QPushButton("导出卡牌正背生产 PDF"); card_export.setObjectName("PrimaryButton"); card_export.clicked.connect(self._export_card_deck_pdf)
        cards.form.addRow("正面", self.card_front_path); cards.form.addRow("", front_btn)
        cards.form.addRow("背面", self.card_back_path); cards.form.addRow("", back_btn)
        cards.form.addRow("清单", self.card_manifest_path); cards.form.addRow("", manifest_btn)
        cards.form.addRow("行数", self.card_rows); cards.form.addRow("列数", self.card_columns); cards.form.addRow("", self.card_common_back); cards.form.addRow("", card_export)
        layout.addWidget(cards)

        self.mix_status = QLabel("混拼队列：0 项"); self.mix_status.setObjectName("MixStatus"); self.mix_status.setWordWrap(True)
        layout.addWidget(self.mix_status)
'''
if new not in text:
    if old not in text: raise SystemExit("V2.4.25 inspector tail marker missing")
    text=text.replace(old,new,1)
old='''    def _show_legacy_workspace(self):
'''
new='''    def _select_card_front(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择卡牌正面 PDF", "", "PDF (*.pdf)")
        if path: self.card_front_path.setText(path)

    def _select_card_back(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择卡牌背面 PDF", "", "PDF (*.pdf)")
        if path: self.card_back_path.setText(path)

    def _select_card_manifest(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择牌组清单", "", "牌组清单 (*.json *.csv)")
        if path: self.card_manifest_path.setText(path)

    def _export_card_deck_pdf(self):
        front, back = self.card_front_path.text().strip(), self.card_back_path.text().strip()
        if not front or not back:
            QMessageBox.information(self, "卡牌正背配对", "请先选择正面和背面 PDF。"); return
        path, _ = QFileDialog.getSaveFileName(self, "导出卡牌正背生产 PDF", "卡牌正背拼版输出.pdf", "PDF (*.pdf)")
        if not path: return
        if not path.lower().endswith(".pdf"): path += ".pdf"
        try:
            result = export_card_deck_pdf(
                front, back, path, sheet_width_mm=self.sheet_w.value(), sheet_height_mm=self.sheet_h.value(),
                trim_width_mm=self.trim_w.value(), trim_height_mm=self.trim_h.value(),
                rows=self.card_rows.value(), columns=self.card_columns.value(),
                gap_x_mm=self.gap_x.value(), gap_y_mm=self.gap_y.value(),
                common_back=self.card_common_back.isChecked(), flip=self.duplex_mode.currentData(),
                manifest_path=self.card_manifest_path.text().strip() or None, crop_marks=self.crop_marks.isChecked(),
            )
            QMessageBox.information(self, "导出完成", f"牌组校验通过：{result['card_count']} 张卡牌。\\n已生成 {result['sheet_count']} 张物理纸 / {result['output_pages']} 个正背印刷面，补空 {result['blank_cards']} 个牌位。\\n\\n{path}")
        except Exception as exc: QMessageBox.critical(self, "卡牌生产 PDF 导出失败", str(exc))

    def _show_legacy_workspace(self):
'''
if new not in text:
    if old not in text: raise SystemExit("V2.4.25 method insertion marker missing")
    text=text.replace(old,new,1)
ui.write_text(text,encoding="utf-8")

for filename in ("product.py","pyproject.toml","installer_nsis.nsi"):
    path=root/filename; path.write_text(path.read_text(encoding="utf-8").replace("2.4.25","2.4.26"),encoding="utf-8")
for filename in ("card_deck.py","professional_canvas.py","test_v2426_card_deck.py","test_v2426_card_deck_ui.py"):
    compile((root/filename).read_text(encoding="utf-8"),str(root/filename),"exec")
(root/"V2426_CARD_DECK.md").write_text("# V2.4.26 Card Deck Pairing\n\n- Manifest-based duplicate, missing, unexpected and blank card detection.\n- Common-back or page-paired backs with deterministic duplex placement.\n- Vector front/back production PDF with crop marks and pairing evidence.\n",encoding="utf-8")
print("V2.4.26 card deck pairing integrated")
