from pathlib import Path
import os
import shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / 'page_canvas_v242.py', root / 'page_canvas.py')
shutil.copy2(patch_root / 'test_v242_ui.py', root / 'test_v242_ui.py')

for filename in ('product.py','pyproject.toml','installer_nsis.nsi'):
    p=root/filename
    text=p.read_text(encoding='utf-8').replace('2.4.1','2.4.2')
    p.write_text(text,encoding='utf-8')

compile((root/'page_canvas.py').read_text(encoding='utf-8'), str(root/'page_canvas.py'), 'exec')
compile((root/'test_v242_ui.py').read_text(encoding='utf-8'), str(root/'test_v242_ui.py'), 'exec')

(root/'V242_PRECISE_CANVAS.md').write_text(
    '# V2.4.2 Precise Imposition Canvas\n\n'
    '- Exact X/Y placement in millimeters.\n'
    '- Configurable snap grid, default 1 mm.\n'
    '- Undo/redo for coordinate, alignment, distribution and rotation operations.\n'
    '- Horizontal/vertical centering.\n'
    '- Horizontal/vertical equal distribution.\n'
    '- Editable sheet width/height and visual bleed/safe reference box.\n'
    '- Existing vector production PDF path remains unchanged.\n', encoding='utf-8')
print('V2.4.2 precise canvas editing applied')
