from pathlib import Path
import os, shutil

root=Path(os.environ.get('APP_ROOT','build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root=Path(__file__).resolve().parent
for src,dst in [('order_quote_v2410.py','order_quote.py'),('order_quote_panel_v2410.py','order_quote_panel.py'),('test_v2410_quote.py','test_v2410_quote.py')]: shutil.copy2(patch_root/src,root/dst)

p=root/'prepress_center.py'; s=p.read_text(encoding='utf-8')
if 'from order_quote_panel import OrderQuotePanel' not in s:
    marker='from production_panel import ProductionCalculatorPanel\n'
    if marker not in s: raise SystemExit('production panel import marker missing')
    s=s.replace(marker,marker+'from order_quote_panel import OrderQuotePanel\n',1)
marker='        self.production_panel = ProductionCalculatorPanel(self.page_canvas, self)\n'
if marker not in s: raise SystemExit('production panel instance marker missing')
if 'self.order_quote_panel = OrderQuotePanel' not in s:
    s=s.replace(marker,marker+'        self.order_quote_panel = OrderQuotePanel(self.page_canvas, self)\n',1)
marker='        tabs.addTab(self.production_panel, "生产计算")\n'
if marker not in s: raise SystemExit('production tab marker missing')
if '"订单与报价"' not in s:
    s=s.replace(marker,marker+'        tabs.addTab(self.order_quote_panel, "订单与报价")\n',1)
old="                'production': self.production_panel.export_state()}\n"
if old in s and "'order_quote':" not in s:
    s=s.replace(old,"                'production': self.production_panel.export_state(),\n                'order_quote': self.order_quote_panel.export_state()}\n",1)
old="            self.production_panel.import_state(data.get('production') or {})\n"
if old in s and 'order_quote_panel.import_state' not in s:
    s=s.replace(old,old+"            self.order_quote_panel.import_state(data.get('order_quote') or {})\n",1)
p.write_text(s,encoding='utf-8')

for filename in ('product.py','pyproject.toml','installer_nsis.nsi'):
    fp=root/filename; fp.write_text(fp.read_text(encoding='utf-8').replace('2.4.9','2.4.10'),encoding='utf-8')
for filename in ('order_quote.py','order_quote_panel.py','test_v2410_quote.py','prepress_center.py'):
    compile((root/filename).read_text(encoding='utf-8'),str(root/filename),'exec')
(root/'V2410_ORDER_QUOTE.md').write_text('# V2.4.10 Order & Quote\n\n- Multi-line production orders with per-item quantity and pieces-per-sheet.\n- Per-item produced quantity, surplus, allocated cost and allocated quote.\n- Configurable fixed cost and markup percentage; no hard-coded business margin.\n- CSV/JSON detail export for audit and handoff.\n- Quote inputs are persisted in the additive V2.4 workspace.\n',encoding='utf-8')
print('V2.4.10 order and quote integrated')
