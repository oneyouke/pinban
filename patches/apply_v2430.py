from pathlib import Path
import os, shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent
shutil.copy2(patch_root / "test_v2430_bottom_dock.py", root / "test_v2430_bottom_dock.py")

def replace_once(text, old, new, label):
    if new in text: return text
    if old not in text: raise SystemExit(f"V2.4.30 marker missing: {label}")
    return text.replace(old, new, 1)

path = root / "professional_canvas.py"
text = path.read_text(encoding="utf-8")
style_marker = 'QSplitter::handle { background:#353b45; width:1px; }\n'
style_add = '''QSplitter::handle { background:#353b45; width:1px; }
QFrame#BottomDock { background:#171b20; border-top:1px solid #353b45; }
QFrame#BottomDockHeader { background:#20252c; border:0; }
QLabel#BottomDockTitle { color:#eef2f7; font-size:12px; font-weight:700; padding-left:8px; }
QToolButton#DockToggle { color:#aab5c4; background:transparent; border:0; min-width:34px; min-height:25px; }
QFrame#DockCard { background:#20252c; border-right:1px solid #353b45; }
QLabel#DockTitle { color:#67a9ff; font-size:11px; font-weight:700; }
QLabel#DockValue { color:#cbd3df; font-size:11px; }
QLabel#DockStrong { color:#55d17d; font-size:18px; font-weight:700; }
'''
text = replace_once(text, style_marker, style_add, "bottom dock style")

old = '''        root.addWidget(body, 1)

        self.canvas.scene().changed.connect(self._schedule_status_refresh)
'''
new = '''        root.addWidget(body, 1)
        root.addWidget(self._build_bottom_dock())

        self.canvas.scene().changed.connect(self._schedule_status_refresh)
        self.canvas.scene().selectionChanged.connect(self._refresh_bottom_dock)
'''
text = replace_once(text, old, new, "bottom dock mount")

