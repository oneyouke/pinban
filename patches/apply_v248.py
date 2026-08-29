from pathlib import Path
import os
import shutil

root=Path(os.environ.get('APP_ROOT','build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root=Path(__file__).resolve().parent

shutil.copy2(patch_root/'resource_matcher_v248.py',root/'resource_matcher.py')
shutil.copy2(patch_root/'resource_panel_v248.py',root/'resource_panel.py')
shutil.copy2(patch_root/'test_v248_resources.py',root/'test_v248_resources.py')

p=root/'prepress_center.py'; s=p.read_text(encoding='utf-8')
if 'from resource_panel import ResourceMatchPanel' not in s:
    marker='from workspace import save_workspace, load_workspace\n'
    if marker not in s: raise SystemExit('workspace import marker missing')
    s=s.replace(marker,marker+'from resource_panel import ResourceMatchPanel\n',1)

old='        self.page_canvas = PageCanvasWidget(self)\n        self.marks_panel = PrintMarksPanel(self)\n        tabs.addTab(self.page_canvas, "页面与画布")\n        tabs.addTab(self.marks_panel, "印刷标记")\n'
if old in s:
    new='        self.page_canvas = PageCanvasWidget(self)\n        self.resources_panel = ResourceMatchPanel(self.page_canvas, self)\n        self.marks_panel = PrintMarksPanel(self)\n        tabs.addTab(self.page_canvas, "页面与画布")\n        tabs.addTab(self.resources_panel, "纸张/印刷机匹配")\n        tabs.addTab(self.marks_panel, "印刷标记")\n'
    s=s.replace(old,new,1)
elif 'self.resources_panel = ResourceMatchPanel' not in s:
    raise SystemExit('V2.4 panel integration marker missing')

old="                'page_canvas': self.page_canvas.export_state(),\n                'print_marks': self.marks_panel.export_state()}\n"
if old in s:
    s=s.replace(old,"                'page_canvas': self.page_canvas.export_state(),\n                'resources': self.resources_panel.export_state(),\n                'print_marks': self.marks_panel.export_state()}\n",1)
elif "'resources': self.resources_panel.export_state()" not in s:
    raise SystemExit('workspace save payload marker missing')

old="            self.page_canvas.import_state(data.get('page_canvas') or {})\n            self.marks_panel.import_state(data.get('print_marks') or {})\n"
if old in s:
    s=s.replace(old,"            self.page_canvas.import_state(data.get('page_canvas') or {})\n            self.resources_panel.import_state(data.get('resources') or {})\n            self.marks_panel.import_state(data.get('print_marks') or {})\n",1)
elif "self.resources_panel.import_state" not in s:
    raise SystemExit('workspace load payload marker missing')
p.write_text(s,encoding='utf-8')

for filename in ('product.py','pyproject.toml','installer_nsis.nsi'):
    fp=root/filename
    fp.write_text(fp.read_text(encoding='utf-8').replace('2.4.7','2.4.8'),encoding='utf-8')

for filename in ('resource_matcher.py','resource_panel.py','prepress_center.py','test_v248_resources.py'):
    compile((root/filename).read_text(encoding='utf-8'),str(root/filename),'exec')

(root/'V248_RESOURCE_MATCHING.md').write_text(
    '# V2.4.8 Paper & Press Matching\n\n'
    '- Editable paper library and press library.\n'
    '- Press constraints include maximum sheet dimensions and gripper allowance.\n'
    '- Compares normal/rotated sheet orientations and mixed-imposition strategies.\n'
    '- Calculates per-sheet counts, required production sheets, total paper area and utilization.\n'
    '- Ranks primarily by total paper area consumed, then sheet count and utilization.\n'
    '- Selected recommendation can be applied directly to the editable canvas.\n'
    '- Resource libraries persist inside the V2.4 workspace.\n',encoding='utf-8')
print('V2.4.8 resource matching integrated')
