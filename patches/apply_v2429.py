from pathlib import Path
import os, shutil

root = Path(os.environ.get("APP_ROOT", "build-src/Desktop-Imposer-Pro-V2.2")).resolve()
patch_root = Path(__file__).resolve().parent
for name in ("test_v2429_professional_ui.py", "test_v2429_mode_ui.py"):
    shutil.copy2(patch_root / name, root / name)

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"V2.4.29 marker missing: {label}")
    return text.replace(old, new, 1)

ui_path = root / "professional_canvas.py"
text = ui_path.read_text(encoding="utf-8")

style_start = text.index('WORKSPACE_STYLE = r"""')
style_end = text.index('"""\n\n\nclass ProfessionalCanvas', style_start) + 3
dark_style = r'''WORKSPACE_STYLE = r"""
QWidget#ImpositionWorkspace { background:#181c22; color:#d8dee9; }
QFrame#TopCommandBar { background:#20252c; border-bottom:1px solid #353b45; }
QLabel#WorkspaceTitle { color:#f0f3f8; font-size:14px; font-weight:700; padding:0 12px; }
QToolButton#CommandButton { background:transparent; border:0; border-right:1px solid #343a43; border-radius:0; padding:5px 9px; min-width:54px; min-height:50px; color:#cbd3df; font-size:11px; font-weight:600; }
QToolButton#CommandButton:hover { background:#2b3440; color:#59a2ff; }
QToolButton#CommandButton:pressed { background:#162f52; }
QFrame#Sidebar, QFrame#Inspector { background:#20252c; border:0; }
QLabel#PaneTitle { font-size:13px; font-weight:700; color:#eef2f7; padding:6px 3px; }
QLabel#SectionTitle { font-size:13px; font-weight:700; color:#dbe2ec; }
QLabel#Muted { color:#8995a6; font-size:11px; }
QFrame#PaneTabs, QFrame#InspectorTabs { background:#181c22; border-bottom:1px solid #353b45; }
QPushButton#PaneTab, QPushButton#InspectorTab { color:#9da9b9; background:transparent; border:0; border-bottom:2px solid transparent; min-height:32px; padding:0 13px; font-weight:700; }
QPushButton#PaneTab:checked, QPushButton#InspectorTab:checked { color:#67a9ff; border-bottom-color:#2784f5; background:#202a37; }
QLineEdit#PageSearch { background:#171b21; color:#dbe2ec; border:1px solid #3a414c; border-radius:5px; min-height:29px; padding:0 9px; }
QListWidget#PageList { background:#1c2026; color:#d5dce6; border:0; outline:0; padding:3px; }
QListWidget#PageList::item { border:1px solid #353b45; border-radius:5px; padding:7px; margin:3px 1px; color:#cbd3df; }
QListWidget#PageList::item:selected { background:#17365c; border:1px solid #2784f5; color:white; }
QFrame#CanvasChrome { background:#181c22; border-left:1px solid #353b45; border-right:1px solid #353b45; }
QFrame#CanvasHeader { background:#20252c; border-bottom:1px solid #353b45; }
QPushButton#SideTab { border:0; border-bottom:2px solid transparent; background:transparent; min-width:62px; min-height:30px; padding:0 12px; color:#929eae; font-weight:700; }
QPushButton#SideTab:checked { background:#202a37; color:#67a9ff; border-bottom-color:#2784f5; }
QFrame#CanvasTools { background:#20252c; border-left:1px solid #353b45; }
QToolButton#CanvasTool { background:transparent; border:0; color:#b7c1cf; min-width:42px; min-height:45px; font-size:10px; }
QToolButton#CanvasTool:hover { background:#2c3541; color:#67a9ff; }
QFrame#CanvasStatus { background:#20252c; border-top:1px solid #353b45; }
QLabel#MetricLabel { color:#aeb8c6; background:#181c22; border:1px solid #343b45; border-radius:4px; padding:4px 9px; }
QLabel#Utilization { color:#55d17d; font-size:15px; font-weight:700; }
QLabel#ReadyStatus { color:#55d17d; font-weight:700; }
QFrame#InspectorSection { background:#20252c; border-bottom:1px solid #343a43; }
QLabel#InspectorTitle { font-size:12px; font-weight:700; color:#eef2f7; }
QDoubleSpinBox, QSpinBox, QComboBox, QLineEdit { background:#171b21; color:#dbe2ec; border:1px solid #3b434f; border-radius:4px; min-height:27px; padding:0 6px; selection-background-color:#1769df; }
QComboBox QAbstractItemView { background:#20252c; color:#dbe2ec; selection-background-color:#1769df; }
QCheckBox { spacing:7px; color:#c7d0dc; min-height:22px; }
QPushButton#SmallButton { background:#272d35; color:#d4dce7; border:1px solid #414956; border-radius:4px; min-height:28px; padding:0 10px; }
QPushButton#SmallButton:hover { border-color:#2784f5; color:#67a9ff; }
QPushButton#PrimaryButton { background:#1473e6; color:white; border:0; border-radius:5px; min-height:38px; font-size:13px; font-weight:700; }
QPushButton#PrimaryButton:hover { background:#2784f5; }
QLabel#MixStatus { background:#181c22; border:1px solid #353d48; border-radius:4px; color:#98a5b6; padding:7px; }
QScrollArea { border:0; background:#20252c; }
QScrollBar:vertical { background:#181c22; width:10px; } QScrollBar::handle:vertical { background:#454d59; border-radius:4px; min-height:28px; }
QSplitter::handle { background:#353b45; width:1px; }
"""'''
text = text[:style_start] + dark_style + text[style_end:]

