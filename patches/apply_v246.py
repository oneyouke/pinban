from pathlib import Path
import os
import shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / 'workspace_v246.py', root / 'workspace.py')
shutil.copy2(patch_root / 'test_v246_workspace.py', root / 'test_v246_workspace.py')

# Page/canvas state export + restore.
p = root / 'page_canvas.py'
s = p.read_text(encoding='utf-8')
marker = '    def _apply_sheet(self):\n'
if marker not in s:
    raise SystemExit('page canvas _apply_sheet marker missing')
if 'def export_state(self):' not in s:
    methods = '''    def export_state(self):
        placements=[]
        for item in self.canvas.scene().items():
            if not isinstance(item, PageItem) or getattr(item, 'side', 'front') != 'front':
                continue
            placements.append({
                'path': item.info.path, 'page_index': int(item.info.page_index),
                'width_pt': float(item.info.width_pt), 'height_pt': float(item.info.height_pt),
                'x_mm': float(item.x()), 'y_mm': float(item.y()),
                'rotation': int(item.rotation()) % 360, 'locked': bool(item.locked),
            })
        return {
            'sheet': {'width_mm': self.sheet_w.value(), 'height_mm': self.sheet_h.value(),
                      'bleed_mm': self.bleed.value(), 'snap_mm': self.snap.value()},
            'duplex_mode': self.duplex_mode.currentData() if hasattr(self, 'duplex_mode') else '',
            'placements': placements,
        }

    def import_state(self, state):
        state = state or {}
        sheet = state.get('sheet') or {}
        self.sheet_w.setValue(float(sheet.get('width_mm', self.sheet_w.value())))
        self.sheet_h.setValue(float(sheet.get('height_mm', self.sheet_h.value())))
        self.bleed.setValue(float(sheet.get('bleed_mm', self.bleed.value())))
        self.snap.setValue(float(sheet.get('snap_mm', self.snap.value())))
        self._apply_sheet()
        if hasattr(self, 'duplex_mode'):
            wanted = str(state.get('duplex_mode') or '')
            for i in range(self.duplex_mode.count()):
                if str(self.duplex_mode.itemData(i)) == wanted:
                    self.duplex_mode.setCurrentIndex(i); break
        for item in list(self.canvas.scene().items()):
            if isinstance(item, PageItem): self.canvas.scene().removeItem(item)
        for row in state.get('placements') or []:
            info = PageInfo(str(row.get('path') or ''), int(row.get('page_index', 0)),
                            float(row.get('width_pt', 0) or 0), float(row.get('height_pt', 0) or 0),
                            int(row.get('rotation', 0) or 0))
            item = self.canvas.add_page(info, self.thumbs.get((info.path, info.page_index)))
            item.setPos(float(row.get('x_mm', 0) or 0), float(row.get('y_mm', 0) or 0))
            item.setRotation(int(row.get('rotation', 0) or 0) % 360)
            item.set_locked(bool(row.get('locked', False)))
        self.canvas.undo_stack.clear()

'''
    s = s.replace(marker, methods + marker, 1)
p.write_text(s, encoding='utf-8')

# Print-marks panel state export + restore.
p = root / 'marks_panel.py'
s = p.read_text(encoding='utf-8')
marker = '    def refresh_preview(self):\n'
if marker not in s:
    raise SystemExit('marks panel refresh marker missing')
if 'def export_state(self):' not in s:
    methods = '''    def export_state(self):
        cfg = self.config()
        data = dict(cfg.__dict__)
        data.update({'file_text': self.file.text(), 'plate_text': self.plate_no.text(), 'side_text': self.side_text.currentText()})
        return data

    def import_state(self, state):
        state = state or {}
        checks = [('crop_marks',self.crop),('register_marks',self.register),('color_bar',self.colorbar),
                  ('file_name',self.filename),('plate_no',self.plate),('date',self.date),
                  ('side_label',self.side),('gripper_arrow',self.gripper)]
        for key, widget in checks:
            if key in state: widget.setChecked(bool(state[key]))
        nums = [('crop_length_mm',self.length),('crop_offset_mm',self.offset),('crop_width_pt',self.width),
                ('register_radius_mm',self.radius),('text_size_pt',self.textsize)]
        for key, widget in nums:
            if key in state: widget.setValue(float(state[key]))
        edge = str(state.get('gripper_edge') or '')
        i = self.edge.findText(edge)
        if i >= 0: self.edge.setCurrentIndex(i)
        if 'file_text' in state: self.file.setText(str(state['file_text']))
        if 'plate_text' in state: self.plate_no.setText(str(state['plate_text']))
        side = str(state.get('side_text') or '')
        i = self.side_text.findText(side)
        if i >= 0: self.side_text.setCurrentIndex(i)
        self.refresh_preview()

'''
    s = s.replace(marker, methods + marker, 1)
