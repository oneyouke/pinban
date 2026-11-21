# -*- coding: utf-8 -*-
"""Desktop Imposer Pro V3.0 - UI prototype.
Run: python v3/run_ui.py
Requires: PySide6, PyMuPDF
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDockWidget, QFrame, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFormLayout, QLabel, QPushButton, QToolButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QTabWidget,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QScrollArea,
    QSplitter, QSlider, QSizePolicy, QGroupBox, QStatusBar
)

BG = "#242629"
PANEL = "#2c2f33"
PANEL2 = "#33373c"
BORDER = "#454a50"
TEXT = "#e5e7eb"
MUTED = "#a5abb3"
BLUE = "#2878d0"
PURPLE = "#c45bd5"
GREEN = "#28b46b"


@dataclass
class Job:
    file_path: str = ""
    page_count: int = 32
    page_width: float = 210.0
    page_height: float = 285.0
    sheet_width: float = 890.0
    sheet_height: float = 630.0
    across: int = 2
    down: int = 4
    gap_x: float = 10.0
    gap_y: float = 10.0
    bleed: float = 3.0
    margin: float = 15.0
    zoom: float = 0.72
    show_crop: bool = True
    show_registration: bool = True
    show_colorbar: bool = True
    show_info: bool = True


class SheetCanvas(QWidget):
    def __init__(self, job: Job, parent=None):
        super().__init__(parent)
        self.job = job
        self.setMinimumSize(520, 440)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#202225"))
        j = self.job
        pad = 36
        avail_w, avail_h = self.width() - 2 * pad, self.height() - 2 * pad
        scale = min(avail_w / max(j.sheet_width, 1), avail_h / max(j.sheet_height, 1)) * j.zoom
        sw, sh = j.sheet_width * scale, j.sheet_height * scale
        sx, sy = (self.width() - sw) / 2, (self.height() - sh) / 2
        sheet = QRectF(sx, sy, sw, sh)

        p.setPen(QPen(QColor("#08090a"), 1))
        p.setBrush(QColor("#f6f6f3"))
        p.drawRect(sheet)

        cols, rows = max(1, j.across), max(1, j.down)
        usable_w = j.sheet_width - 2 * j.margin - (cols - 1) * j.gap_x
        usable_h = j.sheet_height - 2 * j.margin - (rows - 1) * j.gap_y
        cell_w, cell_h = usable_w / cols, usable_h / rows
        page_w, page_h = j.page_width + 2*j.bleed, j.page_height + 2*j.bleed
        fit = min(cell_w / max(page_w, 1), cell_h / max(page_h, 1), 1.0)
        draw_w, draw_h = page_w * fit * scale, page_h * fit * scale
        trim_w, trim_h = j.page_width * fit * scale, j.page_height * fit * scale

        p.setPen(QPen(QColor("#aeb5bd"), 0.7, Qt.DashLine))
        p.setBrush(Qt.NoBrush)
        p.drawRect(sheet.adjusted(j.margin*scale, j.margin*scale, -j.margin*scale, -j.margin*scale))

        n = 1
        for r in range(rows):
            for c in range(cols):
                cx = sx + (j.margin + c*(cell_w+j.gap_x) + cell_w/2) * scale
                cy = sy + (j.margin + r*(cell_h+j.gap_y) + cell_h/2) * scale
                bleed_rect = QRectF(cx-draw_w/2, cy-draw_h/2, draw_w, draw_h)
                trim_rect = QRectF(cx-trim_w/2, cy-trim_h/2, trim_w, trim_h)
                p.setPen(QPen(QColor("#c9d1d9"), 0.6))
                p.setBrush(QColor("#ffffff"))
                p.drawRect(bleed_rect)
                p.setPen(QPen(QColor("#d5d9df"), 0.6))
                p.setBrush(QColor("#fdfdfc"))
                p.drawRect(trim_rect)
                p.setPen(QPen(QColor("#8a929b"), 0.6))
                p.setFont(QFont("Microsoft YaHei", max(6, int(8*scale))))
                p.drawText(trim_rect, Qt.AlignCenter, str(n))
                if j.show_crop:
                    self.draw_crop_marks(p, trim_rect, max(4, 5*scale))
                n += 1

        if j.show_registration:
            self.draw_registration(p, sx + sw/2, sy + 8*scale, max(4, 5*scale))
            self.draw_registration(p, sx + sw/2, sy + sh - 8*scale, max(4, 5*scale))
        if j.show_colorbar:
            self.draw_colorbar(p, sx + sw/2 - 42*scale, sy + sh - 3*scale, scale)
        if j.show_info:
            p.setPen(QColor("#22272b"))
            p.setFont(QFont("Arial", max(6, int(7*scale))))
            p.drawText(QRectF(sx+5, sy+3, sw-10, 12), Qt.AlignRight, "IMPOSER PRO  |  PREVIEW")
        p.end()

    @staticmethod
    def draw_crop_marks(p, rect, length):
        pen = QPen(QColor("#222222"), 0.8)
        p.setPen(pen)
        x1, y1, x2, y2 = rect.left(), rect.top(), rect.right(), rect.bottom()
        for x, y, dx, dy in [
            (x1,y1,-1,-1),(x2,y1,1,-1),(x1,y2,-1,1),(x2,y2,1,1)
        ]:
            p.drawLine(QRectF(x+dx*length, y, length, 0).toRect().topLeft(),
                       QRectF(x, y+dy*length, 0, length).toRect().bottomRight())

    @staticmethod
    def draw_registration(p, x, y, radius):
        p.setPen(QPen(QColor("#161616"), 0.8))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(x-radius, y-radius, radius*2, radius*2))
        p.drawLine(int(x-radius*1.5), int(y), int(x+radius*1.5), int(y))
        p.drawLine(int(x), int(y-radius*1.5), int(x), int(y+radius*1.5))

    @staticmethod
    def draw_colorbar(p, x, y, scale):
        colors = ["#00a5df", "#ec008c", "#fff200", "#231f20", "#777777"]
        w = max(5, 12*scale)
        for i, color in enumerate(colors):
            p.fillRect(QRectF(x+i*(w+1), y, w, max(2, 3*scale)), QColor(color))


class UnitSpin(QDoubleSpinBox):
    def __init__(self, value=0, suffix=" mm", minimum=0, maximum=2000):
        super().__init__()
        self.setRange(minimum, maximum)
        self.setDecimals(1)
        self.setSingleStep(1)
        self.setValue(value)
        self.setSuffix(suffix)
        self.setFixedHeight(28)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Desktop Imposer Pro V3.0 — 云游客专业拼版")
        self.resize(1500, 960)
        self.job = Job()
        self._build_menu()
        self._build_toolbar()
        self._build_navigation()
        self._build_control_dock()
        self._build_pages_dock()
        self._build_inspector()
        self._build_workspace()
        self._build_status()
        self._apply_style()
        self.refresh_preview()

    def _build_menu(self):
        bar = self.menuBar()
        for name in ["文件(F)", "编辑(E)", "视图(V)", "工具(T)", "书册(B)", "窗口(W)", "帮助(H)"]:
            bar.addMenu(name)
        file_menu = bar.actions()[0].menu()
        open_action = QAction("打开 PDF...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_pdf)
        file_menu.addAction(open_action)

    def _build_toolbar(self):
        tb = self.addToolBar("主工具栏")
        tb.setMovable(False)
        for text, slot in [("打开", self.open_pdf), ("保存方案", self.save_job),
                           ("撤销", self.not_implemented), ("重做", self.not_implemented),
                           ("设置", self.not_implemented)]:
            a = QAction(text, self)
            a.triggered.connect(slot)
            tb.addAction(a)
        tb.addSeparator()
        self.job_name = QLineEdit("32P_宣传册拼版")
        self.job_name.setMaximumWidth(230)
        tb.addWidget(QLabel("  工作单："))
        tb.addWidget(self.job_name)
        tb.addSeparator()
        impose = QAction("▶  拼版", self)
        impose.triggered.connect(self.refresh_preview)
        tb.addAction(impose)
        tb.addSeparator()
        tb.addWidget(QLabel("  配置信息："))
        profile = QComboBox()
        profile.addItems(["自定义 210×285mm", "A4 210×297mm", "A3 297×420mm", "对开 889×1194mm"])
        profile.currentIndexChanged.connect(self.apply_profile)
        tb.addWidget(profile)

    def _build_navigation(self):
        dock = QDockWidget("功能导航", self)
        dock.setObjectName("NavigationDock")
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        nav = QWidget()
        nav.setFixedWidth(64)
        lay = QVBoxLayout(nav)
        lay.setContentsMargins(5, 8, 5, 8)
        lay.setSpacing(5)
        self.nav_buttons = []
        entries = [("▦", "基本"), ("⚒", "工具"), ("▤", "页面"), ("A", "标记"),
                   ("▧", "图像"), ("⚙", "处理"), ("◉", "印前"), ("▣", "变量数据")]
        for symbol, label in entries:
            b = QToolButton()
            b.setText(symbol + "\n" + label)
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            b.setMinimumHeight(58)
            b.setCheckable(True)
            b.clicked.connect(lambda checked=False, text=label: self.select_nav(text))
            lay.addWidget(b)
            self.nav_buttons.append(b)
        self.nav_buttons[0].setChecked(True)
        lay.addStretch()
        dock.setWidget(nav)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.nav_dock = dock

    def _build_control_dock(self):
        self.control_dock = QDockWidget("控制面板", self)
        self.control_dock.setObjectName("ControlDock")
        self.control_tabs = QTabWidget()
        self.control_tabs.addTab(self._basic_panel(), "基本")
        self.control_tabs.addTab(self._booklet_panel(), "书册")
        self.control_tabs.addTab(self._layout_panel(), "版面")
        self.control_tabs.addTab(self._appearance_panel(), "外观")
        self.control_dock.setWidget(self.control_tabs)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.control_dock)
        self.control_dock.setMinimumWidth(270)

    def _field(self, label, widget):
        row = QHBoxLayout()
        lab = QLabel(label)
        lab.setMinimumWidth(82)
        row.addWidget(lab)
        row.addWidget(widget, 1)
        return row

    def _basic_panel(self):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(12,12,12,12); v.setSpacing(9)
        self.page_size = QComboBox(); self.page_size.addItems(["自定义", "A4 210×297", "A5 148×210", "210×285"])
        self.sheet_size = QComboBox(); self.sheet_size.addItems(["自定义 890×630", "对开 889×1194", "全开 1194×889", "A2 420×594", "A3 297×420"])
        self.orientation = QComboBox(); self.orientation.addItems(["横向", "纵向"])
        self.mode = QComboBox(); self.mode.addItems(["多页拼版", "重复拼版", "单页拼版", "手动拼版"])
        self.copies = QSpinBox(); self.copies.setRange(1, 128); self.copies.setValue(8)
        for lab, wid in [("页面尺寸：",self.page_size),("纸张尺寸：",self.sheet_size),
                         ("布局方向：",self.orientation),("拼版类型：",self.mode),("每张纸拼版数：",self.copies)]:
            v.addLayout(self._field(lab,wid))
        v.addWidget(self._section("间距"))
        self.gap_x = UnitSpin(10); self.gap_y = UnitSpin(10)
        v.addLayout(self._field("水平间距：",self.gap_x)); v.addLayout(self._field("垂直间距：",self.gap_y))
        v.addWidget(self._section("边距 / 咬口"))
        self.margin_top = UnitSpin(15); self.margin_bottom = UnitSpin(15)
        self.margin_left = UnitSpin(15); self.margin_right = UnitSpin(15)
        for lab,wid in [("上边距：",self.margin_top),("下边距：",self.margin_bottom),
                        ("左边距：",self.margin_left),("右边距：",self.margin_right)]:
            v.addLayout(self._field(lab,wid))
        self.bleed = UnitSpin(3)
        v.addLayout(self._field("出血：",self.bleed))
        adjust = QPushButton("调整尺寸到纸张")
        adjust.clicked.connect(self.fit_to_sheet)
        v.addWidget(adjust)
        v.addStretch()
        return w

    def _booklet_panel(self):
        w=QWidget(); v=QVBoxLayout(w); v.setContentsMargins(12,12,12,12)
        mode=QComboBox(); mode.addItems(["骑马钉", "胶装 / 书刊", "锁线装", "自定义折手"])
        bind=QComboBox(); bind.addItems(["左侧装订", "右侧装订", "上侧装订"])
        sig=QComboBox(); sig.addItems(["8 页折手", "16 页折手", "32 页折手", "自动"])
        flip=QComboBox(); flip.addItems(["长边翻转", "短边翻转", "自翻版", "天地翻"])
        creep=UnitSpin(0, minimum=-20, maximum=20)
        for lab, wid in [("装订方式：",mode),("装订边：",bind),("折手页数：",sig),("正反面：",flip),("爬移补偿：",creep)]:
            v.addLayout(self._field(lab,wid))
        v.addWidget(QLabel("书刊页序与双面映射将在选择 PDF 后生成预览。"))
        v.addStretch()
        return w

    def _layout_panel(self):
        w=QWidget(); v=QVBoxLayout(w); v.setContentsMargins(12,12,12,12)
        self.rows=QSpinBox(); self.rows.setRange(1,32); self.rows.setValue(4)
        self.cols=QSpinBox(); self.cols.setRange(1,32); self.cols.setValue(2)
        rotate=QComboBox(); rotate.addItems(["不旋转", "自动旋转", "顺时针 90°", "180°", "逆时针 90°"])
        scale=QComboBox(); scale.addItems(["实际尺寸", "适合页面", "填满版面"])
        order=QComboBox(); order.addItems(["从左到右、从上到下", "从上到下、从左到右", "蛇形排列"])
        for lab,wid in [("行数：",self.rows),("列数：",self.cols),("旋转：",rotate),("缩放：",scale),("页面顺序：",order)]:
            v.addLayout(self._field(lab,wid))
        v.addStretch()
        return w

    def _appearance_panel(self):
        w=QWidget(); v=QVBoxLayout(w); v.setContentsMargins(12,12,12,12)
        self.cb_crop=QCheckBox("裁切标记"); self.cb_crop.setChecked(True)
        self.cb_reg=QCheckBox("套准标记"); self.cb_reg.setChecked(True)
        self.cb_bar=QCheckBox("颜色条"); self.cb_bar.setChecked(True)
        self.cb_info=QCheckBox("页面信息"); self.cb_info.setChecked(True)
        for cb in [self.cb_crop,self.cb_reg,self.cb_bar,self.cb_info]:
            cb.stateChanged.connect(self.refresh_preview); v.addWidget(cb)
        v.addWidget(QLabel("标记颜色："))
        color=QComboBox(); color.addItems(["黑色", "专色 / Registration", "自定义"])
        v.addWidget(color); v.addStretch()
        return w

    def _section(self, text):
        lab=QLabel(text); lab.setStyleSheet("font-weight:600;color:#dfe4ea;border-bottom:1px solid #4b5158;padding:8px 0 5px 0;")
        return lab

    def _build_pages_dock(self):
        self.pages_dock=QDockWidget("页面列表",self)
        self.pages_dock.setObjectName("PagesDock")
        box=QWidget(); v=QVBoxLayout(box); v.setContentsMargins(7,7,7,7)
        self.search=QLineEdit(); self.search.setPlaceholderText("⌕  搜索页面 / 文件")
        self.page_list=QListWidget()
        for i in range(1,33):
            item=QListWidgetItem(f"  {i:02d}    PDF 页面 {i}")
            item.setSizeHint(QSize(180,30)); self.page_list.addItem(item)
        v.addWidget(self.search); v.addWidget(self.page_list)
        self.pages_dock.setWidget(box)
        self.addDockWidget(Qt.LeftDockWidgetArea,self.pages_dock)
        self.splitDockWidget(self.control_dock,self.pages_dock,Qt.Vertical)
        self.pages_dock.setMinimumHeight(170)

    def _build_inspector(self):
        self.inspector=QDockWidget("属性",self)
        self.inspector.setObjectName("InspectorDock")
        tabs=QTabWidget()
        prop=QWidget(); v=QVBoxLayout(prop); v.setContentsMargins(12,12,12,12)
        v.addWidget(self._section("文件信息"))
        self.file_label=QLabel("文件名：尚未打开\n页面数：32\n文件类型：PDF 文档")
        self.file_label.setWordWrap(True); v.addWidget(self.file_label)
        v.addWidget(self._section("页面尺寸"))
        self.width_field=UnitSpin(210); self.height_field=UnitSpin(285)
        v.addLayout(self._field("宽度：",self.width_field)); v.addLayout(self._field("高度：",self.height_field))
        v.addWidget(self._section("出血设置"))
        self.inspector_bleed=UnitSpin(3); v.addLayout(self._field("出血：",self.inspector_bleed))
        v.addWidget(self._section("标记设置"))
        for text in ["裁切标记", "套准标记", "颜色条", "页面信息"]:
            cb=QCheckBox(text); cb.setChecked(True); v.addWidget(cb)
        edit=QPushButton("编辑标记..."); v.addWidget(edit)
        v.addWidget(self._section("色彩管理"))
        rgb=QComboBox(); rgb.addItems(["sRGB IEC61966-2.1", "Adobe RGB"])
        cmyk=QComboBox(); cmyk.addItems(["ISO Coated v2 300%", "GRACoL 2013", "Japan Color 2011 Coated"])
        v.addLayout(self._field("RGB 配置文件：",rgb)); v.addLayout(self._field("CMYK 配置文件：",cmyk))
        embed=QCheckBox("使用嵌入配置文件（如果可用）"); embed.setChecked(True); v.addWidget(embed)
        v.addStretch()
        tabs.addTab(prop,"属性")
        layers=QListWidget(); layers.addItems(["☑ 页面内容", "☑ 出血区域", "☑ 裁切标记", "☑ 色标与套准"])
        tabs.addTab(layers,"层")
        self.inspector.setWidget(tabs); self.inspector.setMinimumWidth(280)
        self.addDockWidget(Qt.RightDockWidgetArea,self.inspector)

    def _build_workspace(self):
        center=QWidget(); v=QVBoxLayout(center); v.setContentsMargins(0,0,0,0); v.setSpacing(0)
        self.work_tabs=QTabWidget()
        preview=QWidget(); pv=QVBoxLayout(preview); pv.setContentsMargins(0,0,0,0); pv.setSpacing(0)
        tools=QHBoxLayout(); tools.setContentsMargins(10,6,10,6)
        for name in ["适合窗口", "实际大小", "−", "+", "手形平移", "单页视图", "拼版视图"]:
            b=QToolButton(); b.setText(name); b.clicked.connect(lambda checked=False, n=name:self.preview_action(n)); tools.addWidget(b)
        tools.addStretch()
        self.zoom_label=QLabel("72%"); tools.addWidget(self.zoom_label)
        pv.addLayout(tools)
        self.canvas=SheetCanvas(self.job); pv.addWidget(self.canvas,1)
        self.work_tabs.addTab(preview,"预览")
        pageview=QWidget(); pageview_l=QVBoxLayout(pageview); pageview_l.addWidget(QLabel("页面视图：选择左侧 PDF 页面查看页面内容与尺寸。"))
        self.work_tabs.addTab(pageview,"页面视图")
        templates=QWidget(); templates_l=QVBoxLayout(templates); templates_l.addWidget(QLabel("拼版模板库：常用纸张、书刊折手、标签及卡牌模板。"))
        self.work_tabs.addTab(templates,"拼版模板库")
        v.addWidget(self.work_tabs)
        self.setCentralWidget(center)

    def _build_status(self):
        status=QStatusBar(); self.setStatusBar(status)
        self.status_pages=QLabel("页面：32 / 32")
        self.status_sheet=QLabel("纸张：890 × 630 mm")
        self.status_count=QLabel("拼版：8")
        self.status_zoom=QLabel("缩放：72%")
        self.status_ready=QLabel("● 就绪"); self.status_ready.setStyleSheet("color:#32c875;font-weight:600")
        for w in [self.status_pages,self.status_sheet,self.status_count,self.status_zoom,self.status_ready]:
            status.addPermanentWidget(w)

    def _apply_style(self):
        self.setStyleSheet(f"""
        QMainWindow,QWidget {{ background:{BG}; color:{TEXT}; font-family:'Microsoft YaHei UI'; font-size:9pt; }}
        QMenuBar,QMenu,QToolBar {{ background:#292c30; color:{TEXT}; border:0; spacing:5px; }}
        QMenuBar::item:selected,QMenu::item:selected {{ background:#3b4148; }}
        QToolBar {{ border-bottom:1px solid {BORDER}; padding:5px; }}
        QDockWidget::title {{ background:#30343a; padding:8px; border-bottom:1px solid {BORDER}; }}
        QDockWidget {{ border:1px solid {BORDER}; }}
        QTabWidget::pane {{ border:1px solid {BORDER}; }}
        QTabBar::tab {{ background:#30343a; padding:8px 13px; border:1px solid {BORDER}; }}
        QTabBar::tab:selected {{ background:#39434f; border-bottom:2px solid {BLUE}; }}
        QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox {{ background:#202327; border:1px solid #515860; border-radius:3px; padding:4px; min-height:20px; }}
        QPushButton,QToolButton {{ background:#353a40; border:1px solid #4a5058; border-radius:3px; padding:5px 8px; }}
        QPushButton:hover,QToolButton:hover {{ background:#424a54; }}
        QToolButton:checked {{ background:#244d78; border:1px solid {BLUE}; }}
        QListWidget {{ background:#222529; border:0; }}
        QListWidget::item {{ border-bottom:1px solid #353a40; padding:4px; }}
        QListWidget::item:selected {{ background:#244d78; }}
        QStatusBar {{ background:#292c30; border-top:1px solid {BORDER}; }}
        QCheckBox {{ spacing:8px; }}
        QSplitter::handle {{ background:{BORDER}; }}
        """)
        self.setDockOptions(QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks | QMainWindow.AnimatedDocks)

    def select_nav(self, label):
        for b in self.nav_buttons:
            b.setChecked(label in b.text())
        mapping={"基本":0,"工具":1,"页面":0,"标记":3,"图像":3,"处理":2,"印前":3,"变量数据":2}
        self.control_tabs.setCurrentIndex(mapping.get(label,0))
        self.statusBar().showMessage(f"当前功能：{label}",2500)
        if label=="页面": self.pages_dock.show(); self.pages_dock.raise_()

    def open_pdf(self):
        path,_=QFileDialog.getOpenFileName(self,"打开印刷 PDF","","PDF 文件 (*.pdf)")
        if not path: return
        try:
            import fitz
            doc=fitz.open(path)
            count=len(doc)
            if count:
                rect=doc[0].rect
                pw,ph=rect.width*25.4/72,rect.height*25.4/72
                self.job.page_width=round(pw,1); self.job.page_height=round(ph,1)
            doc.close()
        except ImportError:
            QMessageBox.warning(self,"缺少 PDF 引擎","请安装 PyMuPDF：pip install PyMuPDF")
            return
        except Exception as exc:
            QMessageBox.critical(self,"PDF 打开失败",str(exc)); return
        self.job.file_path=path; self.job.page_count=count
        self.page_list.clear()
        for i in range(1,count+1):
            self.page_list.addItem(f"  {i:03d}    {os.path.basename(path)}")
        self.file_label.setText(f"文件名：{os.path.basename(path)}\n文件路径：{path}\n页面尺寸：{self.job.page_width:.1f} × {self.job.page_height:.1f} mm\n页面数：{count}\n文件类型：PDF 文档")
        self.width_field.setValue(self.job.page_width); self.height_field.setValue(self.job.page_height)
        self.status_pages.setText(f"页面：{count} / {count}")
        self.statusBar().showMessage(f"已载入：{path}",5000)
        self.refresh_preview()

    def refresh_preview(self, *_):
        j=self.job
        j.across=max(1,self.cols.value()) if hasattr(self,"cols") else j.across
        j.down=max(1,self.rows.value()) if hasattr(self,"rows") else j.down
        j.gap_x=self.gap_x.value() if hasattr(self,"gap_x") else j.gap_x
        j.gap_y=self.gap_y.value() if hasattr(self,"gap_y") else j.gap_y
        j.bleed=self.bleed.value() if hasattr(self,"bleed") else j.bleed
        j.margin=self.margin_left.value() if hasattr(self,"margin_left") else j.margin
        j.show_crop=self.cb_crop.isChecked() if hasattr(self,"cb_crop") else True
        j.show_registration=self.cb_reg.isChecked() if hasattr(self,"cb_reg") else True
        j.show_colorbar=self.cb_bar.isChecked() if hasattr(self,"cb_bar") else True
        j.show_info=self.cb_info.isChecked() if hasattr(self,"cb_info") else True
        if hasattr(self,"canvas"): self.canvas.update()
        if hasattr(self,"status_count"): self.status_count.setText(f"拼版：{j.across*j.down}")
        if hasattr(self,"status_sheet"): self.status_sheet.setText(f"纸张：{j.sheet_width:g} × {j.sheet_height:g} mm")

    def apply_profile(self,index):
        if index==1: self.job.sheet_width,self.job.sheet_height=210,297
        elif index==2: self.job.sheet_width,self.job.sheet_height=297,420
        elif index==3: self.job.sheet_width,self.job.sheet_height=889,1194
        else: self.job.sheet_width,self.job.sheet_height=890,630
        self.refresh_preview()

    def fit_to_sheet(self):
        self.job.margin=10
        self.margin_top.setValue(10); self.margin_bottom.setValue(10)
        self.margin_left.setValue(10); self.margin_right.setValue(10)
        self.refresh_preview()

    def preview_action(self,name):
        if name=="适合窗口": self.job.zoom=0.72
        elif name=="实际大小": self.job.zoom=1.0
        elif name=="+" : self.job.zoom=min(1.5,self.job.zoom+0.1)
        elif name=="−" : self.job.zoom=max(0.2,self.job.zoom-0.1)
        self.zoom_label.setText(f"{int(self.job.zoom*100)}%")
        self.status_zoom.setText(f"缩放：{int(self.job.zoom*100)}%")
        self.canvas.update()

    def save_job(self):
        path,_=QFileDialog.getSaveFileName(self,"保存拼版方案","","JSON 文件 (*.json)")
        if not path:return
        import json
        data={k:v for k,v in vars(self.job).items()}
        with open(path,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
        self.statusBar().showMessage("拼版参数方案已保存",3000)

    def not_implemented(self):
        QMessageBox.information(self,"功能接入","此操作将在现有 V2.4 拼版引擎接入阶段连接真实业务逻辑。")


def main():
    app=QApplication(sys.argv)
    app.setApplicationName("Desktop Imposer Pro V3.0")
    win=MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__=="__main__":
    main()