marker = '''    def _canvas_tool(self, text, icon, handler):
'''
addition = '''    def _dock_card(self, title):
        card = QFrame(); card.setObjectName("DockCard")
        layout = QVBoxLayout(card); layout.setContentsMargins(12,7,12,7); layout.setSpacing(3)
        heading = QLabel(title); heading.setObjectName("DockTitle"); layout.addWidget(heading)
        return card, layout

    def _build_bottom_dock(self):
        self.bottom_dock = QFrame(); self.bottom_dock.setObjectName("BottomDock")
        dock = QVBoxLayout(self.bottom_dock); dock.setContentsMargins(0,0,0,0); dock.setSpacing(0)
        header = QFrame(); header.setObjectName("BottomDockHeader"); header_row = QHBoxLayout(header); header_row.setContentsMargins(8,2,6,2)
        title = QLabel("生产信息"); title.setObjectName("BottomDockTitle"); header_row.addWidget(title); header_row.addStretch()
        self.bottom_toggle = QToolButton(); self.bottom_toggle.setObjectName("DockToggle"); self.bottom_toggle.setText("收起  ▾"); self.bottom_toggle.clicked.connect(self._toggle_bottom_dock)
        header_row.addWidget(self.bottom_toggle); dock.addWidget(header)
        self.bottom_content = QFrame(); content = QHBoxLayout(self.bottom_content); content.setContentsMargins(0,0,0,0); content.setSpacing(0)

        card, box = self._dock_card("对象属性")
        self.selected_name = QLabel("未选择版位"); self.selected_name.setObjectName("DockValue")
        self.selected_geometry = QLabel("X —   Y —"); self.selected_geometry.setObjectName("DockValue")
        self.selected_size = QLabel("W —   H —"); self.selected_size.setObjectName("DockValue")
        box.addWidget(self.selected_name); box.addWidget(self.selected_geometry); box.addWidget(self.selected_size); content.addWidget(card, 2)

        card, box = self._dock_card("拼版统计")
        stats = QHBoxLayout(); self.bottom_pages = QLabel("0"); self.bottom_pages.setObjectName("DockStrong")
        self.bottom_placements = QLabel("0"); self.bottom_placements.setObjectName("DockStrong")
        stats.addWidget(self.bottom_pages); stats.addWidget(QLabel("页面")); stats.addSpacing(12); stats.addWidget(self.bottom_placements); stats.addWidget(QLabel("版位")); stats.addStretch(); box.addLayout(stats)
        self.bottom_utilization = QLabel("面积利用率 0.0% · 纸张 450 × 320 mm"); self.bottom_utilization.setObjectName("DockValue"); box.addWidget(self.bottom_utilization); content.addWidget(card, 2)

        card, box = self._dock_card("印前预检")
        self.bottom_preflight = QLabel("● 等待检查\\n错误 0 · 警告 0"); self.bottom_preflight.setObjectName("DockValue"); box.addWidget(self.bottom_preflight)
        run = QPushButton("执行检查"); run.setObjectName("SmallButton"); run.clicked.connect(self._run_host_preflight); box.addWidget(run); content.addWidget(card, 2)

        card, box = self._dock_card("图层与标记")
        layers = QHBoxLayout(); self.layer_crop = QCheckBox("裁切"); self.layer_registration = QCheckBox("套准"); self.layer_color = QCheckBox("色条")
        self.layer_crop.setChecked(self.crop_marks.isChecked()); self.layer_registration.setChecked(self.registration_marks.isChecked()); self.layer_color.setChecked(self.color_bar.isChecked())
        self.layer_crop.toggled.connect(self.crop_marks.setChecked); self.layer_registration.toggled.connect(self.registration_marks.setChecked); self.layer_color.toggled.connect(self.color_bar.setChecked)
        layers.addWidget(self.layer_crop); layers.addWidget(self.layer_registration); layers.addWidget(self.layer_color); layers.addStretch(); box.addLayout(layers)
        note = QLabel("页面内容 · 出血框 · 工艺专色"); note.setObjectName("DockValue"); box.addWidget(note); content.addWidget(card, 2)
        dock.addWidget(self.bottom_content); return self.bottom_dock

    def _toggle_bottom_dock(self):
        expanded = not self.bottom_content.isVisible(); self.bottom_content.setVisible(expanded)
        self.bottom_toggle.setText("收起  ▾" if expanded else "展开  ▴")

    def _refresh_bottom_dock(self):
        if not hasattr(self, "bottom_pages"): return
        items = [x for x in self.canvas.scene().items() if isinstance(x, PageItem) and getattr(x, "side", "front") == "front"]
        selected = self.canvas.selected_pages()
        self.bottom_pages.setText(str(len(self.pages))); self.bottom_placements.setText(str(len(items)))
        self.bottom_utilization.setText(f"面积利用率 {self.utilization.text()} · 纸张 {self.sheet_w.value():.0f} × {self.sheet_h.value():.0f} mm")
        if selected:
            item = selected[0]; self.selected_name.setText(f"{Path(item.info.path).name} · P{item.info.page_index + 1}")
            self.selected_geometry.setText(f"X {item.x():.2f} mm   Y {item.y():.2f} mm   R {item.rotation():.0f}°")
            self.selected_size.setText(f"W {item.info.width_mm:.2f} × {item.info.height_mm:.2f} mm")
        else:
            self.selected_name.setText("未选择版位"); self.selected_geometry.setText("X —   Y —   R —"); self.selected_size.setText("W —   H —")

'''
text = replace_once(text, marker, addition + marker, "bottom dock methods")

old = '''        self.status_pages.setText(f"页面 {len(self.pages)}"); self.status_placements.setText(f"版位 {len(items)}")
        scale = self.canvas.transform().m11()*100; self.zoom_label.setText(f"{scale:.0f}%")
'''
new = '''        self.status_pages.setText(f"页面 {len(self.pages)}"); self.status_placements.setText(f"版位 {len(items)}")
        self._refresh_bottom_dock()
        scale = self.canvas.transform().m11()*100; self.zoom_label.setText(f"{scale:.0f}%")
'''
text = replace_once(text, old, new, "bottom metrics refresh")

old = '''            self.preflight_summary.setText("检查任务已提交 · 请查看主状态栏")
            self.status_preflight.setText("预检 执行中"); host.run_preflight()
'''
new = '''            self.preflight_summary.setText("检查任务已提交 · 请查看主状态栏")
            self.status_preflight.setText("预检 执行中"); self.bottom_preflight.setText("● 正在检查\\n分析页面、字体、图像与标记")
            host.run_preflight()
'''
text = replace_once(text, old, new, "bottom preflight status")
path.write_text(text, encoding="utf-8")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    version_path = root / filename
    version_path.write_text(version_path.read_text(encoding="utf-8").replace("2.4.29", "2.4.30"), encoding="utf-8")
for filename in ("professional_canvas.py", "test_v2430_bottom_dock.py"):
    compile((root / filename).read_text(encoding="utf-8"), str(root / filename), "exec")
(root / "V2430_BOTTOM_PRODUCTION_DOCK.md").write_text("# V2.4.30 Bottom Production Dock\n\nLive object geometry, imposition metrics, preflight state and print-mark layers in a collapsible dock.\n", encoding="utf-8")
print("V2.4.30 bottom production dock integrated")