p.write_text(s, encoding='utf-8')

# Prepress-center UI integration.
p = root / 'prepress_center.py'
s = p.read_text(encoding='utf-8')
if 'from workspace import save_workspace, load_workspace' not in s:
    marker = 'from marks_panel import PrintMarksPanel\n'
    if marker not in s: raise SystemExit('marks panel import marker missing')
    s = s.replace(marker, marker + 'from workspace import save_workspace, load_workspace\n', 1)

old = '        tabs.addTab(PageCanvasWidget(self), "页面与画布")\n        tabs.addTab(PrintMarksPanel(self), "印刷标记")\n'
if old in s:
    new = '        self.page_canvas = PageCanvasWidget(self)\n        self.marks_panel = PrintMarksPanel(self)\n        tabs.addTab(self.page_canvas, "页面与画布")\n        tabs.addTab(self.marks_panel, "印刷标记")\n'
    s = s.replace(old, new, 1)
elif 'self.page_canvas = PageCanvasWidget(self)' not in s:
    raise SystemExit('prepress center V2.4 tabs marker missing')

close_marker = '        close_btn = QPushButton("关闭")\n'
if close_marker not in s: raise SystemExit('close button marker missing')
if '保存 V2.4 工作区' not in s:
    ins = '''        workspace_row = QHBoxLayout()
        save_ws = QPushButton("保存 V2.4 工作区")
        save_ws.clicked.connect(self._save_v24_workspace)
        load_ws = QPushButton("打开 V2.4 工作区")
        load_ws.clicked.connect(self._load_v24_workspace)
        workspace_row.addWidget(save_ws); workspace_row.addWidget(load_ws); workspace_row.addStretch()
        root.addLayout(workspace_row)

'''
    s = s.replace(close_marker, ins + close_marker, 1)

method_marker = '    def _button(self, text, method_name):\n'
if method_marker not in s: raise SystemExit('prepress method marker missing')
if 'def _save_v24_workspace' not in s:
    methods = '''    def _save_v24_workspace(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存 V2.4 工作区", "拼版工作区.dipw", "Desktop Imposer Workspace (*.dipw);;JSON (*.json)")
        if not path: return
        data = {'schema_version': 1, 'app_version': '2.4.6',
                'page_canvas': self.page_canvas.export_state(),
                'print_marks': self.marks_panel.export_state()}
        actual = save_workspace(path, data)
        QMessageBox.information(self, "保存完成", f"工作区已保存：\\n{actual}")

    def _load_v24_workspace(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开 V2.4 工作区", "", "Desktop Imposer Workspace (*.dipw *.json)")
        if not path: return
        try:
            data = load_workspace(path)
            self.page_canvas.import_state(data.get('page_canvas') or {})
            self.marks_panel.import_state(data.get('print_marks') or {})
        except Exception as exc:
            QMessageBox.critical(self, "打开失败", str(exc)); return
        QMessageBox.information(self, "恢复完成", "V2.4 纸张、版位、翻版和印刷标记配置已恢复。")

'''
    s = s.replace(method_marker, methods + method_marker, 1)
p.write_text(s, encoding='utf-8')

for filename in ('product.py','pyproject.toml','installer_nsis.nsi'):
    fp=root/filename
    fp.write_text(fp.read_text(encoding='utf-8').replace('2.4.5','2.4.6'), encoding='utf-8')

for filename in ('workspace.py','page_canvas.py','marks_panel.py','prepress_center.py','test_v246_workspace.py'):
    compile((root/filename).read_text(encoding='utf-8'), str(root/filename), 'exec')

(root/'V246_WORKSPACE_PERSISTENCE.md').write_text(
    '# V2.4.6 Workspace Persistence\n\n- Atomic .dipw/JSON workspace save.\n- Restores sheet, bleed, snap, front placements, rotation and lock state.\n- Restores duplex mode and print-mark configuration.\n- Keeps source PDF path/page references without rasterizing source artwork.\n- Uses a versioned additive workspace schema to avoid silently changing legacy project files.\n', encoding='utf-8')
print('V2.4.6 workspace persistence applied')
