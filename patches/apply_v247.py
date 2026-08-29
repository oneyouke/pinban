from pathlib import Path
import os
import shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / 'mix_optimizer_v247.py', root / 'mix_optimizer.py')
shutil.copy2(patch_root / 'test_v247_optimizer.py', root / 'test_v247_optimizer.py')

p = root / 'page_canvas.py'
s = p.read_text(encoding='utf-8')

# Imports.
s = s.replace('QMessageBox, QPushButton, QSplitter, QToolBar, QVBoxLayout, QWidget,',
              'QMessageBox, QPushButton, QSpinBox, QSplitter, QToolBar, QVBoxLayout, QWidget,')
if 'from mix_optimizer import ProductSpec, optimize_mixed' not in s:
    marker = 'from duplex import DuplexMode, Placement, map_backside\n'
    if marker not in s:
        raise SystemExit('duplex import marker missing')
    s = s.replace(marker, marker + 'from mix_optimizer import ProductSpec, optimize_mixed\n', 1)

# State.
marker = '        self.pages=[]; self.thumbs={}\n'
if marker not in s:
    raise SystemExit('page canvas state marker missing')
if 'self.mix_entries=[]' not in s:
    s = s.replace(marker, marker + '        self.mix_entries=[]\n', 1)

# Mixed-imposition control row before duplex controls.
marker = '        duplex_row=QHBoxLayout()\n'
if marker not in s:
    raise SystemExit('duplex row marker missing')
if '自动最省纸混拼' not in s:
    ui = '''        mix_row=QHBoxLayout()
        mix_row.addWidget(QLabel('混拼需求数量'))
        self.mix_qty=QSpinBox(); self.mix_qty.setRange(1,10000000); self.mix_qty.setValue(100)
        mix_row.addWidget(self.mix_qty)
        add_mix=QPushButton('加入混拼队列'); add_mix.clicked.connect(self._add_mix_current)
        clear_mix=QPushButton('清空混拼队列'); clear_mix.clicked.connect(self._clear_mix)
        run_mix=QPushButton('自动最省纸混拼'); run_mix.clicked.connect(self._run_mixed_optimizer)
        mix_row.addWidget(add_mix); mix_row.addWidget(clear_mix); mix_row.addWidget(run_mix)
        self.mix_status=QLabel('混拼队列：0 项')
        mix_row.addWidget(self.mix_status,1)
        root.addLayout(mix_row)

'''
    s = s.replace(marker, ui + marker, 1)

# Methods.
marker = '    def _generate_backside(self):\n'
if marker not in s:
    raise SystemExit('generate backside marker missing')
if 'def _run_mixed_optimizer' not in s:
    methods = '''    def _add_mix_current(self):
        item=self.list.currentItem()
        if item is None:
            QMessageBox.information(self,'混拼','请先在左侧页面列表选择一个 PDF 页面。'); return
        page_idx=int(item.data(Qt.UserRole))
        qty=int(self.mix_qty.value())
        for row in self.mix_entries:
            if row['page_idx']==page_idx:
                row['quantity']=qty; break
        else:
            self.mix_entries.append({'page_idx':page_idx,'quantity':qty})
        self._refresh_mix_status()

    def _clear_mix(self):
        self.mix_entries=[]
        self._refresh_mix_status()

    def _refresh_mix_status(self, result=None):
        parts=[]
        for row in self.mix_entries:
            idx=row['page_idx']
            if 0 <= idx < len(self.pages):
                info=self.pages[idx]
                parts.append(f'P{info.page_index+1}×{row["quantity"]}')
        text='混拼队列：' + (', '.join(parts) if parts else '0 项')
        if result is not None:
            text += f' ｜ 已拼 {len(result.items)} 件 ｜ 利用率 {result.utilization*100:.1f}% ｜ {result.strategy}'
        self.mix_status.setText(text)

    def _run_mixed_optimizer(self):
        if not self.mix_entries:
            QMessageBox.information(self,'混拼','请先选择页面并加入混拼队列。'); return
        specs=[]
        source_by_key={}
        for row in self.mix_entries:
            idx=int(row['page_idx'])
            if not (0 <= idx < len(self.pages)): continue
            info=self.pages[idx]
            key=str(idx)
            source_by_key[key]=(info,self.thumbs.get((info.path,info.page_index)))
            specs.append(ProductSpec(key,info.width_mm,info.height_mm,int(row['quantity']),True))
        if not specs: return
        self._apply_sheet()
        gap=max(0.0,float(self.snap.value()))
        result=optimize_mixed(specs,self.sheet_w.value(),self.sheet_h.value(),margin_mm=max(3.0,self.bleed.value()),gap_x_mm=gap,gap_y_mm=gap)
        if not result.items:
            QMessageBox.warning(self,'混拼失败','当前纸张尺寸无法容纳混拼队列中的产品。'); return
        self.canvas.clear_backside()
        for old in list(self.canvas.scene().items()):
            if isinstance(old,PageItem) and getattr(old,'side','front')=='front': self.canvas.scene().removeItem(old)
        for packed in result.items:
            info,pix=source_by_key[packed.key]
            page_item=self.canvas.add_page(info,pix)
            if int(packed.rotation)==90:
                # QGraphicsItem rotates around origin; shift X so its scene bounding-box starts at optimizer X.
                page_item.setRotation(90)
                page_item.setPos(float(packed.x_mm)+float(packed.width_mm),float(packed.y_mm))
            else:
                page_item.setRotation(0)
                page_item.setPos(float(packed.x_mm),float(packed.y_mm))
            page_item.info.rotation=int(packed.rotation)
        self.canvas.undo_stack.clear()
        self._refresh_mix_status(result)

'''
    s = s.replace(marker, methods + marker, 1)

# Persist the mix queue inside the V2.4 workspace.
old = "            'placements': placements,\n        }\n"
if old in s and "'mix_entries':" not in s:
    s = s.replace(old, "            'placements': placements,\n            'mix_entries': list(self.mix_entries),\n        }\n", 1)
old = "        state = state or {}\n        sheet = state.get('sheet') or {}\n"
if old in s and "self.mix_entries=list(state.get('mix_entries')" not in s:
    s = s.replace(old, "        state = state or {}\n        self.mix_entries=list(state.get('mix_entries') or [])\n        if hasattr(self,'_refresh_mix_status'): self._refresh_mix_status()\n        sheet = state.get('sheet') or {}\n", 1)

p.write_text(s, encoding='utf-8')

for filename in ('product.py','pyproject.toml','installer_nsis.nsi'):
    fp=root/filename
    fp.write_text(fp.read_text(encoding='utf-8').replace('2.4.6','2.4.7'),encoding='utf-8')

for filename in ('mix_optimizer.py','test_v247_optimizer.py','page_canvas.py'):
    compile((root/filename).read_text(encoding='utf-8'),str(root/filename),'exec')

(root/'V247_MIX_OPTIMIZER.md').write_text(
    '# V2.4.7 Mixed Imposition Optimizer\n\n'
    '- Adds page + quantity mixed-imposition queue.\n'
    '- Normalizes order quantities into production ratios.\n'
    '- Tries multiple ordering and rotation policies and selects the best candidate by packed count, utilization and ratio error.\n'
    '- One-click result is placed on the editable V2.4 canvas.\n'
    '- Mix queue is persisted in the V2.4 workspace.\n', encoding='utf-8')
print('V2.4.7 mixed optimizer integrated')
