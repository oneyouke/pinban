from pathlib import Path
import os, shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / 'layout_diagnostics_v2417.py', root / 'layout_diagnostics.py')
shutil.copy2(patch_root / 'test_v2417_legacy_dict.py', root / 'test_v2417_legacy_dict.py')

p = root / 'prepress_center.py'
s = p.read_text(encoding='utf-8')
old = """        if hasattr(self, 'layout_gate_status'):\n            if gate.get('ready'):\n                self.layout_gate_status.setText('手工版位生产：READY')\n                self.layout_gate_status.setToolTip('当前生产引擎契约可安全识别。输出前仍会重新检查。')\n            else:\n                reasons = '; '.join(str(x) for x in gate.get('reasons') or [])\n                self.layout_gate_status.setText('手工版位生产：BLOCKED')\n                self.layout_gate_status.setToolTip(reasons or '当前生产引擎契约未通过安全检查')\n"""
new = """        if hasattr(self, 'layout_gate_status'):\n            raw_status = str((gate.get('diagnostics') or {}).get('status') or gate.get('status') or 'BLOCKED').upper()\n            if gate.get('ready'):\n                self.layout_gate_status.setText('手工版位生产：READY')\n                self.layout_gate_status.setToolTip('当前生产引擎契约可安全识别。输出前仍会重新检查。')\n            else:\n                reasons = '; '.join(str(x) for x in gate.get('reasons') or [])\n                if raw_status == 'LEGACY_DICT':\n                    self.layout_gate_status.setText('手工版位生产：LEGACY_DICT（安全阻止）')\n                else:\n                    self.layout_gate_status.setText('手工版位生产：BLOCKED')\n                self.layout_gate_status.setToolTip(reasons or '当前生产引擎契约未通过安全检查')\n"""
if old not in s:
    raise SystemExit('V2.4.16 layout gate status block missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

for filename in ('product.py','pyproject.toml','installer_nsis.nsi'):
    fp = root / filename
    fp.write_text(fp.read_text(encoding='utf-8').replace('2.4.16','2.4.17'), encoding='utf-8')

for filename in ('layout_diagnostics.py','test_v2417_legacy_dict.py','prepress_center.py'):
    compile((root/filename).read_text(encoding='utf-8'), str(root/filename), 'exec')

(root/'V2417_LEGACY_DICT_CONTRACT.md').write_text(
    '# V2.4.17 Legacy Dict Layout Contract Awareness\n\n'
    '- Detects the existing production engine layout_override: dict contract explicitly.\n'
    '- Distinguishes LEGACY_DICT from generic BLOCKED and typed READY contracts.\n'
    '- Keeps production fail-closed because dict key names, coordinate units, page numbering and job-index semantics are not yet verified.\n'
    '- Prepress Center shows LEGACY_DICT (safe blocked) instead of falsely reporting no layout support.\n',
    encoding='utf-8'
)
print('V2.4.17 legacy dict contract awareness integrated')
