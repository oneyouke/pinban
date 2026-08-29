from pathlib import Path
import os, shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / 'production_safety_v2416.py', root / 'production_safety.py')
shutil.copy2(patch_root / 'test_v2416_production_safety.py', root / 'test_v2416_production_safety.py')

# Prepress-center persistent status + refresh/export diagnostics.
p = root / 'prepress_center.py'
s = p.read_text(encoding='utf-8')

if 'from production_safety import evaluate_manual_layout_gate, export_diagnostics_json' not in s:
    marker = 'from layout_diagnostics import collect_layout_diagnostics, format_layout_diagnostics\n'
    if marker not in s:
        raise SystemExit('V2.4.15 diagnostics import marker missing')
    s = s.replace(marker, marker + 'from production_safety import evaluate_manual_layout_gate, export_diagnostics_json\n', 1)

if '手工版位生产：' not in s:
    marker = '        layout_diag = QPushButton("手工版位生产诊断")\n'
    if marker not in s:
        raise SystemExit('V2.4.15 diagnostics button marker missing')
    block = (
        '        self.layout_gate_status = QLabel("手工版位生产：检查中…")\n'
        '        self.layout_gate_status.setTextInteractionFlags(Qt.TextSelectableByMouse)\n'
        '        workspace_row.addWidget(self.layout_gate_status)\n'
        '        refresh_gate = QPushButton("刷新生产状态")\n'
        '        refresh_gate.clicked.connect(self._refresh_layout_gate_status)\n'
        '        workspace_row.addWidget(refresh_gate)\n'
        '        export_diag = QPushButton("导出诊断 JSON")\n'
        '        export_diag.clicked.connect(self._export_layout_diagnostics_json)\n'
        '        workspace_row.addWidget(export_diag)\n'
    )
    s = s.replace(marker, block + marker, 1)

if 'def _refresh_layout_gate_status(self):' not in s:
    marker = '    def _show_layout_diagnostics(self):\n'
    if marker not in s:
        raise SystemExit('V2.4.15 diagnostics method marker missing')
    methods = '''    def _refresh_layout_gate_status(self):
        try:
            gate = evaluate_manual_layout_gate(collect_layout_diagnostics())
        except Exception as exc:
            gate = {'ready': False, 'status': 'BLOCKED', 'reasons': [str(exc)]}
        if hasattr(self, 'layout_gate_status'):
            if gate.get('ready'):
                self.layout_gate_status.setText('手工版位生产：READY')
                self.layout_gate_status.setToolTip('当前生产引擎契约可安全识别。输出前仍会重新检查。')
            else:
                reasons = '; '.join(str(x) for x in gate.get('reasons') or [])
                self.layout_gate_status.setText('手工版位生产：BLOCKED')
                self.layout_gate_status.setToolTip(reasons or '当前生产引擎契约未通过安全检查')
        return gate

    def _export_layout_diagnostics_json(self):
        path, _ = QFileDialog.getSaveFileName(self, '导出生产诊断', 'Desktop-Imposer-Production-Diagnostics.json', 'JSON (*.json)')
        if not path:
            return
        try:
            from product import APP_VERSION
            actual = export_diagnostics_json(path, APP_VERSION, collect_layout_diagnostics())
        except Exception as exc:
            QMessageBox.critical(self, '导出失败', str(exc)); return
        QMessageBox.information(self, '导出完成', f'生产诊断已导出：\\n{actual}')

'''
    s = s.replace(marker, methods + marker, 1)

# Refresh once after the UI is built. Insert before the close button setup if available.
if 'self._refresh_layout_gate_status()  # V2.4.16' not in s:
    marker = '        close_btn = QPushButton("关闭")\n'
    if marker not in s:
        raise SystemExit('close button marker missing')
    s = s.replace(marker, '        self._refresh_layout_gate_status()  # V2.4.16\n' + marker, 1)

p.write_text(s, encoding='utf-8')

# Batch executor: use the same live safety gate for manual-layout rejection.
p = root / 'batch_executor.py'
s = p.read_text(encoding='utf-8')
if 'from production_safety import require_manual_layout_safe, ProductionSafetyError' not in s:
    marker = 'from production_service import atomic_production_export\n'
    if marker not in s:
        raise SystemExit('batch executor production import marker missing')
    s = s.replace(marker, marker + 'from production_safety import require_manual_layout_safe, ProductionSafetyError\n', 1)

old = "    if _has_manual_layout(page_canvas):\n        raise ValueError('当前批量生产仅支持自动拼版工作区；检测到手工版位。为避免输出与画布不一致，本任务已阻止。')\n"
if old in s:
    new = "    if _has_manual_layout(page_canvas):\n        try:\n            require_manual_layout_safe()\n        except ProductionSafetyError as exc:\n            raise ValueError(str(exc)) from exc\n        raise ValueError('当前生产引擎契约虽已通过诊断，但 V2.4.16 尚未启用手工版位 layout_override 提交；本任务继续阻止，避免输出与画布不一致。')\n"
    s = s.replace(old, new, 1)
elif 'V2.4.16 尚未启用手工版位 layout_override 提交' not in s:
    raise SystemExit('batch executor manual-layout marker missing')
p.write_text(s, encoding='utf-8')

for filename in ('product.py','pyproject.toml','installer_nsis.nsi'):
    fp = root / filename
    text = fp.read_text(encoding='utf-8').replace('2.4.15', '2.4.16')
    fp.write_text(text, encoding='utf-8')

for filename in ('production_safety.py','test_v2416_production_safety.py','prepress_center.py','batch_executor.py'):
    compile((root/filename).read_text(encoding='utf-8'), str(root/filename), 'exec')

(root/'V2416_PRODUCTION_SAFETY_GATE.md').write_text(
    '# V2.4.16 Production Safety Gate\n\n'
    '- Persistent READY/BLOCKED manual-layout production status in Prepress Center.\n'
    '- Explicit refresh performs a fresh runtime contract diagnosis.\n'
    '- Batch manual-layout path uses the same live gate and remains fail-closed until layout_override submission is proven.\n'
    '- Atomic JSON diagnostic export includes app version, UTC timestamp, status, reasons and raw diagnostics.\n'
    '- No manual-layout production output is enabled merely because diagnostics say READY.\n',
    encoding='utf-8'
)
print('V2.4.16 production safety gate integrated')