text = text.replace('self.setBackgroundBrush(QColor("#eef1f5"))', 'self.setBackgroundBrush(QColor("#181c22"))', 1)
text = text.replace('self.setStyleSheet("background:#f7f9fc;border:0;color:#667085;")', 'self.setStyleSheet("background:#242a32;border:0;color:#9aa6b6;")', 1)
text = text.replace('p.fillRect(self.rect(), QColor("#f7f9fc"))', 'p.fillRect(self.rect(), QColor("#242a32"))', 1)
text = text.replace('QColor("#aeb7c5")', 'QColor("#6e7989")', 1)

old = '''    def _build_command_bar(self):
        bar = QFrame(); bar.setObjectName("TopCommandBar")
        layout = QHBoxLayout(bar); layout.setContentsMargins(8, 0, 8, 0); layout.setSpacing(0)
        commands = [
            ("导入 PDF", QStyle.SP_DialogOpenButton, self.import_pdf),
            ("自动拼版", QStyle.SP_BrowserReload, self._auto_impose),
            ("生成反面", QStyle.SP_ArrowRight, self._generate_backside),
            ("撤销", QStyle.SP_ArrowBack, self.canvas.undo_stack.undo),
            ("重做", QStyle.SP_ArrowForward, self.canvas.undo_stack.redo),
            ("旋转 90°", QStyle.SP_BrowserReload, self.canvas.rotate_selected),
            ("删除版位", QStyle.SP_DialogDiscardButton, self.canvas.delete_selected),
            ("印前检查", QStyle.SP_DialogApplyButton, self._run_host_preflight),
            ("导出生产 PDF", QStyle.SP_DialogSaveButton, self._export_host_pdf),
            ("经典参数", QStyle.SP_FileDialogDetailedView, self._show_legacy_workspace),
        ]
        for text, icon, fn in commands: layout.addWidget(self._command(text, icon, fn))
        layout.addStretch(1)
        self.top_ready = QLabel("● 生产画布就绪"); self.top_ready.setObjectName("ReadyStatus")
        layout.addWidget(self.top_ready); layout.addSpacing(14)
        return bar
'''
new = '''    def _build_command_bar(self):
        bar = QFrame(); bar.setObjectName("TopCommandBar")
        layout = QHBoxLayout(bar); layout.setContentsMargins(0, 0, 8, 0); layout.setSpacing(0)
        title = QLabel("拼版工作台"); title.setObjectName("WorkspaceTitle"); layout.addWidget(title)
        commands = [
            ("导入", QStyle.SP_DialogOpenButton, self.import_pdf), ("自动拼版", QStyle.SP_BrowserReload, self._auto_impose),
            ("生成反面", QStyle.SP_ArrowRight, self._generate_backside), ("撤销", QStyle.SP_ArrowBack, self.canvas.undo_stack.undo),
            ("重做", QStyle.SP_ArrowForward, self.canvas.undo_stack.redo), ("旋转", QStyle.SP_BrowserReload, self.canvas.rotate_selected),
            ("删除", QStyle.SP_DialogDiscardButton, self.canvas.delete_selected), ("预检", QStyle.SP_DialogApplyButton, self._run_host_preflight),
            ("导出 PDF", QStyle.SP_DialogSaveButton, self._export_host_pdf), ("切叠式", QStyle.SP_FileDialogListView, self._export_cut_stack_pdf),
            ("经典参数", QStyle.SP_FileDialogDetailedView, self._show_legacy_workspace),
        ]
        for command_text, icon, fn in commands: layout.addWidget(self._command(command_text, icon, fn))
        layout.addStretch(1)
        self.top_ready = QLabel("● 生产画布就绪"); self.top_ready.setObjectName("ReadyStatus")
        layout.addWidget(self.top_ready); layout.addSpacing(10)
        return bar
'''
text = replace_once(text, old, new, "compact command bar")

