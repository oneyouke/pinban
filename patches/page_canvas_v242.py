from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPixmap, QUndoCommand, QUndoStack
from PySide6.QtWidgets import (
    QDoubleSpinBox, QFileDialog, QFormLayout, QGraphicsItem, QGraphicsRectItem,
    QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QSplitter, QToolBar, QVBoxLayout, QWidget,
)

try:
    import fitz
except Exception:
    fitz = None


@dataclass
class PageInfo:
    path: str
    page_index: int
    width_pt: float
    height_pt: float
    rotation: int = 0

    @property
    def width_mm(self):
        return self.width_pt * 25.4 / 72.0

    @property
    def height_mm(self):
        return self.height_pt * 25.4 / 72.0


class MoveCommand(QUndoCommand):
    def __init__(self, item, old_pos, new_pos, text='移动版位'):
        super().__init__(text)
        self.item, self.old_pos, self.new_pos = item, old_pos, new_pos
    def undo(self): self.item.setPos(self.old_pos)
    def redo(self): self.item.setPos(self.new_pos)


class RotateCommand(QUndoCommand):
    def __init__(self, item, old_angle, new_angle):
        super().__init__('旋转版位')
        self.item, self.old_angle, self.new_angle = item, old_angle, new_angle
    def undo(self): self.item.setRotation(self.old_angle)
    def redo(self): self.item.setRotation(self.new_angle)


class PageItem(QGraphicsRectItem):
    def __init__(self, info: PageInfo, pixmap: QPixmap | None = None):
        super().__init__(0, 0, max(20.0, info.width_mm), max(20.0, info.height_mm))
        self.info = info
        self.locked = False
        self.pixmap = pixmap
        self.drag_start = None
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.setPen(QPen(QColor('#3777c2'), 0.6))
        self.setBrush(QBrush(QColor(255, 255, 255)))
        self.setToolTip(f'{Path(info.path).name} · P{info.page_index + 1}\n{info.width_mm:.2f} × {info.height_mm:.2f} mm')

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        r = self.rect().adjusted(1, 1, -1, -1)
        if self.pixmap and not self.pixmap.isNull():
            painter.drawPixmap(r.toRect(), self.pixmap)
        painter.setPen(QPen(Qt.black, 0.4))
        painter.drawText(r.adjusted(3, 3, -3, -3), Qt.AlignTop | Qt.AlignLeft, f'P{self.info.page_index + 1}')

    def set_locked(self, locked: bool):
        self.locked = locked
        self.setFlag(QGraphicsItem.ItemIsMovable, not locked)
        self.setOpacity(0.72 if locked else 1.0)


