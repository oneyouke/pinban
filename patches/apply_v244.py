from pathlib import Path
import os
import shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / 'print_marks_v244.py', root / 'print_marks.py')
shutil.copy2(patch_root / 'marks_panel_v244.py', root / 'marks_panel.py')
shutil.copy2(patch_root / 'test_v244_marks.py', root / 'test_v244_marks.py')

p = root / 'prepress_center.py'
s = p.read_text(encoding='utf-8')
if 'from marks_panel import PrintMarksPanel' not in s:
    marker = 'from page_canvas import PageCanvasWidget\n'
    if marker not in s:
        raise SystemExit('page canvas import marker missing')
    s = s.replace(marker, marker + 'from marks_panel import PrintMarksPanel\n', 1)

if '"印刷标记"' not in s:
    marker = '        tabs.addTab(PageCanvasWidget(self), "页面与画布")\n'
    if marker not in s:
        raise SystemExit('page canvas tab marker missing')
    s = s.replace(marker, marker + '        tabs.addTab(PrintMarksPanel(self), "印刷标记")\n', 1)
p.write_text(s, encoding='utf-8')

for filename in ('product.py', 'pyproject.toml', 'installer_nsis.nsi'):
    fp = root / filename
    text = fp.read_text(encoding='utf-8').replace('2.4.3', '2.4.4')
    fp.write_text(text, encoding='utf-8')

for filename in ('print_marks.py','marks_panel.py','prepress_center.py','test_v244_marks.py'):
    compile((root / filename).read_text(encoding='utf-8'), str(root / filename), 'exec')

(root / 'V244_PRINT_MARKS.md').write_text(
    '# V2.4.4 Vector Print Marks\n\n'
    '- Adds configurable crop marks: length, offset and stroke width.\n'
    '- Adds registration crosses, CMYK color bar, file name, plate number, date and front/back labels.\n'
    '- Adds gripper-direction arrow with top/bottom/left/right selection.\n'
    '- Adds a dedicated print-marks configuration/preview tab.\n'
    '- The print-mark engine includes direct PyMuPDF vector drawing helpers for production PDF integration; no screenshot/raster output is used.\n'
    '- Existing production PDF path remains unchanged in this slice until explicit exporter wiring is validated.\n',
    encoding='utf-8',
)
print('V2.4.4 vector print marks applied')
