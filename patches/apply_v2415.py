from pathlib import Path
import os, shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / 'layout_diagnostics_v2415.py', root / 'layout_diagnostics.py')
shutil.copy2(patch_root / 'test_v2415_layout_diagnostics.py', root / 'test_v2415_layout_diagnostics.py')

p = root / 'prepress_center.py'
s = p.read_text(encoding='utf-8')

# Import diagnostics next to the workspace integration when possible.
if 'from layout_diagnostics import collect_layout_diagnostics, format_layout_diagnostics' not in s:
    marker = 'from workspace import save_workspace, load_workspace\n'
    if marker in s:
        s = s.replace(marker, marker + 'from layout_diagnostics import collect_layout_diagnostics, format_layout_diagnostics\n', 1)
    else:
        # Fallback: insert before the first class definition without disturbing other imports.
        class_marker = '\n\nclass PrepressImpositionCenter'
        if class_marker not in s:
            raise SystemExit('prepress center class marker missing')
        s = s.replace(class_marker, '\nfrom layout_diagnostics import collect_layout_diagnostics, format_layout_diagnostics' + class_marker, 1)

# Add the diagnostics button to the V2.4 workspace control row.
if '手工版位生产诊断' not in s:
    marker = '        workspace_row.addWidget(save_ws); workspace_row.addWidget(load_ws); workspace_row.addStretch()\n'
    if marker not in s:
        raise SystemExit('workspace row marker missing')
    replacement = (
        '        workspace_row.addWidget(save_ws); workspace_row.addWidget(load_ws)\n'
        '        layout_diag = QPushButton("手工版位生产诊断")\n'
        '        layout_diag.clicked.connect(self._show_layout_diagnostics)\n'
        '        workspace_row.addWidget(layout_diag); workspace_row.addStretch()\n'
    )
    s = s.replace(marker, replacement, 1)

if 'def _show_layout_diagnostics(self):' not in s:
    marker = '    def _save_v24_workspace(self):\n'
    if marker not in s:
        raise SystemExit('workspace save method marker missing')
    method = '''    def _show_layout_diagnostics(self):
        try:
            report = collect_layout_diagnostics()
            text = format_layout_diagnostics(report)
        except Exception as exc:
            report = {'status': 'BLOCKED'}
            text = '手工版位生产状态：BLOCKED\\n\\n诊断执行失败：' + str(exc)
        box = QMessageBox(self)
        box.setWindowTitle('手工版位生产诊断')
        if report.get('status') == 'READY':
            box.setIcon(QMessageBox.Information)
            box.setText('当前生产引擎已公开可识别的手工版位契约。')
        else:
            box.setIcon(QMessageBox.Warning)
            box.setText('当前仍阻止手工版位生产，避免输出与画布不一致。')
        box.setDetailedText(text)
        box.setStandardButtons(QMessageBox.Ok)
        box.exec()

'''
    s = s.replace(marker, method + marker, 1)

p.write_text(s, encoding='utf-8')

for filename in ('product.py','pyproject.toml','installer_nsis.nsi'):
    fp = root / filename
    text = fp.read_text(encoding='utf-8').replace('2.4.14', '2.4.15')
    fp.write_text(text, encoding='utf-8')

for filename in ('layout_contract.py','layout_diagnostics.py','test_v2415_layout_diagnostics.py','prepress_center.py'):
    compile((root/filename).read_text(encoding='utf-8'), str(root/filename), 'exec')

(root/'V2415_LAYOUT_DIAGNOSTICS.md').write_text(
    '# V2.4.15 Manual Layout Production Diagnostics\n\n'
    '- Adds runtime diagnostics for impose_jobs and atomic_production_export.\n'
    '- Reports whether layout_override exists and whether its typed dataclass contract is safely mappable.\n'
    '- Shows detected field semantics for x/y/page/job/rotation/width/height.\n'
    '- Adds a Prepress Center button that shows READY/BLOCKED plus detailed reasons.\n'
    '- Keeps manual-layout production fail-closed when the contract is ambiguous.\n',
    encoding='utf-8'
)
print('V2.4.15 layout diagnostics integrated')
