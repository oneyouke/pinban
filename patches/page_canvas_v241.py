from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QGraphicsItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QSplitter, QToolBar, QVBoxLayout, QWidget,
)

try:
    import fitz  # PyMuPDF
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


class PageItem(QGraphicsRectItem):
    def __init__(self, info: PageInfo, pixmap: QPixmap | None = None):
        super().__init__(0, 0, max(20.0, info.width_mm), max(20.0, info.height_mm))
        self.info = info
        self.locked = False
        self.pixmap = pixmap
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setPen(QPen(QColor("#3777c2"), 0.6))
        self.setBrush(QBrush(QColor(255, 255, 255)))
        self.setToolTip(f"{Path(info.path).name} · P{info.page_index + 1}\n{info.width_mm:.2f} × {info.height_mm:.2f} mm")

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        r = self.rect().adjusted(1, 1, -1, -1)
        if self.pixmap and not self.pixmap.isNull():
            painter.drawPixmap(r.toRect(), self.pixmap)
        painter.setPen(QPen(Qt.black, 0.4))
        painter.drawText(r.adjusted(3, 3, -3, -3), Qt.AlignTop | Qt.AlignLeft,
                         f"P{self.info.page_index + 1}")

    def set_locked(self, locked: bool):
        self.locked = locked
        self.setFlag(QGraphicsItem.ItemIsMovable, not locked)
        self.setOpacity(0.72 if locked else 1.0)


class ImpositionCanvas(QGraphicsView):
    def __init__(self):
        scene = QGraphicsScene()
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.sheet = QGraphicsRectItem(0, 0, 650, 450)
        self.sheet.setBrush(QBrush(QColor(245, 245, 245)))
        self.sheet.setPen(QPen(QColor(80, 80, 80), 1.2))
        self.sheet.setZValue(-100)
        scene.addItem(self.sheet)
        scene.setSceneRect(-30, -30, 710, 510)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def add_page(self, info: PageInfo, pixmap: QPixmap | None = None):
        item = PageItem(info, pixmap)
        n = len([x for x in self.scene().items() if isinstance(x, PageItem)])
        x = 10 + (n % 4) * (item.rect().width() + 8)
        y = 10 + (n // 4) * (item.rect().height() + 8)
        item.setPos(x, y)
        self.scene().addItem(item)
        return item

    def selected_pages(self):
        return [x for x in self.scene().selectedItems() if isinstance(x, PageItem)]

    def rotate_selected(self):
        for item in self.selected_pages():
            if item.locked:
                continue
            item.setRotation((item.rotation() + 90) % 360)
            item.info.rotation = int(item.rotation())

    def delete_selected(self):
        for item in self.selected_pages():
            if not item.locked:
                self.scene().removeItem(item)

    def toggle_lock_selected(self):
        for item in self.selected_pages():
            item.set_locked(not item.locked)

    def align_left(self):
        items = self.selected_pages()
        if len(items) < 2:
            return
        x = min(i.x() for i in items)
        for i in items:
            if not i.locked:
                i.setX(x)

    def align_top(self):
        items = self.selected_pages()
        if len(items) < 2:
            return
        y = min(i.y() for i in items)
        for i in items:
            if not i.locked:
                i.setY(y)


class PageCanvasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pages: list[PageInfo] = []
        self.thumbs: dict[tuple[str, int], QPixmap] = {}

        root = QVBoxLayout(self)
        bar = QToolBar()
        add = bar.addAction("导入 PDF")
        add.triggered.connect(self.import_pdf)
        bar.addSeparator()
        a = bar.addAction("旋转 90°"); a.triggered.connect(self._rotate)
        a = bar.addAction("删除"); a.triggered.connect(self._delete)
        a = bar.addAction("锁定/解锁"); a.triggered.connect(self.canvas.toggle_lock_selected)
        bar.addSeparator()
        a = bar.addAction("左对齐"); a.triggered.connect(self.canvas.align_left)
        a = bar.addAction("顶对齐"); a.triggered.connect(self.canvas.align_top)
        root.addWidget(bar)

        split = QSplitter()
        left = QWidget(); ll = QVBoxLayout(left)
        ll.addWidget(QLabel("PDF 页面（双击加入画布）"))
        self.list = QListWidget()
        self.list.setIconSize(QPixmap(120, 160).size())
        self.list.itemDoubleClicked.connect(self.add_selected_page)
        ll.addWidget(self.list, 1)
        split.addWidget(left)

        self.canvas = ImpositionCanvas()
        split.addWidget(self.canvas)
        split.setStretchFactor(1, 1)
        root.addWidget(split, 1)

        hint = QLabel("画布支持：拖动、框选、多选、滚轮缩放、90°旋转、删除、锁定、左/顶对齐。当前页面内容仅用于预览；生产 PDF 仍由原矢量 PDF 输出链路生成。")
        hint.setWordWrap(True)
        root.addWidget(hint)

    def import_pdf(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "导入 PDF", "", "PDF (*.pdf)")
        for path in paths:
            self._load_pdf(path)

    def _load_pdf(self, path: str):
        if fitz is None:
            QMessageBox.warning(self, "缺少 PDF 预览组件", "当前运行环境没有 PyMuPDF，无法生成页面缩略图。")
            return
        try:
            doc = fitz.open(path)
            for idx, page in enumerate(doc):
                rect = page.rect
                info = PageInfo(path, idx, float(rect.width), float(rect.height), int(page.rotation or 0))
                mat = fitz.Matrix(0.28, 0.28)
                pm = page.get_pixmap(matrix=mat, alpha=False)
                fmt = QImage.Format_RGB888 if pm.n == 3 else QImage.Format_RGBA8888
                image = QImage(pm.samples, pm.width, pm.height, pm.stride, fmt).copy()
                pixmap = QPixmap.fromImage(image)
                self.pages.append(info)
                self.thumbs[(path, idx)] = pixmap
                item = QListWidgetItem(f"{Path(path).name} · P{idx+1}\n{info.width_mm:.2f} × {info.height_mm:.2f} mm")
                item.setData(Qt.UserRole, len(self.pages) - 1)
                item.setIcon(pixmap)
                self.list.addItem(item)
        except Exception as exc:
            QMessageBox.critical(self, "PDF 导入失败", str(exc))

    def add_selected_page(self, item: QListWidgetItem):
        idx = int(item.data(Qt.UserRole))
        info = self.pages[idx]
        self.canvas.add_page(info, self.thumbs.get((info.path, info.page_index)))

    def _rotate(self):
        self.canvas.rotate_selected()

    def _delete(self):
        self.canvas.delete_selected()