old = '''        title_row = QHBoxLayout(); title = QLabel("作业文件"); title.setObjectName("PaneTitle")
        add = QToolButton(); add.setText("＋"); add.clicked.connect(self.import_pdf)
        title_row.addWidget(title); title_row.addStretch(); title_row.addWidget(add); layout.addLayout(title_row)
'''
new = '''        title_row = QHBoxLayout(); title = QLabel("页面管理"); title.setObjectName("PaneTitle")
        add = QToolButton(); add.setText("＋ 导入"); add.clicked.connect(self.import_pdf)
        title_row.addWidget(title); title_row.addStretch(); title_row.addWidget(add); layout.addLayout(title_row)
        pane_tabs = QFrame(); pane_tabs.setObjectName("PaneTabs"); pane_row = QHBoxLayout(pane_tabs); pane_row.setContentsMargins(0,0,0,0); pane_row.setSpacing(0)
        for index, label in enumerate(("页面缩略图", "作业文件")):
            button = QPushButton(label); button.setObjectName("PaneTab"); button.setCheckable(True); button.setChecked(index == 0); pane_row.addWidget(button)
        layout.addWidget(pane_tabs)
'''
text = replace_once(text, old, new, "left pane tabs")

text = text.replace('tabs = QFrame(); tabs.setStyleSheet("background:#ffffff;border-bottom:1px solid #d8dee8;")', 'tabs = QFrame(); tabs.setObjectName("CanvasHeader")', 1)
old = '''        canvas_row = QHBoxLayout(); canvas_row.setContentsMargins(0, 0, 0, 0); canvas_row.setSpacing(0)
        self.v_ruler = RulerWidget(self.canvas, Qt.Vertical); canvas_row.addWidget(self.v_ruler); canvas_row.addWidget(self.canvas, 1)
        layout.addLayout(canvas_row, 1)
'''
new = '''        canvas_row = QHBoxLayout(); canvas_row.setContentsMargins(0, 0, 0, 0); canvas_row.setSpacing(0)
        self.v_ruler = RulerWidget(self.canvas, Qt.Vertical); canvas_row.addWidget(self.v_ruler); canvas_row.addWidget(self.canvas, 1)
        self.canvas_tools = QFrame(); self.canvas_tools.setObjectName("CanvasTools"); tools = QVBoxLayout(self.canvas_tools); tools.setContentsMargins(0,5,0,5); tools.setSpacing(0)
        tools.addWidget(self._canvas_tool("选择", QStyle.SP_ArrowUp, lambda: None))
        tools.addWidget(self._canvas_tool("旋转", QStyle.SP_BrowserReload, self.canvas.rotate_selected))
        tools.addWidget(self._canvas_tool("适屏", QStyle.SP_DesktopIcon, lambda: self.canvas.fitInView(self.canvas.sceneRect(), Qt.KeepAspectRatio)))
        tools.addWidget(self._canvas_tool("删除", QStyle.SP_DialogDiscardButton, self.canvas.delete_selected)); tools.addStretch(1)
        canvas_row.addWidget(self.canvas_tools); layout.addLayout(canvas_row, 1)
'''
text = replace_once(text, old, new, "canvas tool rail")

