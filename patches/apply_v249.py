from pathlib import Path
import os
import shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / 'production_planner_v249.py', root / 'production_planner.py')
shutil.copy2(patch_root / 'production_panel_v249.py', root / 'production_panel.py')
shutil.copy2(patch_root / 'test_v249_production.py', root / 'test_v249_production.py')

p = root / 'prepress_center.py'
s = p.read_text(encoding='utf-8')
if 'from production_panel import ProductionCalculatorPanel' not in s:
    marker = 'from workspace import save_workspace, load_workspace\n'
    if marker not in s:
        raise SystemExit('workspace import marker missing')
    s = s.replace(marker, marker + 'from production_panel import ProductionCalculatorPanel\n', 1)

marker = '        self.marks_panel = PrintMarksPanel(self)\n'
if marker not in s:
    raise SystemExit('marks panel instance marker missing')
if 'self.production_panel = ProductionCalculatorPanel' not in s:
    s = s.replace(marker, marker + '        self.production_panel = ProductionCalculatorPanel(self.page_canvas, self)\n', 1)

marker = '        tabs.addTab(self.marks_panel, "印刷标记")\n'
if marker not in s:
    raise SystemExit('marks tab marker missing')
if '"生产计算"' not in s:
    s = s.replace(marker, marker + '        tabs.addTab(self.production_panel, "生产计算")\n', 1)

# Save and restore production calculator state in the additive workspace payload.
old = "                'print_marks': self.marks_panel.export_state()}\n"
if old in s and "'production':" not in s:
    s = s.replace(old, "                'print_marks': self.marks_panel.export_state(),\n                'production': self.production_panel.export_state()}\n", 1)

old = "            self.marks_panel.import_state(data.get('print_marks') or {})\n"
if old in s and "production_panel.import_state" not in s:
    s = s.replace(old, old + "            self.production_panel.import_state(data.get('production') or {})\n", 1)

p.write_text(s, encoding='utf-8')

for filename in ('product.py','pyproject.toml','installer_nsis.nsi'):
    fp = root / filename
    fp.write_text(fp.read_text(encoding='utf-8').replace('2.4.8','2.4.9'), encoding='utf-8')

for filename in ('production_planner.py','production_panel.py','test_v249_production.py','prepress_center.py'):
    compile((root/filename).read_text(encoding='utf-8'), str(root/filename), 'exec')

(root/'V249_PRODUCTION_CALCULATOR.md').write_text(
    '# V2.4.9 Production Calculator\n\n'
    '- Order quantity, pieces per sheet, spoilage rate and make-ready sheets.\n'
    '- Theoretical sheets, spoilage allowance, actual production sheets, produced pieces and surplus.\n'
    '- Paper cost, print cost, total cost and per-order-piece cost.\n'
    '- Can count front-side placements from the V2.4 canvas.\n'
    '- Production inputs are persisted in the additive V2.4 workspace.\n',
    encoding='utf-8')
print('V2.4.9 production calculator integrated')
