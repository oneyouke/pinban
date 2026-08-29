from pathlib import Path
import os
import shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent

# Install page/canvas module and smoke test.
shutil.copy2(patch_root / 'page_canvas_v241.py', root / 'page_canvas.py')
shutil.copy2(patch_root / 'test_v241_ui.py', root / 'test_v241_ui.py')

# Fix toolbar bindings so they resolve self.canvas only when the action is triggered.
p = root / 'page_canvas.py'
s = p.read_text(encoding='utf-8')
s = s.replace('a = bar.addAction("锁定/解锁"); a.triggered.connect(self.canvas.toggle_lock_selected)',
              'a = bar.addAction("锁定/解锁"); a.triggered.connect(lambda: self.canvas.toggle_lock_selected())')
s = s.replace('a = bar.addAction("左对齐"); a.triggered.connect(self.canvas.align_left)',
              'a = bar.addAction("左对齐"); a.triggered.connect(lambda: self.canvas.align_left())')
s = s.replace('a = bar.addAction("顶对齐"); a.triggered.connect(self.canvas.align_top)',
              'a = bar.addAction("顶对齐"); a.triggered.connect(lambda: self.canvas.align_top())')
p.write_text(s, encoding='utf-8')

# Integrate a dedicated Page & Canvas tab into the prepress center.
p = root / 'prepress_center.py'
s = p.read_text(encoding='utf-8')
if 'from page_canvas import PageCanvasWidget' not in s:
    marker = 'from booklet import saddle_stitch, perfect_bound_sections\n'
    if marker not in s:
        raise SystemExit('prepress_center import marker missing')
    s = s.replace(marker, marker + 'from page_canvas import PageCanvasWidget\n', 1)

if '"页面与画布"' not in s:
    marker = '        tabs.addTab(self._booklet_tab(), "折手规划")\n'
    if marker not in s:
        raise SystemExit('prepress_center tab marker missing')
    s = s.replace(marker, marker + '        tabs.addTab(PageCanvasWidget(self), "页面与画布")\n', 1)
p.write_text(s, encoding='utf-8')

# Version bump.
for filename in ('product.py', 'pyproject.toml', 'installer_nsis.nsi'):
    p = root / filename
    text = p.read_text(encoding='utf-8').replace('2.4.0', '2.4.1')
    p.write_text(text, encoding='utf-8')

compile((root / 'page_canvas.py').read_text(encoding='utf-8'), str(root / 'page_canvas.py'), 'exec')
compile((root / 'prepress_center.py').read_text(encoding='utf-8'), str(root / 'prepress_center.py'), 'exec')
compile((root / 'test_v241_ui.py').read_text(encoding='utf-8'), str(root / 'test_v241_ui.py'), 'exec')

(root / 'V241_PAGE_CANVAS.md').write_text(
    '# V2.4.1 PDF Page Manager & Imposition Canvas\n\n'
    '- Multi-PDF page list with thumbnails when PyMuPDF is available.\n'
    '- Shows page number and physical page dimensions.\n'
    '- Double-click page to place it on the imposition canvas.\n'
    '- Drag, multi-select, zoom, rotate 90 degrees, delete, lock/unlock.\n'
    '- Basic left/top alignment.\n'
    '- Preview rendering remains separate from production PDF output; vector output path is unchanged.\n',
    encoding='utf-8',
)
print('V2.4.1 page manager and imposition canvas applied')
