from __future__ import annotations

import json
import re
from pathlib import Path
from xml.etree import ElementTree

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout,
    QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QSplitter, QStackedWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from booklet import perfect_bound_sections, saddle_stitch
from nesting import NestItem, nest_polygons_multi_sheet
from professional_canvas import ProfessionalPageCanvasWidget


MODE_STYLE = """
QWidget#ProductionModes { background:#edf1f6; color:#172033; }
QFrame#ModeBar { background:#0d2748; border:0; }
QLabel#ModeBrand { color:white; font-size:15px; font-weight:700; padding:0 12px; }
QPushButton#ModeButton { color:#cad8e9; background:transparent; border:0; border-radius:5px; padding:9px 22px; font-weight:700; }
QPushButton#ModeButton:checked { color:white; background:#1769df; }
QFrame#ModePanel { background:white; border:0; }
QLabel#ModeTitle { color:#172033; font-size:17px; font-weight:700; }
QPushButton#PrimaryMode { background:#1266d8; color:white; border:0; border-radius:6px; min-height:38px; font-weight:700; }
QPushButton#SecondaryMode { background:white; border:1px solid #cbd3df; border-radius:6px; min-height:32px; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background:white; border:1px solid #cfd6e0; border-radius:5px; min-height:28px; padding:0 6px; }
QTableWidget { background:white; border:1px solid #d9e0e9; gridline-color:#e4e9f0; }
"""


def _spin(value, minimum, maximum, decimals=1, suffix=""):
    widget = QDoubleSpinBox()
    widget.setRange(minimum, maximum)
    widget.setDecimals(decimals)
    widget.setValue(value)
    widget.setSuffix(suffix)
    return widget


class BookSheetPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(620, 390)
        self.front = None
        self.back = None
        self.sheet_w = 450.0
        self.sheet_h = 320.0
        self.spine = 0.0
        self.fold_lines = True
        self.flip = "长边翻"

    def set_spreads(self, front, back, sheet_w, sheet_h, spine, fold_lines, flip):
        self.front, self.back = front, back
        self.sheet_w, self.sheet_h = float(sheet_w), float(sheet_h)
        self.spine, self.fold_lines, self.flip = float(spine), bool(fold_lines), str(flip)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#eef2f7"))
        margin, gap = 28, 24
        available_w = self.width() - margin * 2
        panel_w = (available_w - gap) / 2
        panel_h = self.height() - 74
        ratio = self.sheet_w / max(1.0, self.sheet_h)
        draw_w = min(panel_w, panel_h * ratio)
        draw_h = draw_w / ratio
        if draw_h > panel_h:
            draw_h = panel_h; draw_w = draw_h * ratio
        for index, (label, spread) in enumerate((("正面大版", self.front), ("背面大版", self.back))):
            x = margin + index * (panel_w + gap) + (panel_w - draw_w) / 2
            y = 46 + (panel_h - draw_h) / 2
            rect = QRectF(x, y, draw_w, draw_h)
            painter.setPen(QPen(QColor("#1769df"), 2)); painter.setBrush(QColor("white")); painter.drawRect(rect)
            painter.setPen(QColor("#253247")); painter.drawText(QRectF(x, 14, draw_w, 24), Qt.AlignCenter, label)
            if spread is None:
                painter.setPen(QColor("#8b96a7")); painter.drawText(rect, Qt.AlignCenter, "等待计算")
                continue
            center_x = rect.center().x()
            if self.spine > 0:
                spine_px = min(draw_w * .18, self.spine / max(1.0, self.sheet_w) * draw_w)
                painter.fillRect(QRectF(center_x - spine_px / 2, rect.top(), spine_px, rect.height()), QColor(237, 119, 183, 55))
            if self.fold_lines:
                painter.setPen(QPen(QColor("#e552a1"), 1, Qt.DashLine)); painter.drawLine(QPointF(center_x, rect.top()), QPointF(center_x, rect.bottom()))
            painter.setPen(QPen(QColor("#d7dde7"), 1)); painter.drawLine(QPointF(center_x, rect.top()), QPointF(center_x, rect.bottom()))
            painter.setPen(QColor("#1c3150"))
            left = "空白" if spread.left is None else f"P{spread.left}"
            right = "空白" if spread.right is None else f"P{spread.right}"
            painter.drawText(QRectF(rect.left(), rect.top(), rect.width()/2, rect.height()), Qt.AlignCenter, left)
            painter.drawText(QRectF(center_x, rect.top(), rect.width()/2, rect.height()), Qt.AlignCenter, right)
            footer = f"第 {spread.signature} 帖 · 第 {spread.sheet} 张 · 爬移 {spread.creep_mm:.3f} mm · {self.flip}"
            painter.setPen(QColor("#65748a")); painter.drawText(QRectF(rect.left(), rect.bottom()-28, rect.width(), 22), Qt.AlignCenter, footer)


class BookImpositionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plan = []
        self.source_path = ""
        root = QHBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(1)
        split = QSplitter(Qt.Horizontal); root.addWidget(split)

        controls = QFrame(); controls.setObjectName("ModePanel"); controls.setMinimumWidth(280); controls.setMaximumWidth(350)
        left = QVBoxLayout(controls); left.setContentsMargins(16, 14, 16, 14)
        title = QLabel("书籍拼版"); title.setObjectName("ModeTitle"); left.addWidget(title)
        self.file_label = QLineEdit(); self.file_label.setReadOnly(True); self.file_label.setPlaceholderText("尚未导入书籍 PDF")
        import_btn = QPushButton("导入书籍 PDF"); import_btn.setObjectName("SecondaryMode"); import_btn.clicked.connect(self.import_pdf)
        left.addWidget(self.file_label); left.addWidget(import_btn)
        form = QFormLayout()
        self.total_pages = QSpinBox(); self.total_pages.setRange(1, 100000); self.total_pages.setValue(32)
        self.signature_pages = QComboBox(); self.signature_pages.addItems(["4", "8", "12", "16", "20", "24", "32"]); self.signature_pages.setCurrentText("16")
        self.binding = QComboBox(); self.binding.addItems(["骑马订", "胶装 / 锁线分帖"])
        self.flip = QComboBox(); self.flip.addItems(["长边翻", "短边翻", "天地翻"])
        self.sheet_w = _spin(450, 20, 3000, 1, " mm"); self.sheet_h = _spin(320, 20, 3000, 1, " mm")
        self.spine = _spin(0, 0, 200, 2, " mm"); self.creep = _spin(.10, 0, 10, 3, " mm/张")
        self.fold_lines = QCheckBox("显示折手线"); self.fold_lines.setChecked(True)
        for label, widget in (("总页数", self.total_pages), ("每帖页数", self.signature_pages), ("装订方式", self.binding), ("翻页方式", self.flip), ("纸张宽度", self.sheet_w), ("纸张高度", self.sheet_h), ("书脊宽度", self.spine), ("爬移补偿", self.creep), ("", self.fold_lines)):
            form.addRow(label, widget)
        left.addLayout(form)
        calc = QPushButton("计算书籍拼版"); calc.setObjectName("PrimaryMode"); calc.clicked.connect(self.calculate); left.addWidget(calc)
        export = QPushButton("导出折手页序 JSON"); export.setObjectName("SecondaryMode"); export.clicked.connect(self.export_json); left.addWidget(export)
        self.summary = QLabel(); self.summary.setWordWrap(True); self.summary.setStyleSheet("color:#536176;background:#f5f8fc;padding:8px;border-radius:5px;"); left.addWidget(self.summary)
        left.addStretch(); split.addWidget(controls)

        center = QFrame(); center.setObjectName("ModePanel"); center_l = QVBoxLayout(center); center_l.setContentsMargins(12, 12, 12, 12)
        nav = QHBoxLayout(); nav.addWidget(QLabel("正背面大版预览")); nav.addStretch(); nav.addWidget(QLabel("帖 / 张"))
        self.sheet_select = QComboBox(); self.sheet_select.currentIndexChanged.connect(self.refresh_preview); nav.addWidget(self.sheet_select); center_l.addLayout(nav)
        self.preview = BookSheetPreview(); center_l.addWidget(self.preview, 1)
        self.table = QTableWidget(0, 7); self.table.setHorizontalHeaderLabels(["帖", "张", "面", "左页", "右页", "爬移 mm", "翻页"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.table.setMaximumHeight(230); center_l.addWidget(self.table)
        split.addWidget(center); split.setStretchFactor(1, 1); split.setSizes([310, 900])
        self.calculate()

    def import_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入书籍 PDF", "", "PDF (*.pdf)")
        if not path: return
        try:
            from pypdf import PdfReader
            count = len(PdfReader(path).pages)
            self.source_path = path; self.file_label.setText(Path(path).name); self.total_pages.setValue(count); self.calculate()
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", str(exc))

    def calculate(self):
        pages = self.total_pages.value(); creep = self.creep.value()
        try:
            if self.binding.currentText() == "骑马订": sections = [saddle_stitch(pages, creep)]
            else: sections = perfect_bound_sections(pages, int(self.signature_pages.currentText()), creep)
        except Exception as exc:
            QMessageBox.warning(self, "书籍拼版", str(exc)); return
        self.plan = [spread for section in sections for spread in section]
        self.table.setRowCount(0)
        for spread in self.plan:
            row = self.table.rowCount(); self.table.insertRow(row)
            values = [spread.signature, spread.sheet, "正面" if spread.side == "front" else "背面", spread.left or "空白", spread.right or "空白", f"{spread.creep_mm:.3f}", self.flip.currentText()]
            for col, value in enumerate(values): self.table.setItem(row, col, QTableWidgetItem(str(value)))
        keys = []
        for spread in self.plan:
            key = (spread.signature, spread.sheet)
            if key not in keys: keys.append(key)
        self.sheet_select.blockSignals(True); self.sheet_select.clear()
        for signature, sheet in keys: self.sheet_select.addItem(f"第 {signature} 帖 / 第 {sheet} 张", (signature, sheet))
        self.sheet_select.blockSignals(False)
        padded = sum(1 for spread in self.plan for page in (spread.left, spread.right) if page is None)
        self.summary.setText(f"共 {len(sections)} 帖 · {len(keys)} 张物理纸 · {len(self.plan)} 个正背版 · 补白 {padded} 页")
        self.refresh_preview()

    def refresh_preview(self, *_):
        key = self.sheet_select.currentData()
        front = back = None
        if key:
            for spread in self.plan:
                if (spread.signature, spread.sheet) == tuple(key):
                    if spread.side == "front": front = spread
                    else: back = spread
        self.preview.set_spreads(front, back, self.sheet_w.value(), self.sheet_h.value(), self.spine.value(), self.fold_lines.isChecked(), self.flip.currentText())

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出折手页序", "书籍折手页序.json", "JSON (*.json)")
        if not path: return
        payload = {"source": self.source_path, "total_pages": self.total_pages.value(), "signature_pages": int(self.signature_pages.currentText()), "binding": self.binding.currentText(), "flip": self.flip.currentText(), "spine_mm": self.spine.value(), "creep_per_sheet_mm": self.creep.value(), "spreads": [x.to_dict() for x in self.plan]}
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_points(points):
    if len(points) < 3: raise ValueError("刀模轮廓至少需要 3 个点")
    min_x = min(x for x, _ in points); min_y = min(y for _, y in points)
    return [(float(x-min_x), float(y-min_y)) for x, y in points]


def load_die_contour(path):
    source = Path(path); suffix = source.suffix.lower()
    if suffix == ".json":
        data = json.loads(source.read_text(encoding="utf-8")); raw = data.get("points", data)
        return _normalize_points([(float(p[0]), float(p[1])) for p in raw])
    if suffix == ".svg":
        root = ElementTree.parse(source).getroot()
        for node in root.iter():
            if node.tag.lower().endswith(("polygon", "polyline")) and node.get("points"):
                nums = [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)", node.get("points"))]
                return _normalize_points(list(zip(nums[0::2], nums[1::2])))
        raise ValueError("SVG 中未找到 polygon/polyline 刀模轮廓")
    if suffix == ".dxf":
        lines = source.read_text(encoding="utf-8", errors="ignore").splitlines(); xs, ys = [], []
        for i in range(0, len(lines)-1, 2):
            code = lines[i].strip(); value = lines[i+1].strip()
            try:
                if code == "10": xs.append(float(value))
                elif code == "20": ys.append(float(value))
            except ValueError: pass
        return _normalize_points(list(zip(xs, ys)))
    if suffix == ".pdf":
        import fitz
        from shapely.geometry import MultiPoint
        doc = fitz.open(path); page = doc[0]; points = []
        for drawing in page.get_drawings():
            for item in drawing.get("items", []):
                for obj in item[1:]:
                    if hasattr(obj, "x") and hasattr(obj, "y"): points.append((obj.x*25.4/72, obj.y*25.4/72))
                    elif hasattr(obj, "x0"): points.extend([(obj.x0*25.4/72, obj.y0*25.4/72), (obj.x1*25.4/72, obj.y1*25.4/72)])
        if len(points) >= 3:
            hull = MultiPoint(points).convex_hull
            if hull.geom_type == "Polygon": return _normalize_points(list(hull.exterior.coords)[:-1])
        rect = page.rect; return [(0,0), (rect.width*25.4/72,0), (rect.width*25.4/72,rect.height*25.4/72), (0,rect.height*25.4/72)]
    raise ValueError("支持 PDF、SVG、DXF 或 points JSON 刀模")


class DieNestPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setMinimumSize(620, 460)
        self.points, self.plan = [], None; self.sheet_w, self.sheet_h = 650., 450.; self.bleed = 3.; self.sheet_no = 1

    def set_plan(self, points, plan, sheet_w, sheet_h, bleed, sheet_no=1):
        self.points, self.plan = points, plan; self.sheet_w, self.sheet_h = float(sheet_w), float(sheet_h); self.bleed = float(bleed); self.sheet_no = int(sheet_no); self.update()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing); painter.fillRect(self.rect(), QColor("#eef2f7"))
        margin = 35.; scale = min((self.width()-2*margin)/max(1.,self.sheet_w), (self.height()-2*margin)/max(1.,self.sheet_h))
        origin = QPointF((self.width()-self.sheet_w*scale)/2, (self.height()-self.sheet_h*scale)/2)
        sheet = QRectF(origin.x(), origin.y(), self.sheet_w*scale, self.sheet_h*scale)
        painter.setBrush(QColor("white")); painter.setPen(QPen(QColor("#1769df"),2)); painter.drawRect(sheet)
        if not self.plan: return
        for placement in self.plan.placements:
            if placement.sheet != self.sheet_no: continue
            angle = placement.rotation % 360; transformed=[]
            for x,y in self.points:
                if angle == 90: rx,ry = -y,x
                elif angle == 180: rx,ry = -x,-y
                elif angle == 270: rx,ry = y,-x
                else: rx,ry = x,y
                transformed.append((rx,ry))
            minx=min(x for x,_ in transformed); miny=min(y for _,y in transformed)
            poly = QPolygonF([QPointF(origin.x()+(placement.x_mm+x-minx)*scale, origin.y()+(placement.y_mm+y-miny)*scale) for x,y in transformed])
            if self.bleed > 0:
                painter.setPen(QPen(QColor(238,86,164,110), max(1., self.bleed*2*scale), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)); painter.setBrush(Qt.NoBrush); painter.drawPolygon(poly)
            painter.setPen(QPen(QColor("#d81b60"),1.3)); painter.setBrush(QColor(23,105,223,28)); painter.drawPolygon(poly)
            painter.setPen(QColor("#1c3150")); painter.drawText(poly.boundingRect(), Qt.AlignCenter, str(placement.copy_index+1))


class BoxImpositionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.points=[]; self.plan=None; self.source_path=""
        root=QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(1); split=QSplitter(Qt.Horizontal); root.addWidget(split)
        controls=QFrame(); controls.setObjectName("ModePanel"); controls.setMinimumWidth(280); controls.setMaximumWidth(350)
        left=QVBoxLayout(controls); left.setContentsMargins(16,14,16,14); title=QLabel("盒型拼版"); title.setObjectName("ModeTitle"); left.addWidget(title)
        self.file_label=QLineEdit(); self.file_label.setReadOnly(True); self.file_label.setPlaceholderText("尚未导入刀模")
        import_btn=QPushButton("导入刀模 PDF / SVG / DXF / JSON"); import_btn.setObjectName("SecondaryMode"); import_btn.clicked.connect(self.import_die)
        left.addWidget(self.file_label); left.addWidget(import_btn)
        form=QFormLayout(); self.quantity=QSpinBox(); self.quantity.setRange(1,10000); self.quantity.setValue(12)
        self.sheet_w=_spin(650,20,3000,1," mm"); self.sheet_h=_spin(450,20,3000,1," mm"); self.gap=_spin(3,0,100,1," mm"); self.bleed=_spin(3,0,50,1," mm"); self.step=_spin(2,.5,20,1," mm")
        self.rotations=QComboBox(); self.rotations.addItems(["0° / 90° / 180° / 270°", "仅 0° / 180°", "仅 0°"])
        self.spot=QLineEdit("CutContour"); self.spot.setPlaceholderText("刀线专色名称")
        for label,w in (("数量",self.quantity),("纸张宽度",self.sheet_w),("纸张高度",self.sheet_h),("轮廓间距",self.gap),("出血",self.bleed),("搜索步长",self.step),("允许旋转",self.rotations),("刀线专色",self.spot)): form.addRow(label,w)
        left.addLayout(form); calc=QPushButton("执行异形套料"); calc.setObjectName("PrimaryMode"); calc.clicked.connect(self.calculate); left.addWidget(calc)
        export=QPushButton("导出套料方案 JSON"); export.setObjectName("SecondaryMode"); export.clicked.connect(self.export_json); left.addWidget(export)
        self.summary=QLabel("导入刀模后计算"); self.summary.setWordWrap(True); self.summary.setStyleSheet("color:#536176;background:#f5f8fc;padding:8px;border-radius:5px;"); left.addWidget(self.summary); left.addStretch(); split.addWidget(controls)
        center=QFrame(); center.setObjectName("ModePanel"); cl=QVBoxLayout(center); cl.setContentsMargins(12,12,12,12)
        nav=QHBoxLayout(); nav.addWidget(QLabel("盒型刀模与异形套料预览")); nav.addStretch(); nav.addWidget(QLabel("大版")); self.sheet_select=QComboBox(); self.sheet_select.currentIndexChanged.connect(self.refresh_preview); nav.addWidget(self.sheet_select); cl.addLayout(nav)
        self.preview=DieNestPreview(); cl.addWidget(self.preview,1); split.addWidget(center); split.setStretchFactor(1,1); split.setSizes([310,900])

    def import_die(self):
        path,_=QFileDialog.getOpenFileName(self,"导入盒型刀模","","刀模 (*.pdf *.svg *.dxf *.json)")
        if not path:return
        try:
            self.points=load_die_contour(path); self.source_path=path; self.file_label.setText(Path(path).name); self.calculate()
        except Exception as exc: QMessageBox.critical(self,"刀模导入失败",str(exc))

    def calculate(self):
        if not self.points: QMessageBox.information(self,"异形套料","请先导入刀模轮廓。"); return
        choices=((0,90,180,270),(0,180),(0,)); rotations=choices[self.rotations.currentIndex()]
        try:
            item=NestItem(Path(self.source_path).stem or "box",self.points,self.quantity.value(),rotations)
            self.plan=nest_polygons_multi_sheet([item],self.sheet_w.value(),self.sheet_h.value(),self.gap.value()+self.bleed.value()*2,self.step.value())
        except Exception as exc: QMessageBox.warning(self,"套料失败",str(exc)); return
        self.sheet_select.blockSignals(True); self.sheet_select.clear()
        for number in range(1,self.plan.sheet_count+1): self.sheet_select.addItem(f"第 {number} 张",number)
        self.sheet_select.blockSignals(False)
        average=sum(self.plan.utilization)/max(1,len(self.plan.utilization))*100
        self.summary.setText(f"{len(self.plan.placements)} 个盒型 · {self.plan.sheet_count} 张大版 · 平均轮廓利用率 {average:.1f}% · 刀线专色 {self.spot.text().strip() or 'CutContour'}")
        self.refresh_preview()

    def refresh_preview(self,*_):
        self.preview.set_plan(self.points,self.plan,self.sheet_w.value(),self.sheet_h.value(),self.bleed.value(),self.sheet_select.currentData() or 1)

    def export_json(self):
        if not self.plan: QMessageBox.information(self,"导出套料","请先完成异形套料。"); return
        path,_=QFileDialog.getSaveFileName(self,"导出套料方案","盒型套料方案.json","JSON (*.json)")
        if not path:return
        payload={"source":self.source_path,"spot_color":self.spot.text().strip() or "CutContour","bleed_mm":self.bleed.value(),"sheet":{"width_mm":self.sheet_w.value(),"height_mm":self.sheet_h.value()},"contour":self.points,"sheet_count":self.plan.sheet_count,"utilization":self.plan.utilization,"placements":[vars(x) for x in self.plan.placements]}
        Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")


class ProductionModeWorkspace(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("ImpositionWorkspace"); self.setStyleSheet(MODE_STYLE); self.production_host=None
        root=QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        bar=QFrame(); bar.setObjectName("ModeBar"); row=QHBoxLayout(bar); row.setContentsMargins(10,6,10,6)
        brand=QLabel("智印拼版"); brand.setObjectName("ModeBrand"); row.addWidget(brand)
        self.mode_buttons=[]; group=QButtonGroup(self); group.setExclusive(True)
        self.stack=QStackedWidget()
        self.single_page=ProfessionalPageCanvasWidget(self); self.book=BookImpositionWidget(self); self.box=BoxImpositionWidget(self)
        for index,(text,widget) in enumerate((("单页拼版",self.single_page),("书籍拼版",self.book),("盒型拼版",self.box))):
            button=QPushButton(text); button.setObjectName("ModeButton"); button.setCheckable(True); button.setChecked(index==0); button.clicked.connect(lambda checked=False,i=index:self.stack.setCurrentIndex(i)); group.addButton(button); row.addWidget(button); self.mode_buttons.append(button); self.stack.addWidget(widget)
        row.addStretch(); self.mode_hint=QLabel("生产模式"); self.mode_hint.setStyleSheet("color:#9fb2ca;padding-right:12px;"); row.addWidget(self.mode_hint)
        root.addWidget(bar); root.addWidget(self.stack,1)

    def bind_production_host(self, host): self.production_host=host; self.single_page.bind_production_host(host)
    def _sync_host_parameters(self): self.single_page._sync_host_parameters()