old = '''        row.addWidget(self.zoom_out); row.addWidget(self.zoom_label); row.addWidget(self.zoom_in)
        row.addSpacing(18); row.addWidget(QLabel("利用率")); self.utilization = QLabel("0.0%"); self.utilization.setObjectName("Utilization"); row.addWidget(self.utilization)
        row.addStretch(); self.canvas_status = QLabel("等待导入页面"); self.canvas_status.setObjectName("ReadyStatus"); row.addWidget(self.canvas_status)
'''
new = '''        row.addWidget(self.zoom_out); row.addWidget(self.zoom_label); row.addWidget(self.zoom_in); row.addSpacing(12)
        self.status_pages = QLabel("页面 0"); self.status_pages.setObjectName("MetricLabel")
        self.status_placements = QLabel("版位 0"); self.status_placements.setObjectName("MetricLabel")
        self.status_preflight = QLabel("预检 待执行"); self.status_preflight.setObjectName("MetricLabel")
        row.addWidget(self.status_pages); row.addWidget(self.status_placements); row.addWidget(self.status_preflight)
        row.addSpacing(12); row.addWidget(QLabel("利用率")); self.utilization = QLabel("0.0%"); self.utilization.setObjectName("Utilization"); row.addWidget(self.utilization)
        row.addStretch(); self.canvas_status = QLabel("等待导入页面"); self.canvas_status.setObjectName("ReadyStatus"); row.addWidget(self.canvas_status)
'''
text = replace_once(text, old, new, "production status strip")

marker = '''    def _dspin(self, value, minimum, maximum, suffix=" mm", decimals=1):
'''
addition = '''    def _canvas_tool(self, text, icon, handler):
        button = QToolButton(); button.setObjectName("CanvasTool"); button.setText(text)
        button.setIcon(self.style().standardIcon(icon)); button.setIconSize(QSize(18,18)); button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.clicked.connect(handler); return button

    def _set_inspector_group(self, group):
        self.inspector_group = group
        for key, sections in self._inspector_sections.items():
            for section in sections: section.setVisible(key == group)
        names = ("basic", "production", "output")
        for button, key in zip(self.inspector_tabs, names): button.setChecked(key == group)

'''
text = replace_once(text, marker, addition + marker, "canvas tool helpers")

old = '''        panel = QFrame(); panel.setObjectName("Inspector")
        layout = QVBoxLayout(panel); layout.setContentsMargins(0, 0, 0, 10); layout.setSpacing(0)

        sheet = InspectorSection("纸张设置")
'''
new = '''        panel = QFrame(); panel.setObjectName("Inspector")
        layout = QVBoxLayout(panel); layout.setContentsMargins(0, 0, 0, 10); layout.setSpacing(0)
        self._inspector_sections = {"basic": [], "production": [], "output": []}; self.inspector_tabs = []
        tabs = QFrame(); tabs.setObjectName("InspectorTabs"); tabs_row = QHBoxLayout(tabs); tabs_row.setContentsMargins(0,0,0,0); tabs_row.setSpacing(0)
        for label, key in (("基本","basic"),("工艺","production"),("输出","output")):
            button = QPushButton(label); button.setObjectName("InspectorTab"); button.setCheckable(True); button.clicked.connect(lambda checked=False, group=key: self._set_inspector_group(group))
            tabs_row.addWidget(button); self.inspector_tabs.append(button)
        layout.addWidget(tabs)

        sheet = InspectorSection("纸张设置"); self.sheet_section = sheet
'''
text = replace_once(text, old, new, "inspector group tabs")

replacements = {
    'layout.addWidget(sheet)': 'layout.addWidget(sheet); self._inspector_sections["basic"].append(sheet)',
    'layout.addWidget(product)': 'layout.addWidget(product); self._inspector_sections["basic"].append(product)',
    'layout.addWidget(params)': 'layout.addWidget(params); self._inspector_sections["basic"].append(params)',
    'layout.addWidget(position)': 'layout.addWidget(position); self._inspector_sections["basic"].append(position)',
    'layout.addWidget(marks)': 'layout.addWidget(marks); self._inspector_sections["output"].append(marks); self.marks_section = marks',
    'layout.addWidget(duplex)': 'layout.addWidget(duplex); self._inspector_sections["basic"].append(duplex)',
    'layout.addWidget(cut_stack)': 'layout.addWidget(cut_stack); self._inspector_sections["production"].append(cut_stack); self.cut_stack_section = cut_stack',
    'layout.addWidget(cards)': 'layout.addWidget(cards); self._inspector_sections["production"].append(cards)',
    'layout.addWidget(labels)': 'layout.addWidget(labels); self._inspector_sections["production"].append(labels)',
    'layout.addWidget(special); self._apply_special_preset()': 'layout.addWidget(special); self._inspector_sections["production"].append(special); self._apply_special_preset()',
}
for old_part, new_part in replacements.items():
    text = replace_once(text, old_part, new_part, old_part)

