from pathlib import Path
import os, shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent
for src, dst in [
    ('template_store_v2411.py', 'template_store.py'),
    ('template_panel_v2411.py', 'template_panel.py'),
    ('test_v2411_templates.py', 'test_v2411_templates.py'),
]:
    shutil.copy2(patch_root / src, root / dst)

p = root / 'prepress_center.py'
s = p.read_text(encoding='utf-8')

if 'from template_panel import TemplateManagerPanel' not in s:
    marker = 'from order_quote_panel import OrderQuotePanel\n'
    if marker not in s:
        raise SystemExit('order quote import marker missing')
    s = s.replace(marker, marker + 'from template_panel import TemplateManagerPanel\n', 1)

instance_marker = '        self.order_quote_panel = OrderQuotePanel(self.page_canvas, self)\n'
if instance_marker not in s:
    raise SystemExit('order quote instance marker missing')
if 'self.template_panel = TemplateManagerPanel' not in s:
    s = s.replace(
        instance_marker,
        instance_marker + '        self.template_panel = TemplateManagerPanel(self._capture_template_workspace, self._apply_template_workspace, self)\n',
        1,
    )

tab_marker = '        tabs.addTab(self.order_quote_panel, "订单与报价")\n'
if tab_marker not in s:
    raise SystemExit('order quote tab marker missing')
if 'tabs.addTab(self.template_panel, "生产模板")' not in s:
    s = s.replace(tab_marker, tab_marker + '        tabs.addTab(self.template_panel, "生产模板")\n', 1)

method_marker = '    def _save_v24_workspace(self):\n'
if method_marker not in s:
    raise SystemExit('workspace save method marker missing')
if 'def _capture_template_workspace(self):' not in s:
    methods = '''    def _capture_template_workspace(self):
        return {
            'schema_version': 1,
            'app_version': '2.4.11',
            'page_canvas': self.page_canvas.export_state(),
            'resources': self.resources_panel.export_state(),
            'print_marks': self.marks_panel.export_state(),
            'production': self.production_panel.export_state(),
            'order_quote': self.order_quote_panel.export_state(),
        }

    def _apply_template_workspace(self, data):
        data = data or {}
        self.page_canvas.import_state(data.get('page_canvas') or {})
        self.resources_panel.import_state(data.get('resources') or {})
        self.marks_panel.import_state(data.get('print_marks') or {})
        self.production_panel.import_state(data.get('production') or {})
        self.order_quote_panel.import_state(data.get('order_quote') or {})

'''
    s = s.replace(method_marker, methods + method_marker, 1)

p.write_text(s, encoding='utf-8')

for filename in ('product.py', 'pyproject.toml', 'installer_nsis.nsi'):
    fp = root / filename
    fp.write_text(fp.read_text(encoding='utf-8').replace('2.4.10', '2.4.11'), encoding='utf-8')

for filename in ('template_store.py', 'template_panel.py', 'test_v2411_templates.py', 'prepress_center.py'):
    compile((root / filename).read_text(encoding='utf-8'), str(root / filename), 'exec')

(root / 'V2411_PRODUCTION_TEMPLATES.md').write_text(
    '# V2.4.11 Production Template Library\n\n'
    '- Versioned JSON template library with atomic writes.\n'
    '- Save/overwrite/delete/import/export templates.\n'
    '- Captures canvas/sheet/duplex references, paper/press resources, print marks, production calculation and order quote settings.\n'
    '- Templates keep source PDF references only; PDF bytes are not copied or rasterized.\n'
    '- One-click apply restores the captured production workspace into editable panels.\n',
    encoding='utf-8',
)
print('V2.4.11 production template library integrated')
