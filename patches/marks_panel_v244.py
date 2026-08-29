from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem,
    QGraphicsView, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from print_marks import MarkConfig, JobMarkInfo, crop_segments, registration_centers, color_bar_rects, gripper_arrow, info_lines


class PrintMarksPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QHBoxLayout(self)
        controls = QWidget(); form = QFormLayout(controls)

        self.crop = QCheckBox(); self.crop.setChecked(True)
        self.register = QCheckBox(); self.register.setChecked(True)
        self.colorbar = QCheckBox(); self.colorbar.setChecked(True)
        self.filename = QCheckBox(); self.filename.setChecked(True)
        self.plate = QCheckBox(); self.plate.setChecked(True)
        self.date = QCheckBox(); self.date.setChecked(True)
        self.side = QCheckBox(); self.side.setChecked(True)
        self.gripper = QCheckBox(); self.gripper.setChecked(True)
        for label, w in [('裁切线',self.crop),('套准十字',self.register),('CMYK 色标',self.colorbar),('文件名',self.filename),('版号',self.plate),('日期',self.date),('正反面标识',self.side),('咬口方向',self.gripper)]:
            form.addRow(label,w)

        self.length = QDoubleSpinBox(); self.length.setRange(1,30); self.length.setValue(5); self.length.setSuffix(' mm')
        self.offset = QDoubleSpinBox(); self.offset.setRange(0,20); self.offset.setValue(2); self.offset.setSuffix(' mm')
        self.width = QDoubleSpinBox(); self.width.setRange(0.1,3); self.width.setDecimals(2); self.width.setValue(0.25); self.width.setSuffix(' pt')
        self.radius = QDoubleSpinBox(); self.radius.setRange(1,15); self.radius.setValue(3); self.radius.setSuffix(' mm')
        self.textsize = QDoubleSpinBox(); self.textsize.setRange(4,24); self.textsize.setValue(7); self.textsize.setSuffix(' pt')
        self.edge = QComboBox(); self.edge.addItems(['top','bottom','left','right'])
        self.file = QLineEdit('job.pdf'); self.plate_no = QLineEdit('A01'); self.side_text = QComboBox(); self.side_text.addItems(['FRONT','BACK'])
        for label,w in [('裁切线长度',self.length),('裁切线偏移',self.offset),('裁切线粗细',self.width),('套准圈半径',self.radius),('文字大小',self.textsize),('咬口边',self.edge),('文件名文字',self.file),('版号',self.plate_no),('面别',self.side_text)]: form.addRow(label,w)

        btn = QPushButton('刷新标记预览'); btn.clicked.connect(self.refresh_preview); form.addRow(btn)
        note = QLabel('预览按 650 × 450 mm 纸张和示例成品框显示。生产标记底层为矢量 PDF 绘制，不依赖画布截图。'); note.setWordWrap(True); form.addRow(note)
        root.addWidget(controls)

        self.scene = QGraphicsScene(); self.view = QGraphicsView(self.scene); self.view.setRenderHint(self.view.renderHints() | 1)
        root.addWidget(self.view,1)
        self.refresh_preview()

    def config(self):
        return MarkConfig(
            crop_marks=self.crop.isChecked(), register_marks=self.register.isChecked(), color_bar=self.colorbar.isChecked(),
            file_name=self.filename.isChecked(), plate_no=self.plate.isChecked(), date=self.date.isChecked(), side_label=self.side.isChecked(),
            gripper_arrow=self.gripper.isChecked(), crop_length_mm=self.length.value(), crop_offset_mm=self.offset.value(), crop_width_pt=self.width.value(),
            register_radius_mm=self.radius.value(), text_size_pt=self.textsize.value(), gripper_edge=self.edge.currentText(),
        )

    def refresh_preview(self):
        cfg = self.config(); self.scene.clear(); sw, sh = 650.0, 450.0
        sheet = self.scene.addRect(0,0,sw,sh,QPen(QColor('#555'),1),QBrush(QColor('#f7f7f7'))); sheet.setZValue(-20)
        boxes = [(50,60,160,100),(250,60,160,100),(50,210,160,100),(250,210,160,100)]
        for x,y,w,h in boxes:
            self.scene.addRect(x,y,w,h,QPen(QColor('#3777c2'),0.7))
            if cfg.crop_marks:
                for a,b in crop_segments(x,y,w,h,cfg): self.scene.addLine(a[0],a[1],b[0],b[1],QPen(Qt.black,max(.2,cfg.crop_width_pt)))
        if cfg.register_marks:
            r=cfg.register_radius_mm
            for cx,cy in registration_centers(sw,sh,cfg):
                self.scene.addEllipse(cx-r,cy-r,2*r,2*r,QPen(Qt.black,.4)); self.scene.addLine(cx-r*1.5,cy,cx+r*1.5,cy,QPen(Qt.black,.3)); self.scene.addLine(cx,cy-r*1.5,cx,cy+r*1.5,QPen(Qt.black,.3))
        if cfg.color_bar:
            colors={'C':QColor('cyan'),'M':QColor('magenta'),'Y':QColor('yellow'),'K':QColor('black')}
            for x,y,w,h,name in color_bar_rects(sw,sh,cfg): self.scene.addRect(x,y,w,h,QPen(Qt.black,.2),QBrush(colors[name]))
        info=JobMarkInfo(file_name=self.file.text(),plate_no=self.plate_no.text(),side=self.side_text.currentText())
        y=20
        for text in info_lines(info,cfg):
            t=QGraphicsSimpleTextItem(text); t.setPos(15,y); self.scene.addItem(t); y+=13
        if cfg.gripper_arrow:
            pts=gripper_arrow(sw,sh,cfg)
            for i in range(3):
                a,b=pts[i],pts[(i+1)%3]; self.scene.addLine(a[0],a[1],b[0],b[1],QPen(Qt.black,.5))
        self.scene.setSceneRect(-20,-20,sw+40,sh+40); self.view.fitInView(self.scene.sceneRect(),Qt.KeepAspectRatio)