class ImpositionCanvas(QGraphicsView):
    def __init__(self):
        scene = QGraphicsScene()
        super().__init__()
        # Explicitly bind the scene. This is more robust than relying on the
        # overloaded QGraphicsView(scene) constructor across PySide6 versions.
        self.setScene(scene)
        self.undo_stack = QUndoStack(self)
        self.snap_mm = 1.0
        self.sheet_w = 650.0
        self.sheet_h = 450.0
        self.bleed_mm = 3.0
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.sheet = QGraphicsRectItem(0, 0, self.sheet_w, self.sheet_h)
        self.sheet.setBrush(QBrush(QColor(245, 245, 245)))
        self.sheet.setPen(QPen(QColor(80, 80, 80), 1.2))
        self.sheet.setZValue(-100)
        scene.addItem(self.sheet)
        self.bleed_box = QGraphicsRectItem(self.bleed_mm, self.bleed_mm, self.sheet_w-2*self.bleed_mm, self.sheet_h-2*self.bleed_mm)
        self.bleed_box.setBrush(Qt.NoBrush)
        self.bleed_box.setPen(QPen(QColor('#d97706'), 0.6, Qt.DashLine))
        self.bleed_box.setZValue(-90)
        scene.addItem(self.bleed_box)
        self._update_scene_rect()

    def _update_scene_rect(self):
        self.scene().setSceneRect(-30, -30, self.sheet_w + 60, self.sheet_h + 60)

    def set_sheet(self, width_mm, height_mm, bleed_mm):
        self.sheet_w, self.sheet_h, self.bleed_mm = float(width_mm), float(height_mm), float(bleed_mm)
        self.sheet.setRect(0, 0, self.sheet_w, self.sheet_h)
        b = max(0.0, self.bleed_mm)
        self.bleed_box.setRect(b, b, max(0.0, self.sheet_w-2*b), max(0.0, self.sheet_h-2*b))
        self._update_scene_rect()

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1/1.15
        self.scale(factor, factor)

    def add_page(self, info, pixmap=None):
        item = PageItem(info, pixmap)
        n = len([x for x in self.scene().items() if isinstance(x, PageItem)])
        item.setPos(10 + (n % 4) * (item.rect().width() + 8), 10 + (n // 4) * (item.rect().height() + 8))
        self.scene().addItem(item)
        return item

    def selected_pages(self):
        return [x for x in self.scene().selectedItems() if isinstance(x, PageItem)]

    def snap_value(self, value):
        g = max(0.1, float(self.snap_mm))
        return round(float(value) / g) * g

    def set_selected_position(self, x, y):
        for item in self.selected_pages():
            if item.locked: continue
            old = item.pos(); new = old.__class__(self.snap_value(x), self.snap_value(y))
            self.undo_stack.push(MoveCommand(item, old, new, '设置坐标'))

    def rotate_selected(self):
        for item in self.selected_pages():
            if item.locked: continue
            old = item.rotation(); new = (old + 90) % 360
            self.undo_stack.push(RotateCommand(item, old, new))
            item.info.rotation = int(new)

    def delete_selected(self):
        for item in self.selected_pages():
            if not item.locked: self.scene().removeItem(item)

    def toggle_lock_selected(self):
        for item in self.selected_pages(): item.set_locked(not item.locked)

    def _move_many(self, mapping, text):
        self.undo_stack.beginMacro(text)
        for item, new in mapping:
            if not item.locked and item.pos() != new:
                self.undo_stack.push(MoveCommand(item, item.pos(), new, text))
        self.undo_stack.endMacro()

    def align_left(self):
        items = self.selected_pages()
        if len(items) < 2: return
        x = min(i.x() for i in items)
        self._move_many([(i, i.pos().__class__(x, i.y())) for i in items], '左对齐')

    def align_top(self):
        items = self.selected_pages()
        if len(items) < 2: return
        y = min(i.y() for i in items)
        self._move_many([(i, i.pos().__class__(i.x(), y)) for i in items], '顶对齐')

    def center_horizontal(self):
        items = self.selected_pages()
        if not items: return
        mapping=[]
        for i in items:
            x=(self.sheet_w-i.sceneBoundingRect().width())/2
            mapping.append((i, i.pos().__class__(self.snap_value(x), i.y())))
        self._move_many(mapping, '水平居中')

    def center_vertical(self):
        items = self.selected_pages()
        if not items: return
        mapping=[]
        for i in items:
            y=(self.sheet_h-i.sceneBoundingRect().height())/2
            mapping.append((i, i.pos().__class__(i.x(), self.snap_value(y))))
        self._move_many(mapping, '垂直居中')

    def distribute_horizontal(self):
        items = sorted(self.selected_pages(), key=lambda i: i.x())
        if len(items) < 3: return
        left, right = items[0].x(), items[-1].x()
        step = (right-left)/(len(items)-1)
        self._move_many([(i, i.pos().__class__(self.snap_value(left+n*step), i.y())) for n,i in enumerate(items)], '水平等距')

    def distribute_vertical(self):
        items = sorted(self.selected_pages(), key=lambda i: i.y())
        if len(items) < 3: return
        top, bottom = items[0].y(), items[-1].y()
        step = (bottom-top)/(len(items)-1)
        self._move_many([(i, i.pos().__class__(i.x(), self.snap_value(top+n*step))) for n,i in enumerate(items)], '垂直等距')


class PageCanvasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pages=[]; self.thumbs={}
        root=QVBoxLayout(self)
        self.canvas=ImpositionCanvas()

        bar=QToolBar()
        a=bar.addAction('导入 PDF'); a.triggered.connect(self.import_pdf)
        bar.addSeparator()
        for text, fn in [
            ('旋转 90°', self.canvas.rotate_selected), ('删除', self.canvas.delete_selected),
            ('锁定/解锁', self.canvas.toggle_lock_selected), ('撤销', self.canvas.undo_stack.undo),
            ('重做', self.canvas.undo_stack.redo), ('左对齐', self.canvas.align_left), ('顶对齐', self.canvas.align_top),
            ('水平居中', self.canvas.center_horizontal), ('垂直居中', self.canvas.center_vertical),
            ('水平等距', self.canvas.distribute_horizontal), ('垂直等距', self.canvas.distribute_vertical),
        ]:
            a=bar.addAction(text); a.triggered.connect(fn)
        root.addWidget(bar)

        controls=QHBoxLayout(); form=QFormLayout()
        self.sheet_w=QDoubleSpinBox(); self.sheet_w.setRange(20,3000); self.sheet_w.setValue(650); self.sheet_w.setSuffix(' mm')
        self.sheet_h=QDoubleSpinBox(); self.sheet_h.setRange(20,3000); self.sheet_h.setValue(450); self.sheet_h.setSuffix(' mm')
        self.bleed=QDoubleSpinBox(); self.bleed.setRange(0,50); self.bleed.setValue(3); self.bleed.setSuffix(' mm')
        self.snap=QDoubleSpinBox(); self.snap.setRange(0.1,50); self.snap.setValue(1); self.snap.setSuffix(' mm')
        self.xpos=QDoubleSpinBox(); self.xpos.setRange(-3000,3000); self.xpos.setDecimals(2); self.xpos.setSuffix(' mm')
        self.ypos=QDoubleSpinBox(); self.ypos.setRange(-3000,3000); self.ypos.setDecimals(2); self.ypos.setSuffix(' mm')
        for label,w in [('纸宽',self.sheet_w),('纸高',self.sheet_h),('出血框偏移',self.bleed),('吸附步长',self.snap),('X',self.xpos),('Y',self.ypos)]: form.addRow(label,w)
        apply_sheet=QPushButton('应用纸张'); apply_sheet.clicked.connect(self._apply_sheet)
        apply_pos=QPushButton('设置选中坐标'); apply_pos.clicked.connect(self._apply_pos)
        controls.addLayout(form); controls.addWidget(apply_sheet); controls.addWidget(apply_pos); controls.addStretch()
        root.addLayout(controls)

        split=QSplitter(); left=QWidget(); ll=QVBoxLayout(left); ll.addWidget(QLabel('PDF 页面（双击加入画布）'))
        self.list=QListWidget(); self.list.setIconSize(QPixmap(120,160).size()); self.list.itemDoubleClicked.connect(self.add_selected_page); ll.addWidget(self.list,1)
        split.addWidget(left); split.addWidget(self.canvas); split.setStretchFactor(1,1); root.addWidget(split,1)
        hint=QLabel('画布单位为 mm。支持精确坐标、1 mm 默认吸附、撤销/重做、居中、等距分布；虚线框用于版面安全/出血参考。生产 PDF 仍保持原矢量输出链路。')
        hint.setWordWrap(True); root.addWidget(hint)

    def _apply_sheet(self):
        self.canvas.snap_mm=self.snap.value(); self.canvas.set_sheet(self.sheet_w.value(), self.sheet_h.value(), self.bleed.value())

    def _apply_pos(self):
        self.canvas.snap_mm=self.snap.value(); self.canvas.set_selected_position(self.xpos.value(), self.ypos.value())

    def import_pdf(self):
        paths,_=QFileDialog.getOpenFileNames(self,'导入 PDF','','PDF (*.pdf)')
        for path in paths: self._load_pdf(path)

    def _load_pdf(self,path):
        if fitz is None:
            QMessageBox.warning(self,'缺少 PDF 预览组件','当前运行环境没有 PyMuPDF，无法生成页面缩略图。'); return
        try:
            doc=fitz.open(path)
            for idx,page in enumerate(doc):
                rect=page.rect; info=PageInfo(path,idx,float(rect.width),float(rect.height),int(page.rotation or 0))
                pm=page.get_pixmap(matrix=fitz.Matrix(0.28,0.28),alpha=False)
                fmt=QImage.Format_RGB888 if pm.n==3 else QImage.Format_RGBA8888
                pixmap=QPixmap.fromImage(QImage(pm.samples,pm.width,pm.height,pm.stride,fmt).copy())
                self.pages.append(info); self.thumbs[(path,idx)]=pixmap
                item=QListWidgetItem(f'{Path(path).name} · P{idx+1}\n{info.width_mm:.2f} × {info.height_mm:.2f} mm')
                item.setData(Qt.UserRole,len(self.pages)-1); item.setIcon(pixmap); self.list.addItem(item)
        except Exception as exc:
            QMessageBox.critical(self,'PDF 导入失败',str(exc))

    def add_selected_page(self,item):
        idx=int(item.data(Qt.UserRole)); info=self.pages[idx]; self.canvas.add_page(info,self.thumbs.get((info.path,info.page_index)))
