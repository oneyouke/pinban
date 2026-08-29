from pathlib import Path
import os
import shutil

root = Path(os.environ.get('APP_ROOT', 'build-src/Desktop-Imposer-Pro-V2.2')).resolve()
patch_root = Path(__file__).resolve().parent

shutil.copy2(patch_root / 'duplex_v243.py', root / 'duplex.py')
shutil.copy2(patch_root / 'test_v243_duplex.py', root / 'test_v243_duplex.py')

p = root / 'page_canvas.py'
s = p.read_text(encoding='utf-8')

s = s.replace('QDoubleSpinBox, QFileDialog, QFormLayout', 'QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout')
if 'from duplex import DuplexMode, Placement, map_backside' not in s:
    marker = 'try:\n    import fitz\n'
    if marker not in s:
        raise SystemExit('page canvas import marker missing')
    s = s.replace(marker, 'from duplex import DuplexMode, Placement, map_backside\n\n' + marker, 1)

canvas_marker = '\n\nclass PageCanvasWidget(QWidget):\n'
if canvas_marker not in s:
    raise SystemExit('PageCanvasWidget marker missing')
if 'def generate_backside' not in s:
    methods = '''
    def clear_backside(self):
        for item in list(self.scene().items()):
            if isinstance(item, PageItem) and getattr(item, 'side', 'front') == 'back':
                self.scene().removeItem(item)

    def generate_backside(self, mode):
        fronts = [x for x in self.scene().items()
                  if isinstance(x, PageItem) and getattr(x, 'side', 'front') == 'front']
        self.clear_backside()
        created = []
        for src in fronts:
            bounds = src.sceneBoundingRect()
            placement = Placement(src.x(), src.y(), bounds.width(), bounds.height(), int(src.rotation()) % 360)
            back = map_backside(placement, self.sheet_w, self.sheet_h, mode)
            item = PageItem(src.info, src.pixmap)
            item.side = 'back'
            item.setPos(back.x, back.y)
            item.setRotation(back.rotation)
            item.setFlag(QGraphicsItem.ItemIsMovable, False)
            item.setFlag(QGraphicsItem.ItemIsSelectable, False)
            item.setPen(QPen(QColor('#dc2626'), 0.8, Qt.DashLine))
            item.setOpacity(0.42)
            item.setZValue(20)
            item.setToolTip('反面预览 · ' + src.toolTip())
            self.scene().addItem(item)
            created.append(item)
        return created

    def set_backside_visible(self, visible):
        for item in self.scene().items():
            if isinstance(item, PageItem) and getattr(item, 'side', 'front') == 'back':
                item.setVisible(bool(visible))
'''
    s = s.replace(canvas_marker, methods + canvas_marker, 1)

bar_marker = "        root.addWidget(bar)\n\n        controls=QHBoxLayout(); form=QFormLayout()\n"
if bar_marker not in s:
    raise SystemExit('toolbar marker missing')
if 'self.duplex_mode=QComboBox()' not in s:
    duplex_ui = '''        root.addWidget(bar)

        duplex_row=QHBoxLayout()
        duplex_row.addWidget(QLabel('反面方式'))
        self.duplex_mode=QComboBox()
        self.duplex_mode.addItem('左右翻版', DuplexMode.LEFT_RIGHT.value)
        self.duplex_mode.addItem('天地翻版', DuplexMode.TOP_BOTTOM.value)
        self.duplex_mode.addItem('长边翻', DuplexMode.LONG_EDGE.value)
        self.duplex_mode.addItem('短边翻', DuplexMode.SHORT_EDGE.value)
        self.duplex_mode.addItem('自翻版 / 180°', DuplexMode.SELF_TURN.value)
        duplex_row.addWidget(self.duplex_mode)
        gen_back=QPushButton('生成反面叠加'); gen_back.clicked.connect(self._generate_backside)
        clear_back=QPushButton('清除反面叠加'); clear_back.clicked.connect(self.canvas.clear_backside)
        duplex_row.addWidget(gen_back); duplex_row.addWidget(clear_back); duplex_row.addStretch()
        root.addLayout(duplex_row)

        controls=QHBoxLayout(); form=QFormLayout()
'''
    s = s.replace(bar_marker, duplex_ui, 1)

method_marker = '    def _apply_sheet(self):\n'
if method_marker not in s:
    raise SystemExit('_apply_sheet marker missing')
if 'def _generate_backside' not in s:
    method = '''    def _generate_backside(self):
        self._apply_sheet()
        mode = self.duplex_mode.currentData()
        created = self.canvas.generate_backside(mode)
        if not created:
            QMessageBox.information(self, '反面预览', '请先把至少一个 PDF 页面加入画布。')

'''
    s = s.replace(method_marker, method + method_marker, 1)

s = s.replace("hint=QLabel('画布单位为 mm。支持精确坐标、1 mm 默认吸附、撤销/重做、居中、等距分布；虚线框用于版面安全/出血参考。生产 PDF 仍保持原矢量输出链路。')",
              "hint=QLabel('画布单位为 mm。支持精确坐标、吸附、撤销/重做、居中、等距分布，以及左右/天地/长边/短边/自翻版的半透明反面叠加核对。反面叠加当前用于几何预览；生产 PDF 仍保持原矢量输出链路。')")

p.write_text(s, encoding='utf-8')

for filename in ('product.py', 'pyproject.toml', 'installer_nsis.nsi'):
    fp = root / filename
    text = fp.read_text(encoding='utf-8').replace('2.4.2', '2.4.3')
    fp.write_text(text, encoding='utf-8')

compile((root / 'duplex.py').read_text(encoding='utf-8'), str(root / 'duplex.py'), 'exec')
compile((root / 'page_canvas.py').read_text(encoding='utf-8'), str(root / 'page_canvas.py'), 'exec')
compile((root / 'test_v243_duplex.py').read_text(encoding='utf-8'), str(root / 'test_v243_duplex.py'), 'exec')

(root / 'V243_DUPLEX_PREVIEW.md').write_text(
    '# V2.4.3 Duplex Mapping & Overlay\n\n'
    '- Adds deterministic left/right, top/bottom, long-edge, short-edge and self-turn mappings.\n'
    '- Mapping tests verify registration positions remain inside the sheet and are reversible.\n'
    '- Page canvas can generate a semi-transparent backside overlay for visual registration checks.\n'
    '- This slice is preview/mapping only; production PDF duplex emission remains on the existing vector output path.\n',
    encoding='utf-8',
)
print('V2.4.3 duplex mapping and overlay applied')