old = '''        self.mix_status = QLabel("混拼队列：0 项"); self.mix_status.setObjectName("MixStatus"); self.mix_status.setWordWrap(True)
        layout.addWidget(self.mix_status)
        recalc = QPushButton("重新计算拼版"); recalc.setObjectName("PrimaryButton"); recalc.clicked.connect(self._auto_impose)
        layout.addWidget(recalc); layout.addStretch()
        scroll.setWidget(panel); return scroll
'''
new = '''        output = InspectorSection("生产输出与预检")
        self.preflight_summary = QLabel("0 错误 · 0 警告 · 等待检查"); self.preflight_summary.setObjectName("Muted"); self.preflight_summary.setWordWrap(True)
        preflight = QPushButton("执行印前检查"); preflight.setObjectName("SmallButton"); preflight.clicked.connect(self._run_host_preflight)
        export = QPushButton("导出生产 PDF"); export.setObjectName("PrimaryButton"); export.clicked.connect(self._export_host_pdf)
        output.form.addRow("状态", self.preflight_summary); output.form.addRow("", preflight); output.form.addRow("", export)
        layout.addWidget(output); self._inspector_sections["output"].append(output)
        self.mix_status = QLabel("混拼队列：0 项"); self.mix_status.setObjectName("MixStatus"); self.mix_status.setWordWrap(True)
        layout.addWidget(self.mix_status)
        recalc = QPushButton("重新计算拼版"); recalc.setObjectName("PrimaryButton"); recalc.clicked.connect(self._auto_impose)
        layout.addWidget(recalc); layout.addStretch(); self._set_inspector_group("basic")
        scroll.setWidget(panel); return scroll
'''
text = replace_once(text, old, new, "output inspector")

old = '''    def _run_host_preflight(self):
        host = self._prepare_host_job()
        if host is not None:
            host.run_preflight()
'''
new = '''    def _run_host_preflight(self):
        host = self._prepare_host_job()
        if host is not None:
            self.preflight_summary.setText("检查任务已提交 · 请查看主状态栏")
            self.status_preflight.setText("预检 执行中"); host.run_preflight()
'''
text = replace_once(text, old, new, "preflight status")

old = '''        pct = min(999.9, used/sheet*100.0); self.utilization.setText(f"{pct:.1f}%")
        scale = self.canvas.transform().m11()*100; self.zoom_label.setText(f"{scale:.0f}%")
'''
new = '''        pct = min(999.9, used/sheet*100.0); self.utilization.setText(f"{pct:.1f}%")
        self.status_pages.setText(f"页面 {len(self.pages)}"); self.status_placements.setText(f"版位 {len(items)}")
        scale = self.canvas.transform().m11()*100; self.zoom_label.setText(f"{scale:.0f}%")
'''
text = replace_once(text, old, new, "status metrics refresh")
ui_path.write_text(text, encoding="utf-8")

mode_path = root / "production_modes.py"
mode = mode_path.read_text(encoding="utf-8")
mode_start = mode.index('MODE_STYLE = """')
mode_end = mode.index('"""\n\n\ndef _spin', mode_start) + 3
mode_style = '''MODE_STYLE = """
QWidget#ProductionModes, QWidget#ImpositionWorkspace { background:#181c22; color:#d8dee9; }
QFrame#ModeBar { background:#11151a; border-bottom:1px solid #353b45; }
QLabel#ModeBrand { color:#f1f4f8; font-size:14px; font-weight:700; padding:0 12px; }
QPushButton#ModeButton { color:#96a3b4; background:transparent; border:0; border-bottom:2px solid transparent; padding:9px 22px; font-weight:700; }
QPushButton#ModeButton:checked { color:#67a9ff; background:#202a37; border-bottom-color:#2784f5; }
QFrame#ModePanel { background:#20252c; border:0; color:#d8dee9; }
QLabel#ModeTitle { color:#f0f3f8; font-size:17px; font-weight:700; }
QPushButton#PrimaryMode { background:#1473e6; color:white; border:0; border-radius:5px; min-height:38px; font-weight:700; }
QPushButton#SecondaryMode { background:#272d35; color:#d5dde8; border:1px solid #414956; border-radius:5px; min-height:32px; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background:#171b21; color:#dbe2ec; border:1px solid #3b434f; border-radius:4px; min-height:28px; padding:0 6px; }
QComboBox QAbstractItemView { background:#20252c; color:#dbe2ec; selection-background-color:#1769df; }
QTableWidget { background:#1b2026; color:#d8dee9; border:1px solid #39414c; gridline-color:#343b45; selection-background-color:#17365c; }
QHeaderView::section { background:#272d35; color:#c7d0dc; border:0; border-right:1px solid #3b434f; padding:5px; }
QSplitter::handle { background:#353b45; width:1px; }
"""'''
mode = mode[:mode_start] + mode_style + mode[mode_end:]
mode = mode.replace('painter.fillRect(self.rect(), QColor("#eef2f7"))', 'painter.fillRect(self.rect(), QColor("#181c22"))', 1)
mode = mode.replace('painter.setPen(QColor("#253247")); painter.drawText', 'painter.setPen(QColor("#d8dee9")); painter.drawText', 1)
mode = mode.replace('painter.fillRect(self.rect(), QColor("#eef2f7"))', 'painter.fillRect(self.rect(), QColor("#181c22"))', 1)

old = '''        bar=QFrame(); bar.setObjectName("ModeBar"); row=QHBoxLayout(bar); row.setContentsMargins(10,6,10,6)
        brand=QLabel("智印拼版"); brand.setObjectName("ModeBrand"); row.addWidget(brand)
'''
new = '''        bar=QFrame(); bar.setObjectName("ModeBar"); self.mode_bar = bar; row=QHBoxLayout(bar); row.setContentsMargins(10,6,10,6)
        self.brand=QLabel("智印拼版 · PRODUCTION WORKSPACE"); self.brand.setObjectName("ModeBrand"); row.addWidget(self.brand)
'''
mode = replace_once(mode, old, new, "mode brand")
old = '''            button=QPushButton(text); button.setObjectName("ModeButton"); button.setCheckable(True); button.setChecked(index==0); button.clicked.connect(lambda checked=False,i=index:self.stack.setCurrentIndex(i)); group.addButton(button); row.addWidget(button); self.mode_buttons.append(button); self.stack.addWidget(widget)
        row.addStretch(); self.mode_hint=QLabel("生产模式"); self.mode_hint.setStyleSheet("color:#9fb2ca;padding-right:12px;"); row.addWidget(self.mode_hint)
'''
new = '''            button=QPushButton(text); button.setObjectName("ModeButton"); button.setCheckable(True); button.setChecked(index==0); button.clicked.connect(lambda checked=False,i=index:self._set_mode(i)); group.addButton(button); row.addWidget(button); self.mode_buttons.append(button); self.stack.addWidget(widget)
        row.addStretch(); self.mode_hint=QLabel("单页生产工作台"); self.mode_hint.setStyleSheet("color:#8d9aab;padding-right:12px;"); row.addWidget(self.mode_hint)
'''
mode = replace_once(mode, old, new, "mode status hint")
old = '''    def bind_production_host(self, host): self.production_host=host; self.single_page.bind_production_host(host)
'''
new = '''    def _set_mode(self, index):
        self.stack.setCurrentIndex(index)
        self.mode_hint.setText(("单页生产工作台", "书刊折手与装订", "包装刀模与异形套料")[index])

    def bind_production_host(self, host): self.production_host=host; self.single_page.bind_production_host(host)
'''
mode = replace_once(mode, old, new, "mode switching")
mode_path.write_text(mode, encoding="utf-8")

for filename in ("product.py", "pyproject.toml", "installer_nsis.nsi"):
    path = root / filename
    path.write_text(path.read_text(encoding="utf-8").replace("2.4.28", "2.4.29"), encoding="utf-8")
for filename in ("professional_canvas.py", "production_modes.py", "test_v2429_professional_ui.py", "test_v2429_mode_ui.py"):
    compile((root / filename).read_text(encoding="utf-8"), str(root / filename), "exec")
(root / "V2429_PROFESSIONAL_UI.md").write_text("# V2.4.29 Professional UI\n\nDark production workspace, grouped inspector, canvas tool rail and production status metrics.\n", encoding="utf-8")
print("V2.4.29 professional workspace UI integrated")
